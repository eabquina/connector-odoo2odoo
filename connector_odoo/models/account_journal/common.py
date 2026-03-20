# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooAccountJournal(models.Model):
    _name = "odoo.account.journal"
    _inherit = "odoo.binding"
    _inherits = {"account.journal": "odoo_id"}
    _description = "External Odoo Account Journal"

    odoo_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
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

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class AccountJournal(models.Model):
    _inherit = "account.journal"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.journal",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountJournalAdapter(Component):
    _name = "odoo.account.journal.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.journal"
    _odoo_model = "account.journal"
