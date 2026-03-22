# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

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

    def _post_if_needed(self):
        for binding in self:
            if binding.backend_state == "posted" and binding.odoo_id.state == "draft":
                # Check that all move lines have been synced before posting
                expected = binding.backend_move_line_count
                actual = binding.synced_move_line_count
                if expected and actual < expected:
                    _logger.info(
                        "Deferring post for account.move %s (binding %s): "
                        "%d/%d lines synced",
                        binding.odoo_id.id,
                        binding.id,
                        actual,
                        expected,
                    )
                    binding.with_delay(
                        priority=20,
                        eta=300,
                        description="Retry post account.move %s (%d/%d lines)"
                        % (binding.odoo_id.id, actual, expected),
                    )._post_if_needed()
                    continue
                if not binding.odoo_id.line_ids:
                    _logger.warning(
                        "Skipping post for account.move %s (binding %s): "
                        "no lines present",
                        binding.odoo_id.id,
                        binding.id,
                    )
                    continue
                try:
                    binding.odoo_id.action_post()
                except Exception:
                    _logger.warning(
                        "Could not post account.move %s (binding %s)",
                        binding.odoo_id.id,
                        binding.id,
                        exc_info=True,
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
