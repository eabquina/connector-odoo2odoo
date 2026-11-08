# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooHrAttendance(models.Model):
    _name = "odoo.hr.attendance"
    _inherit = "odoo.binding"
    _inherits = {"hr.attendance": "odoo_id"}
    _description = "External Odoo HrAttendance"

    odoo_id = fields.Many2one(
        comodel_name="hr.attendance", string="HrAttendance", required=True, ondelete="cascade"
    )

    _external_id = models.Constraint('UNIQUE(external_id)', 'External ID (external_id) must be unique!')

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.attendance",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HrAttendanceAdapter(Component):
    _name = "odoo.hr.attendance.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.attendance"

    _odoo_model = "hr.attendance"


class HrAttendanceListener(Component):
    _name = "hr.attendance.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["hr.attendance"]
    _usage = "event.listener"
