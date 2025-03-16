import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooHrOvertime(models.Model):
    _name = "odoo.hr.overtime"
    _inherit = "odoo.binding"
    _inherits = {"hr.overtime": "odoo_id"}
    _description = "External Odoo Hr Overtime"

    odoo_id = fields.Many2one(
        comodel_name="hr.overtime", string="Hr Overtime", required=True, ondelete="cascade"
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


class HrOvertime(models.Model):
    _inherit = "hr.overtime"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.overtime",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class OdooHrOvertimeAdapter(Component):
    _name = "odoo.hr.overtime.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.overtime"

    _odoo_model = "hr.overtime"


class HrOvertimeListener(Component):
    _name = "hr.overtime.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["hr.overtime"]
    _usage = "event.listener"
