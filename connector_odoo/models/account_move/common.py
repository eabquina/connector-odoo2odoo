# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component
from odoo.addons.queue_job import exception as queue_job_exception

RetryableJobError = getattr(queue_job_exception, "RetryableJobError", None)
if RetryableJobError is None:
    RetryableJobError = getattr(queue_job_exception, "JobError", Exception)

_logger = logging.getLogger(__name__)


class OdooAccountMove(models.Model):
    _name = "odoo.account.move"
    _inherit = "odoo.binding"
    _inherits = {"account.move": "odoo_id"}
    _description = "External Odoo Account Move"

    odoo_id = fields.Many2one(
        comodel_name="account.move",
        string="Account Move",
        required=True,
        ondelete="cascade",
    )

    backend_amount_total = fields.Float()
    backend_amount_residual = fields.Float()
    backend_state = fields.Char()
    backend_move_line_count = fields.Integer(string="Backend Move Line Count")
    synced_move_line_count = fields.Integer(
        string="Synced Move Line Count",
        compute="_compute_synced_move_line_count",
    )
    _MAX_POST_RETRIES_WITHOUT_PROGRESS = 8

    def _compute_synced_move_line_count(self):
        line_model = self.env["odoo.account.move.line"]
        for move in self:
            move.synced_move_line_count = line_model.search_count(
                [
                    ("backend_id", "=", move.backend_id.id),
                    ("move_id", "=", move.odoo_id.id),
                ]
            )

    def _compute_import_state(self):
        for move in self:
            if move.backend_move_line_count != move.synced_move_line_count:
                move.import_state = "error_sync"
            elif (
                move.backend_amount_total
                and round(move.backend_amount_total, 2)
                != round(move.amount_total, 2)
            ):
                move.import_state = "error_amount"
            else:
                move.import_state = "done"

    import_state = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("error_sync", "Sync Error"),
            ("error_amount", "Amounts Error"),
            ("done", "Done"),
        ],
        default="waiting",
        compute=_compute_import_state,
    )

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )

    def _get_remote_move_line_ids(self):
        self.ensure_one()
        if self.external_id <= 0:
            return []
        with self.backend_id.work_on("odoo.account.move.line") as work:
            adapter = work.component(usage="backend.adapter")
            return adapter.search(
                [("move_id", "=", self.external_id)],
                order="id",
            )

    def sync_move_lines(self):
        for binding in self:
            remote_line_ids = binding._get_remote_move_line_ids()
            binding.backend_move_line_count = len(remote_line_ids)
            for remote_line_id in remote_line_ids:
                self.env["odoo.account.move.line"].with_delay().import_record(
                    binding.backend_id, remote_line_id, force=True
                )
        return True

    def _raise_retryable(self, message, seconds=300):
        err = RetryableJobError(message)
        try:
            setattr(err, "seconds", seconds)
        except Exception:
            pass
        raise err

    def _current_job_retry(self):
        job_uuid = self.env.context.get("job_uuid")
        if not job_uuid:
            return 0
        job = self.env["queue.job"].sudo().search([("uuid", "=", job_uuid)], limit=1)
        return job.retry if job and "retry" in job._fields else 0

    def _enqueue_missing_move_lines(self, binding, remote_line_ids):
        line_model = self.env["odoo.account.move.line"]
        existing_external_ids = set(
            line_model.search(
                [
                    ("backend_id", "=", binding.backend_id.id),
                    ("move_id", "=", binding.odoo_id.id),
                ]
            ).mapped("external_id")
        )
        missing_remote_ids = [
            line_id for line_id in remote_line_ids if line_id not in existing_external_ids
        ]
        for line_id in missing_remote_ids:
            line_model.with_delay(priority=12).import_record(
                binding.backend_id,
                line_id,
                force=True,
            )
        return len(missing_remote_ids)

    def _post_if_needed(self):
        for binding in self:
            if binding.backend_state == "posted" and binding.odoo_id.state == "draft":
                # Avoid remote RPC calls here: this method can run in high-volume
                # queue retries and should not be blocked by backend auth/network errors.
                expected = binding.backend_move_line_count or 0
                synced_actual = binding.synced_move_line_count
                local_line_count = len(binding.odoo_id.line_ids)
                effective_actual = max(synced_actual, local_line_count)
                if expected <= 0 and local_line_count:
                    expected = local_line_count
                if expected and effective_actual < expected:
                    binding.with_delay(priority=12).sync_move_lines()
                    retry = binding._current_job_retry()
                    message = (
                        "Retry post account.move %s (%d/%d lines)"
                        % (binding.odoo_id.id, effective_actual, expected)
                    )
                    _logger.info(
                        "%s. Triggered line sync job.",
                        message,
                    )
                    if retry >= self._MAX_POST_RETRIES_WITHOUT_PROGRESS:
                        raise Exception(
                            "Post aborted for account.move %s after %d retries without line progress (%d/%d)."
                            % (binding.odoo_id.id, retry, effective_actual, expected)
                        )
                    binding._raise_retryable(message, seconds=300)
                if expected and not binding.odoo_id.line_ids:
                    message = (
                        "Retry post account.move %s: no local lines present yet"
                        % binding.odoo_id.id
                    )
                    _logger.warning(
                        "%s (binding %s)",
                        message,
                        binding.id,
                    )
                    binding._raise_retryable(message, seconds=300)
                if not expected and not binding.odoo_id.line_ids:
                    binding.with_delay(priority=12).sync_move_lines()
                    binding._raise_retryable(
                        "Retry post account.move %s: waiting for line metadata"
                        % binding.odoo_id.id,
                        seconds=300,
                    )
                try:
                    binding.odoo_id.action_post()
                except Exception as err:
                    _logger.warning(
                        "Could not post account.move %s (binding %s)",
                        binding.odoo_id.id,
                        binding.id,
                        exc_info=True,
                    )
                    binding._raise_retryable(
                        "Retry post account.move %s after post error: %s"
                        % (binding.odoo_id.id, str(err)),
                        seconds=120,
                    )


class AccountMove(models.Model):
    _inherit = "account.move"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.move",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountMoveAdapter(Component):
    _name = "odoo.account.move.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.move"
    _odoo_model = "account.move"


class OdooAccountMoveLine(models.Model):
    _name = "odoo.account.move.line"
    _inherit = "odoo.binding"
    _inherits = {"account.move.line": "odoo_id"}
    _description = "External Odoo Account Move Line"

    odoo_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Account Move Line",
        required=True,
        ondelete="cascade",
    )

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.move.line",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountMoveLineAdapter(Component):
    _name = "odoo.account.move.line.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.move.line"
    _odoo_model = "account.move.line"
