# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooAttendance(models.Model):
    _name = "odoo.hr.attendance.late"
    _inherit = "odoo.binding"
    _inherits = {"hr.attendance.late": "odoo_id"}
    _description = "External Odoo Attendance"

    odoo_id = fields.Many2one(
        comodel_name="hr.attendance.late", string="Attendance", required=True, ondelete="cascade"
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


class Attendance(models.Model):
    _inherit = "hr.attendance.late"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.attendance.late",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AttendanceAdapter(Component):
    _name = "odoo.hr.attendance.late.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.attendance.late"

    _odoo_model = "hr.attendance.late"


class JobPositionListener(Component):
    _name = "hr.attendance.late.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["hr.attendance.late"]
    _usage = "event.listener"
