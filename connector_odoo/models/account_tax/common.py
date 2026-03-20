# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooAccountTax(models.Model):
    _name = "odoo.account.tax"
    _inherit = "odoo.binding"
    _inherits = {"account.tax": "odoo_id"}
    _description = "External Odoo Account Tax"

    odoo_id = fields.Many2one(
        comodel_name="account.tax",
        string="Tax",
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


class AccountTax(models.Model):
    _inherit = "account.tax"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.tax",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountTaxAdapter(Component):
    _name = "odoo.account.tax.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.tax"
    _odoo_model = "account.tax"
