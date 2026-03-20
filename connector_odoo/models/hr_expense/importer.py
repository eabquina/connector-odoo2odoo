# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


def _safe_value(record, name, default=False):
    try:
        value = getattr(record, name, default)
    except Exception:
        return default
    if callable(value):
        return default
    return value


# -- hr.expense.sheet --


class HrExpenseSheetBatchImporter(Component):
    _name = "odoo.hr.expense.sheet.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.expense.sheet"]

    def run(self, filters=None, force=False):
        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo expense sheets %s returned %s items",
            filters,
            len(updated_ids),
        )
        for external_id in updated_ids:
            job_options = {"priority": 18}
            self._import_record(external_id, job_options=job_options, force=force)


class HrExpenseSheetImporter(Component):
    _name = "odoo.hr.expense.sheet.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.expense.sheet"]

    def _import_dependencies(self, force=False):
        employee = _safe_value(self.odoo_record, "employee_id", False)
        if employee and getattr(employee, "id", False):
            self._import_dependency(employee.id, "odoo.hr.employee", force=force)

        currency = _safe_value(self.odoo_record, "currency_id", False)
        if currency and getattr(currency, "id", False):
            self._import_dependency(currency.id, "odoo.res.currency", force=False)

        journal = _safe_value(self.odoo_record, "journal_id", False)
        if journal and getattr(journal, "id", False):
            self._import_dependency(journal.id, "odoo.account.journal", force=False)

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        remote_expense_ids = binding._get_remote_expense_ids()
        binding.backend_expense_count = len(remote_expense_ids)
        for expense_id in remote_expense_ids:
            self.env["odoo.hr.expense"].with_delay().import_record(
                self.backend_record, expense_id, force
            )
        if binding.backend_state in ("approve", "post", "done"):
            binding.with_delay()._approve_if_needed()
        return res


class HrExpenseSheetImportMapper(Component):
    _name = "odoo.hr.expense.sheet.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.hr.expense.sheet"

    direct = [
        ("name", "name"),
        ("state", "backend_state"),
    ]

    @mapping
    def backend_total_amount(self, record):
        total_amount = _safe_value(record, "total_amount", 0.0)
        return {"backend_total_amount": total_amount}

    @mapping
    def accounting_date(self, record):
        accounting_date = _safe_value(record, "accounting_date", False)
        if accounting_date:
            return {"accounting_date": accounting_date}
        return {}

    @mapping
    def employee_id(self, record):
        employee = _safe_value(record, "employee_id", False)
        if not employee or not getattr(employee, "id", False):
            return {}
        binder = self.binder_for("odoo.hr.employee")
        local_employee = binder.to_internal(employee.id, unwrap=True)
        if local_employee:
            return {"employee_id": local_employee.id}
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

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}


# -- hr.expense --


class HrExpenseBatchImporter(Component):
    _name = "odoo.hr.expense.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.expense"]

    def run(self, filters=None, force=False):
        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo expenses %s returned %s items",
            filters,
            len(updated_ids),
        )
        for external_id in updated_ids:
            job_options = {"priority": 19}
            self._import_record(external_id, job_options=job_options, force=force)


class HrExpenseImporter(Component):
    _name = "odoo.hr.expense.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.expense"]

    def _import_dependencies(self, force=False):
        employee = _safe_value(self.odoo_record, "employee_id", False)
        if employee and getattr(employee, "id", False):
            self._import_dependency(employee.id, "odoo.hr.employee", force=force)

        product = _safe_value(self.odoo_record, "product_id", False)
        if product and getattr(product, "id", False):
            self._import_dependency(product.id, "odoo.product.product", force=force)

        currency = _safe_value(self.odoo_record, "currency_id", False)
        if currency and getattr(currency, "id", False):
            self._import_dependency(currency.id, "odoo.res.currency", force=False)

        account = _safe_value(self.odoo_record, "account_id", False)
        if account and getattr(account, "id", False):
            self._import_dependency(account.id, "odoo.account.account", force=False)


class HrExpenseImportMapper(Component):
    _name = "odoo.hr.expense.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.hr.expense"

    direct = [
        ("name", "name"),
        ("date", "date"),
        ("quantity", "quantity"),
        ("reference", "reference"),
        ("description", "description"),
        ("payment_mode", "payment_mode"),
    ]

    def _lookup_odoo_id(self, table, external_id):
        self.env.cr.execute(
            f"""
            SELECT odoo_id
              FROM {table}
             WHERE backend_id = %s
               AND external_id = %s
             ORDER BY id DESC
             LIMIT 1
            """,
            (self.backend_record.id, external_id),
        )
        row = self.env.cr.fetchone()
        return row[0] if row else False

    def _extract_external_id(self, record, field_name):
        value = _safe_value(record, field_name, False)
        if not value:
            return False
        value_id = getattr(value, "id", False)
        if callable(value_id):
            return False
        return value_id or False

    @mapping
    def unit_amount(self, record):
        # Handle both unit_amount and price_unit field names
        unit_amount = _safe_value(record, "unit_amount", False)
        if unit_amount is False:
            unit_amount = _safe_value(record, "price_unit", 0.0)
        return {"unit_amount": unit_amount or 0.0}

    @mapping
    def total_amount(self, record):
        total_amount = _safe_value(record, "total_amount", False)
        if total_amount is not False:
            return {"total_amount": total_amount}
        return {}

    @mapping
    def employee_id(self, record):
        external_id = self._extract_external_id(record, "employee_id")
        if not external_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_hr_employee", external_id)
        if odoo_id:
            return {"employee_id": odoo_id}
        return {}

    @mapping
    def product_id(self, record):
        external_id = self._extract_external_id(record, "product_id")
        if not external_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_product_product", external_id)
        if odoo_id:
            return {"product_id": odoo_id}
        return {}

    @mapping
    def account_id(self, record):
        external_id = self._extract_external_id(record, "account_id")
        if not external_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_account_account", external_id)
        if odoo_id:
            return {"account_id": odoo_id}
        return {}

    @mapping
    def currency_id(self, record):
        external_id = self._extract_external_id(record, "currency_id")
        if not external_id:
            return {"currency_id": self.env.user.company_id.currency_id.id}
        binder = self.binder_for("odoo.res.currency")
        local_currency = binder.to_internal(external_id, unwrap=True)
        if local_currency:
            return {"currency_id": local_currency.id}
        return {"currency_id": self.env.user.company_id.currency_id.id}

    @mapping
    def sheet_id(self, record):
        external_id = self._extract_external_id(record, "sheet_id")
        if not external_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_hr_expense_sheet", external_id)
        if odoo_id:
            return {"sheet_id": odoo_id}
        return {}

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}
