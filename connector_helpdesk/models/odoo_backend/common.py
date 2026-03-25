# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class OdooBackend(models.Model):
    _inherit = "odoo.backend"

    # HELPDESK STAGE SYNC
    default_import_helpdesk_stage = fields.Boolean("Import Stages")
    import_helpdesk_stage_from_date = fields.Datetime("Import Stages From Date")
    external_helpdesk_stage_domain_filter = fields.Char(
        string="Stage Domain Filter", default="[]",
    )

    # HELPDESK TAG SYNC
    default_import_helpdesk_tag = fields.Boolean("Import Tags")
    import_helpdesk_tag_from_date = fields.Datetime("Import Tags From Date")
    external_helpdesk_tag_domain_filter = fields.Char(
        string="Tag Domain Filter", default="[]",
    )

    # HELPDESK CATEGORY SYNC
    default_import_helpdesk_category = fields.Boolean("Import Categories")
    import_helpdesk_category_from_date = fields.Datetime("Import Categories From Date")
    external_helpdesk_category_domain_filter = fields.Char(
        string="Category Domain Filter", default="[]",
    )

    # HELPDESK CHANNEL SYNC
    default_import_helpdesk_channel = fields.Boolean("Import Channels")
    import_helpdesk_channel_from_date = fields.Datetime("Import Channels From Date")
    external_helpdesk_channel_domain_filter = fields.Char(
        string="Channel Domain Filter", default="[]",
    )

    # HELPDESK TEAM SYNC
    default_import_helpdesk_team = fields.Boolean("Import Teams")
    import_helpdesk_team_from_date = fields.Datetime("Import Teams From Date")
    external_helpdesk_team_domain_filter = fields.Char(
        string="Team Domain Filter", default="[]",
    )

    # HELPDESK TICKET SYNC
    default_import_helpdesk_ticket = fields.Boolean("Import Tickets")
    import_helpdesk_ticket_from_date = fields.Datetime("Import Tickets From Date")
    external_helpdesk_ticket_domain_filter = fields.Char(
        string="Ticket Domain Filter", default="[]",
    )

    # IMPORT ACTIONS
    def import_helpdesk_stage(self):
        if not self.default_import_helpdesk_stage:
            return False
        self._import_from_date(
            "odoo.helpdesk.ticket.stage", "import_helpdesk_stage_from_date"
        )
        return True

    def import_helpdesk_tag(self):
        if not self.default_import_helpdesk_tag:
            return False
        self._import_from_date(
            "odoo.helpdesk.ticket.tag", "import_helpdesk_tag_from_date"
        )
        return True

    def import_helpdesk_category(self):
        if not self.default_import_helpdesk_category:
            return False
        self._import_from_date(
            "odoo.helpdesk.ticket.category", "import_helpdesk_category_from_date"
        )
        return True

    def import_helpdesk_channel(self):
        if not self.default_import_helpdesk_channel:
            return False
        self._import_from_date(
            "odoo.helpdesk.ticket.channel", "import_helpdesk_channel_from_date"
        )
        return True

    def import_helpdesk_team(self):
        if not self.default_import_helpdesk_team:
            return False
        self._import_from_date(
            "odoo.helpdesk.ticket.team", "import_helpdesk_team_from_date"
        )
        return True

    def import_helpdesk_ticket(self):
        if not self.default_import_helpdesk_ticket:
            return False
        self._import_from_date(
            "odoo.helpdesk.ticket", "import_helpdesk_ticket_from_date"
        )
        return True

    def import_helpdesk_all(self):
        """Import all helpdesk data in dependency order."""
        _logger.info("Starting full helpdesk import for backend %s", self.name)
        self.import_helpdesk_stage()
        self.import_helpdesk_tag()
        self.import_helpdesk_category()
        self.import_helpdesk_channel()
        self.import_helpdesk_team()
        self.import_helpdesk_ticket()
        _logger.info("Completed full helpdesk import for backend %s", self.name)
        return True
