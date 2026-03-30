# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.queue_job import exception as queue_job_exception

_logger = logging.getLogger(__name__)

RetryableJobError = getattr(queue_job_exception, "RetryableJobError", None)
if RetryableJobError is None:
    RetryableJobError = getattr(queue_job_exception, "JobError", Exception)


def _safe_value(record, name, default=False):
    try:
        value = getattr(record, name, default)
    except Exception:
        return default
    if callable(value):
        return default
    return value


def _normalize_payment_type(payment_type):
    if payment_type == "transfer":
        return "outbound"
    if payment_type in ("inbound", "outbound"):
        return payment_type
    return "inbound"


class AccountPaymentBatchImporter(Component):
    """Import the Odoo Account Payments.

    For every payment in the list, a delayed job is created.
    """

    _name = "odoo.account.payment.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.payment"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo account payments %s returned %s items",
            filters,
            len(updated_ids),
        )
        for external_id in updated_ids:
            job_options = {"priority": 17}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountPaymentImporter(Component):
    _name = "odoo.account.payment.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.payment"]

    def _resolve_payment_method_line(self, data, current_payment=None):
        method_line_id = data.get("payment_method_line_id")
        if method_line_id:
            return method_line_id

        journal_id = data.get("journal_id")
        if not journal_id and current_payment and current_payment.journal_id:
            journal_id = current_payment.journal_id.id
        if not journal_id:
            return False

        journal = self.env["account.journal"].browse(journal_id).exists()
        if not journal:
            return False

        payment_type = data.get("payment_type")
        if not payment_type and current_payment:
            payment_type = current_payment.payment_type
        if not payment_type:
            payment_type = _safe_value(self.odoo_record, "payment_type", "inbound")
        payment_type = _normalize_payment_type(payment_type)

        if payment_type == "inbound":
            method_lines = journal.inbound_payment_method_line_ids
        else:
            method_lines = journal.outbound_payment_method_line_ids
        if method_lines:
            return method_lines[0].id
        return False

    def _validate_data(self, data, current_payment=None):
        super()._validate_data(data)
        method_line_id = self._resolve_payment_method_line(
            data, current_payment=current_payment
        )
        if method_line_id:
            data["payment_method_line_id"] = method_line_id
            return

        journal_id = data.get("journal_id")
        if not journal_id and current_payment and current_payment.journal_id:
            journal_id = current_payment.journal_id.id
        if not journal_id:
            raise RetryableJobError(
                "Account payment %s is missing a mapped journal_id"
                % self.external_id,
                seconds=60,
                ignore_retry=False,
            )

        payment_type = data.get("payment_type")
        if not payment_type and current_payment:
            payment_type = current_payment.payment_type
        payment_type = _normalize_payment_type(
            payment_type or _safe_value(self.odoo_record, "payment_type", "inbound")
        )
        raise RetryableJobError(
            "Account payment %s has no %s payment method line on local journal %s"
            % (self.external_id, payment_type, journal_id),
            seconds=60,
            ignore_retry=False,
        )

    def _update(self, binding, data):
        self._validate_data(data, current_payment=binding.odoo_id)
        return super()._update(binding, data)

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        partner = _safe_value(self.odoo_record, "partner_id", False)
        if partner and getattr(partner, "id", False):
            self._import_dependency(partner.id, "odoo.res.partner", force=force)

        currency = _safe_value(self.odoo_record, "currency_id", False)
        if currency and getattr(currency, "id", False):
            self._import_dependency(currency.id, "odoo.res.currency", force=False)

        journal = _safe_value(self.odoo_record, "journal_id", False)
        if journal and getattr(journal, "id", False):
            self._import_dependency(journal.id, "odoo.account.journal", force=False)

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if binding.backend_state == "posted" and binding.odoo_id.state == "draft":
            binding.with_delay()._confirm_if_needed()
        return res


class AccountPaymentImportMapper(Component):
    _name = "odoo.account.payment.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.payment"

    direct = [
        ("ref", "memo"),
        ("state", "backend_state"),
    ]

    @only_create
    @mapping
    def payment_type(self, record):
        backend_payment_type = _safe_value(record, "payment_type", "inbound")
        payment_type = _normalize_payment_type(backend_payment_type)
        if backend_payment_type != payment_type:
            _logger.info(
                "Normalized backend account.payment payment_type %r to %r",
                backend_payment_type,
                payment_type,
            )
        return {"payment_type": payment_type}

    @only_create
    @mapping
    def partner_type(self, record):
        partner_type = _safe_value(record, "partner_type", "customer")
        if not partner_type:
            partner_type = "customer"
        return {"partner_type": partner_type}

    @mapping
    def date(self, record):
        date = _safe_value(record, "date", False)
        if date:
            return {"date": date}
        return {}

    @mapping
    def amount(self, record):
        amount = _safe_value(record, "amount", 0.0)
        return {"amount": amount}

    @mapping
    def backend_amount(self, record):
        amount = _safe_value(record, "amount", 0.0)
        return {"backend_amount": amount}

    @mapping
    def partner_id(self, record):
        partner = _safe_value(record, "partner_id", False)
        if not partner or not getattr(partner, "id", False):
            return {}
        binder = self.binder_for("odoo.res.partner")
        local_partner = binder.to_internal(partner.id, unwrap=True)
        if local_partner:
            return {"partner_id": local_partner.id}
        return {}

    @mapping
    def currency_id(self, record):
        currency = _safe_value(record, "currency_id", False)
        if not currency or not getattr(currency, "id", False):
            return {"currency_id": self.env.user.company_id.currency_id.id}
        binder = self.binder_for("odoo.res.currency")
        local_currency = binder.to_internal(currency.id, unwrap=True)
        if local_currency:
            return {"currency_id": local_currency.id}
        return {"currency_id": self.env.user.company_id.currency_id.id}

    @mapping
    def journal_id(self, record):
        journal = _safe_value(record, "journal_id", False)
        if not journal or not getattr(journal, "id", False):
            return {}
        binder = self.binder_for("odoo.account.journal")
        local_journal = binder.to_internal(journal.id, unwrap=True)
        if local_journal:
            return {"journal_id": local_journal.id}
        return {}

    @mapping
    def payment_method_line_id(self, record):
        """Set default payment method line for the journal."""
        journal = _safe_value(record, "journal_id", False)
        if not journal or not getattr(journal, "id", False):
            return {}
        binder = self.binder_for("odoo.account.journal")
        local_journal = binder.to_internal(journal.id, unwrap=True)
        if not local_journal:
            return {}
        payment_type = _normalize_payment_type(
            _safe_value(record, "payment_type", "inbound")
        )
        if payment_type == "inbound":
            method_lines = local_journal.inbound_payment_method_line_ids
        else:
            method_lines = local_journal.outbound_payment_method_line_ids
        if method_lines:
            return {"payment_method_line_id": method_lines[0].id}
        return {}

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}
