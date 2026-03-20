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


class AccountTaxBatchImporter(Component):
    _name = "odoo.account.tax.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.tax"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo account taxes %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 11}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountTaxImporter(Component):
    _name = "odoo.account.tax.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.tax"]

    def _import_dependencies(self, force=False):
        tax_group = _safe_value(self.odoo_record, "tax_group_id", False)
        if tax_group and getattr(tax_group, "id", False):
            self._import_dependency(
                tax_group.id, "odoo.account.tax.group", force=False
            )


class AccountTaxImportMapper(Component):
    _name = "odoo.account.tax.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.tax"

    direct = [
        ("name", "name"),
        ("amount", "amount"),
        ("sequence", "sequence"),
        ("description", "description"),
        ("price_include", "price_include"),
        ("include_base_amount", "include_base_amount"),
        ("active", "active"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """Match existing tax by name, type_tax_use, and amount."""
        name = _safe_value(record, "name", False)
        if not name:
            return {}
        type_tax_use = _safe_value(record, "type_tax_use", False)
        amount = _safe_value(record, "amount", False)
        domain = [("name", "=", name)]
        if type_tax_use:
            domain.append(("type_tax_use", "=", type_tax_use))
        if amount is not False:
            domain.append(("amount", "=", amount))
        tax = self.env["account.tax"].search(domain, limit=1)
        if tax:
            return {"odoo_id": tax.id}
        return {}

    @only_create
    @mapping
    def amount_type(self, record):
        amount_type = _safe_value(record, "amount_type", "percent")
        if not amount_type:
            amount_type = "percent"
        return {"amount_type": amount_type}

    @only_create
    @mapping
    def type_tax_use(self, record):
        type_tax_use = _safe_value(record, "type_tax_use", "sale")
        if not type_tax_use:
            type_tax_use = "sale"
        return {"type_tax_use": type_tax_use}

    @mapping
    def tax_scope(self, record):
        tax_scope = _safe_value(record, "tax_scope", False)
        if tax_scope:
            return {"tax_scope": tax_scope}
        return {}

    @mapping
    def tax_group_id(self, record):
        tax_group = _safe_value(record, "tax_group_id", False)
        if not tax_group or not getattr(tax_group, "id", False):
            return {}
        binder = self.binder_for("odoo.account.tax.group")
        local_group = binder.to_internal(tax_group.id, unwrap=True)
        if local_group:
            return {"tax_group_id": local_group.id}
        return {}

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}
