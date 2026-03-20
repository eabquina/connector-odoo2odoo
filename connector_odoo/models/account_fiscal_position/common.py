# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooAccountFiscalPosition(models.Model):
    _name = "odoo.account.fiscal.position"
    _inherit = "odoo.binding"
    _inherits = {"account.fiscal.position": "odoo_id"}
    _description = "External Odoo Fiscal Position"

    odoo_id = fields.Many2one(
        comodel_name="account.fiscal.position",
        string="Fiscal Position",
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
        return self.with_delay().import_record(
            self.backend_id, self.external_id, force=True
        )


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.fiscal.position",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountFiscalPositionAdapter(Component):
    _name = "odoo.account.fiscal.position.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.fiscal.position"
    _odoo_model = "account.fiscal.position"
