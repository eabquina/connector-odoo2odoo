# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import IDMissingInBackend

_logger = logging.getLogger(__name__)


def _safe_value(record, name, default=False):
    try:
        value = getattr(record, name, default)
    except Exception:
        return default
    if callable(value):
        return default
    return value


class _RemoteRelationValue:
    def __init__(self, value):
        self.id = value


class _RemoteRecordValue:
    def __init__(self, values):
        self._values = {}
        for key, value in values.items():
            self._values[key] = self._wrap(value)

    def _wrap(self, value):
        if not value:
            return value
        if isinstance(value, tuple) and len(value) == 2:
            return _RemoteRelationValue(value[0])
        if isinstance(value, list):
            if len(value) == 2 and isinstance(value[0], int):
                return _RemoteRelationValue(value[0])
            if value and all(isinstance(item, int) for item in value):
                return [_RemoteRelationValue(item) for item in value]
        return value

    def __getattr__(self, name):
        if name in self._values:
            return self._values[name]
        raise AttributeError(name)

    def __getitem__(self, name):
        return self._values[name]

    def get(self, name, default=False):
        return self._values.get(name, default)


# -- account.move --


class AccountMoveBatchImporter(Component):
    """Import the Odoo Account Moves.

    For every account move in the list, a delayed job is created.
    """

    _name = "odoo.account.move.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.move"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo account moves %s returned %s items",
            filters,
            len(updated_ids),
        )
        for external_id in updated_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountMoveImporter(Component):
    _name = "odoo.account.move.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.move"]

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
        remote_line_ids = binding._get_remote_move_line_ids()
        binding.backend_move_line_count = len(remote_line_ids)
        if remote_line_ids:
            for line_id in remote_line_ids:
                self.env["odoo.account.move.line"].with_delay().import_record(
                    self.backend_record, line_id, force
                )
        if binding.backend_state == "posted" and binding.odoo_id.state == "draft":
            binding.with_delay()._post_if_needed()
        return res


class AccountMoveImportMapper(Component):
    _name = "odoo.account.move.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.move"

    direct = [
        ("ref", "ref"),
        ("narration", "narration"),
        ("state", "backend_state"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """Try to match by name (sequence number)."""
        name = _safe_value(record, "name", False)
        if not name or name == "/":
            return {}
        move = self.env["account.move"].search([("name", "=", name)], limit=1)
        if move:
            return {"odoo_id": move.id}
        return {}

    @only_create
    @mapping
    def move_type(self, record):
        move_type = _safe_value(record, "move_type", "entry")
        if not move_type:
            move_type = "entry"
        return {"move_type": move_type}

    @mapping
    def date(self, record):
        date = _safe_value(record, "date", False)
        if date:
            return {"date": date}
        return {}

    @mapping
    def invoice_date(self, record):
        invoice_date = _safe_value(record, "invoice_date", False)
        if invoice_date:
            return {"invoice_date": invoice_date}
        return {}

    @mapping
    def invoice_date_due(self, record):
        invoice_date_due = _safe_value(record, "invoice_date_due", False)
        if invoice_date_due:
            return {"invoice_date_due": invoice_date_due}
        return {}

    @mapping
    def payment_reference(self, record):
        payment_reference = _safe_value(record, "payment_reference", False)
        if payment_reference:
            return {"payment_reference": payment_reference}
        return {}

    @mapping
    def backend_amount_total(self, record):
        amount_total = _safe_value(record, "amount_total", 0.0)
        return {"backend_amount_total": amount_total}

    @mapping
    def backend_amount_residual(self, record):
        amount_residual = _safe_value(record, "amount_residual", 0.0)
        return {"backend_amount_residual": amount_residual}

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

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}


# -- account.move.line --


class AccountMoveLineBatchImporter(Component):
    """Import the Odoo Account Move Lines."""

    _name = "odoo.account.move.line.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.move.line"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo account move lines %s returned %s items",
            filters,
            len(updated_ids),
        )
        for external_id in updated_ids:
            job_options = {"priority": 16}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountMoveLineImporter(Component):
    _name = "odoo.account.move.line.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.move.line"]

    def _read_remote_fields(self, fields):
        rows = self.work.odoo_api.api.execute_kw(
            "account.move.line",
            "read",
            [[int(self.external_id)]],
            {"fields": fields},
        )
        if isinstance(rows, dict):
            rows = [rows]
        if not rows:
            raise IDMissingInBackend
        return rows[0]

    def _get_odoo_data(self):
        data = self._read_remote_fields(
            [
                "id",
                "name",
                "move_id",
                "account_id",
                "partner_id",
                "product_id",
                "product_uom_id",
                "quantity",
                "price_unit",
                "debit",
                "credit",
                "balance",
                "amount_currency",
                "currency_id",
                "display_type",
                "date_maturity",
            ]
        )
        return _RemoteRecordValue(data)

    def _import_dependencies(self, force):
        """Import the dependencies for the record"""
        product_id = self._extract_external_id("product_id")
        if product_id:
            self._import_dependency(product_id, "odoo.product.product", force=force)

        account_id = self._extract_external_id("account_id")
        if account_id:
            self._import_dependency(account_id, "odoo.account.account", force=False)

        partner_id = self._extract_external_id("partner_id")
        if partner_id:
            self._import_dependency(partner_id, "odoo.res.partner", force=force)

    def _extract_external_id(self, field_name):
        value = _safe_value(self.odoo_record, field_name, False)
        if not value:
            return False
        value_id = getattr(value, "id", False)
        if callable(value_id):
            return False
        return value_id or False


