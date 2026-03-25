# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooHelpdeskTicketChannel(models.Model):
    _name = "odoo.helpdesk.ticket.channel"
    _inherit = "odoo.binding"
    _inherits = {"helpdesk.ticket.channel": "odoo_id"}
    _description = "External Odoo Helpdesk Ticket Channel"

    odoo_id = fields.Many2one(
        comodel_name="helpdesk.ticket.channel",
        string="Channel",
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


class HelpdeskTicketChannel(models.Model):
    _inherit = "helpdesk.ticket.channel"

    bind_ids = fields.One2many(
        comodel_name="odoo.helpdesk.ticket.channel",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HelpdeskTicketChannelAdapter(Component):
    _name = "odoo.helpdesk.ticket.channel.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.helpdesk.ticket.channel"

    _odoo_model = "helpdesk.ticket.channel"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_helpdesk_channel_domain_filter)
        )
        filters += ext_filter or []
        return super().search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class HelpdeskTicketChannelListener(Component):
    _name = "helpdesk.ticket.channel.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["helpdesk.ticket.channel"]
    _usage = "event.listener"
