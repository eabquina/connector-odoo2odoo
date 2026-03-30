# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from psycopg2 import IntegrityError

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.queue_job import exception as queue_job_exception

_logger = logging.getLogger(__name__)

RetryableJobError = getattr(queue_job_exception, "RetryableJobError", None)
if RetryableJobError is None:
    RetryableJobError = getattr(queue_job_exception, "JobError", Exception)


class OdooStockPicking(models.Model):
    _name = "odoo.stock.picking"
    _inherit = [
        "odoo.binding",
    ]
    _inherits = {"stock.picking": "odoo_id"}
    _description = "Odoo Picking"

    odoo_id = fields.Many2one(
        comodel_name="stock.picking", string="Transfer", required=True, ondelete="cascade"
    )

    backend_state = fields.Char()

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        recordset = self.browse()
        regular_vals = []

        for vals in vals_list:
            backend_id = vals.get("backend_id")
            odoo_id = vals.get("odoo_id")

            # Existing stock.picking must not be updated through _inherits on create.
            if backend_id and odoo_id:
                existing = self.search(
                    [("backend_id", "=", backend_id), ("odoo_id", "=", odoo_id)],
                    limit=1,
                )
                if existing:
                    recordset |= existing
                    continue

                external_id = vals.get("external_id", -1)
                backend_state = vals.get("backend_state")
                uid = self.env.uid
                try:
                    with self.env.cr.savepoint():
                        self.env.cr.execute(
                            f"""
                            INSERT INTO {self._table}
                                (backend_id, external_id, odoo_id, backend_state, create_uid, create_date, write_uid, write_date)
                            VALUES
                                (%s, %s, %s, %s, %s, NOW() AT TIME ZONE 'UTC', %s, NOW() AT TIME ZONE 'UTC')
                            RETURNING id
                            """,
                            (backend_id, external_id, odoo_id, backend_state, uid, uid),
                        )
                        new_id = self.env.cr.fetchone()[0]
                except IntegrityError:
                    existing = self.search(
                        [("backend_id", "=", backend_id), ("odoo_id", "=", odoo_id)],
                        limit=1,
                    )
                    if existing:
                        recordset |= existing
                        continue
                    raise

                recordset |= self.browse(new_id)
            else:
                regular_vals.append(vals)

        if regular_vals:
            recordset |= super().create(regular_vals)
        return recordset

    def _compute_import_state(self):
        for picking_id in self:
            waiting = len(
                picking_id.queue_job_ids.filtered(
                    lambda j: j.state in ("pending", "enqueued", "started")
                )
            )
            error = len(
                picking_id.queue_job_ids.filtered(lambda j: j.state == "failed")
            )
            if waiting:
                picking_id.import_state = "waiting"
            elif error:
                picking_id.import_state = "error_sync"
            else:
                picking_id.import_state = "done"

    import_state = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("error_sync", "Sync Error"),
            ("done", "Done"),
        ],
        default="waiting",
        compute=_compute_import_state,
    )

    def resync(self):
        if self.backend_id.read_operation_from == "odoo":
            raise NotImplementedError
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )

    def _set_state(self):
        for picking in self:
            state_error = ValidationError(
                _('Can not set state to "{}" for picking "{}"').format(
                    picking.backend_state, picking.name
                )
            )
            if picking.backend_state == picking.odoo_id.state:
                continue

            if picking.backend_state == "done":
                if picking.state != "assigned":
                    picking.odoo_id.action_confirm()
                if picking.state != "assigned":
                    raise RetryableJobError(
                        _(
                            'Picking "%s" is not ready to validate yet; waiting for moves to finish syncing.'
                        )
                        % picking.name,
                        seconds=120,
                        ignore_retry=False,
                    )
                for move_id in picking.move_lines:
                    move_id.quantity_done = move_id.product_uom_qty
                picking.odoo_id.button_validate()
                if picking.state != "done":
                    raise RetryableJobError(
                        _(
                            'Picking "%s" could not reach done state yet; retrying later.'
                        )
                        % picking.name,
                        seconds=120,
                        ignore_retry=False,
                    )
            elif picking.backend_state == "auto":
                picking.odoo_id.action_confirm()
            elif picking.backend_state == "cancel":
                picking.odoo_id.action_cancel()
            elif picking.backend_state == "confirmed":
                picking.odoo_id.action_confirm()
            elif picking.backend_state == "approved":
                picking.odoo_id.action_approve()
            elif picking.backend_state != picking.odoo_id.state:
                raise state_error


class StockPicking(models.Model):
    _inherit = "stock.picking"

    bind_ids = fields.One2many(
        comodel_name="odoo.stock.picking",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )

    queue_job_ids = fields.Many2many(
        comodel_name="queue.job",
    )


class StockPickingAdapter(Component):
    _name = "odoo.stock.picking.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.stock.picking"
    _odoo_model = "stock.picking"