class AccountMoveLineImportMapper(Component):
    _name = "odoo.account.move.line.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.move.line"

    direct = [
        ("name", "name"),
        ("quantity", "quantity"),
        ("price_unit", "price_unit"),
        ("debit", "debit"),
        ("credit", "credit"),
        ("amount_currency", "amount_currency"),
        ("display_type", "display_type"),
        ("date_maturity", "date_maturity"),
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
    def move_id(self, record):
        external_move_id = self._extract_external_id(record, "move_id")
        if not external_move_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_account_move", external_move_id)
        if not odoo_id:
            _logger.warning(
                "Skipping move_id mapping for move line %s: missing account.move binding "
                "for backend %s external move %s",
                getattr(record, "id", "n/a"),
                self.backend_record.id,
                external_move_id,
            )
            return {}
        return {"move_id": odoo_id}

    @mapping
    def account_id(self, record):
        external_account_id = self._extract_external_id(record, "account_id")
        if not external_account_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_account_account", external_account_id)
        if not odoo_id:
            _logger.warning(
                "Skipping account_id mapping for move line %s: missing account.account binding "
                "for backend %s external account %s",
                getattr(record, "id", "n/a"),
                self.backend_record.id,
                external_account_id,
            )
            return {}
        return {"account_id": odoo_id}

    @mapping
    def partner_id(self, record):
        external_partner_id = self._extract_external_id(record, "partner_id")
        if not external_partner_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_res_partner", external_partner_id)
        if not odoo_id:
            return {}
        return {"partner_id": odoo_id}

    @mapping
    def product_id(self, record):
        if _safe_value(record, "display_type", False):
            return {}
        external_product_id = self._extract_external_id(record, "product_id")
        if not external_product_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_product_product", external_product_id)
        if not odoo_id:
            return {}
        return {"product_id": odoo_id}

    @mapping
    def product_uom_id(self, record):
        if _safe_value(record, "display_type", False):
            return {}
        external_uom_id = self._extract_external_id(record, "product_uom_id")
        if not external_uom_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_uom_uom", external_uom_id)
        if not odoo_id:
            return {}
        return {"product_uom_id": odoo_id}

    @mapping
    def currency_id(self, record):
        external_currency_id = self._extract_external_id(record, "currency_id")
        if not external_currency_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_res_currency", external_currency_id)
        if not odoo_id:
            return {}
        currency = self.env["res.currency"].browse(odoo_id)
        if currency.exists():
            return {"currency_id": currency.id}
        return {}
