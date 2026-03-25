# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import odoo_backend

# Level 0: No helpdesk dependencies
from . import helpdesk_ticket_stage
from . import helpdesk_ticket_tag
from . import helpdesk_ticket_category
from . import helpdesk_ticket_channel

# Level 1: Depends on category
from . import helpdesk_ticket_team

# Level 2: Depends on stage, tag, category, channel, team, partner
from . import helpdesk_ticket
