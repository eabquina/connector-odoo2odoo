# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooHrEmployee(models.Model):
    _name = "odoo.hr.employee"
    _inherit = "odoo.binding"
    _inherits = {"hr.employee": "odoo_id"}
    _description = "External Odoo Employee"

    odoo_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        return self.with_delay().import_record(
            self.backend_id, self.external_id, force=True
        )


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.employee",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HrEmployeeAdapter(Component):
    _name = "odoo.hr.employee.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.employee"
    _odoo_model = "hr.employee"
