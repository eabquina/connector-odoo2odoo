# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooHrOvertimeType(models.Model):
    _name = "odoo.overtime.type"
    _inherit = "odoo.binding"
    _inherits = {"overtime.type": "odoo_id"}
    _description = "External Odoo HR Leave Type"

    odoo_id = fields.Many2one(
        comodel_name="overtime.type", string="HR Overtime Type", required=True, ondelete="cascade"
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


class HrOvertimeType(models.Model):
    _inherit = "overtime.type"

    bind_ids = fields.One2many(
        comodel_name="odoo.overtime.type",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HrOvertimeTypeAdapter(Component):
    _name = "odoo.overtime.type.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.overtime.type"

    _odoo_model = "overtime.type"


class HrOvertimeTypeListener(Component):
    _name = "overtime.type.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["overtime.type"]
    _usage = "event.listener"
