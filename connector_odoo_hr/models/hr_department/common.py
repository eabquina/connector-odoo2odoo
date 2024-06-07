# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooJobPosition(models.Model):
    _name = "odoo.hr.department"
    _inherit = "odoo.binding"
    _inherits = {"hr.department": "odoo_id"}
    _description = "External Odoo Department"

    odoo_id = fields.Many2one(
        comodel_name="hr.department", string="Department", required=True, ondelete="cascade"
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


class JobPosition(models.Model):
    _inherit = "hr.department"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.department",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class JobPositionAdapter(Component):
    _name = "odoo.hr.department.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.department"

    _odoo_model = "hr.department"


class JobPositionListener(Component):
    _name = "hr.department.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["hr.department"]
    _usage = "event.listener"
