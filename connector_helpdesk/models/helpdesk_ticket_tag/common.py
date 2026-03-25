# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooHelpdeskTicketTag(models.Model):
    _name = "odoo.helpdesk.ticket.tag"
    _inherit = "odoo.binding"
    _inherits = {"helpdesk.ticket.tag": "odoo_id"}
    _description = "External Odoo Helpdesk Ticket Tag"

    odoo_id = fields.Many2one(
        comodel_name="helpdesk.ticket.tag",
        string="Tag",
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


class HelpdeskTicketTag(models.Model):
    _inherit = "helpdesk.ticket.tag"

    bind_ids = fields.One2many(
        comodel_name="odoo.helpdesk.ticket.tag",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HelpdeskTicketTagAdapter(Component):
    _name = "odoo.helpdesk.ticket.tag.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.helpdesk.ticket.tag"

    _odoo_model = "helpdesk.ticket.tag"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_helpdesk_tag_domain_filter)
        )
        filters += ext_filter or []
        return super().search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class HelpdeskTicketTagListener(Component):
    _name = "helpdesk.ticket.tag.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["helpdesk.ticket.tag"]
    _usage = "event.listener"
