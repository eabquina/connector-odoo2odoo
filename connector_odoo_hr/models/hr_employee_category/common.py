# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooEmployeeCategory(models.Model):
    _name = "odoo.hr.employee.category"
    _inherit = "odoo.binding"
    _inherits = {"hr.employee.category": "odoo_id"}
    _description = "External Odoo Employee Tags"

    odoo_id = fields.Many2one(
        comodel_name="hr.employee.category", string="Employee Tags", required=True, ondelete="cascade"
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


class EmployeeCategory(models.Model):
    _inherit = "hr.employee.category"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.employee.category",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class EmployeeCategoryAdapter(Component):
    _name = "odoo.hr.employee.category.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.employee.category"

    _odoo_model = "hr.employee.category"


class EmployeeCategoryListener(Component):
    _name = "hr.employee.category.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["hr.employee.category"]
    _usage = "event.listener"
