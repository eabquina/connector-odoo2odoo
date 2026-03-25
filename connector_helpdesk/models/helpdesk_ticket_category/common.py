# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooHelpdeskTicketCategory(models.Model):
    _name = "odoo.helpdesk.ticket.category"
    _inherit = "odoo.binding"
    _inherits = {"helpdesk.ticket.category": "odoo_id"}
    _description = "External Odoo Helpdesk Ticket Category"

    odoo_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Category",
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

    def name_get(self):
        result = []
        for record in self:
            name = "{} (Backend: {})".format(
                record.odoo_id.display_name, record.backend_id.display_name
            )
            result.append((record.id, name))
        return result

    def resync(self):
        return self.with_delay().import_record(
            self.backend_id, self.external_id, force=True
        )


class HelpdeskTicketCategory(models.Model):
    _inherit = "helpdesk.ticket.category"

    bind_ids = fields.One2many(
        comodel_name="odoo.helpdesk.ticket.category",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HelpdeskTicketCategoryAdapter(Component):
    _name = "odoo.helpdesk.ticket.category.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.helpdesk.ticket.category"

    _odoo_model = "helpdesk.ticket.category"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_helpdesk_category_domain_filter)
        )
        filters += ext_filter or []
        return super().search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class HelpdeskTicketCategoryListener(Component):
    _name = "helpdesk.ticket.category.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["helpdesk.ticket.category"]
    _usage = "event.listener"
