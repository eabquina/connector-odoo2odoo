# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooAccountPayment(models.Model):
    _name = "odoo.account.payment"
    _inherit = "odoo.binding"
    _inherits = {"account.payment": "odoo_id"}
    _description = "External Odoo Account Payment"

    odoo_id = fields.Many2one(
        comodel_name="account.payment",
        string="Payment",
        required=True,
        ondelete="cascade",
    )

    backend_amount = fields.Float()
    backend_state = fields.Char()

    def _compute_import_state(self):
        for payment in self:
            if (
                payment.backend_amount
                and round(payment.backend_amount, 2) != round(payment.amount, 2)
            ):
                payment.import_state = "error_amount"
            else:
                payment.import_state = "done"

    import_state = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("error_amount", "Amounts Error"),
            ("done", "Done"),
        ],
        default="waiting",
        compute=_compute_import_state,
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

    def _confirm_if_needed(self):
        for binding in self:
            if binding.backend_state == "posted" and binding.odoo_id.state == "draft":
                try:
                    binding.odoo_id.action_post()
                except Exception:
                    _logger.warning(
                        "Could not post account.payment %s (binding %s)",
                        binding.odoo_id.id,
                        binding.id,
                        exc_info=True,
                    )


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.payment",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountPaymentAdapter(Component):
    _name = "odoo.account.payment.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.payment"
    _odoo_model = "account.payment"
