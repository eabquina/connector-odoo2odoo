# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooHelpdeskTicketTeam(models.Model):
    _name = "odoo.helpdesk.ticket.team"
    _inherit = "odoo.binding"
    _inherits = {"helpdesk.ticket.team": "odoo_id"}
    _description = "External Odoo Helpdesk Ticket Team"

    odoo_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Team",
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


class HelpdeskTicketTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    bind_ids = fields.One2many(
        comodel_name="odoo.helpdesk.ticket.team",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HelpdeskTicketTeamAdapter(Component):
    _name = "odoo.helpdesk.ticket.team.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.helpdesk.ticket.team"

    _odoo_model = "helpdesk.ticket.team"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_helpdesk_team_domain_filter)
        )
        filters += ext_filter or []
        return super().search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class HelpdeskTicketTeamListener(Component):
    _name = "helpdesk.ticket.team.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["helpdesk.ticket.team"]
    _usage = "event.listener"
