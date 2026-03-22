# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class AccountJournalBatchImporter(Component):
    """Import the Odoo Account Journals.

    For every journal in the list, a delayed job is created.
    """

    _name = "odoo.account.journal.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.journal"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo account journals %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 12}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountJournalImporter(Component):
    _name = "odoo.account.journal.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.journal"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        currency = getattr(self.odoo_record, "currency_id", False)
        if currency and getattr(currency, "id", False):
            self._import_dependency(currency.id, "odoo.res.currency", force=False)


class AccountJournalImportMapper(Component):
    _name = "odoo.account.journal.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.journal"

    direct = [
        ("name", "name"),
    ]

    @only_create
    @mapping
    def code(self, record):
        code = getattr(record, "code", False)
        if callable(code):
            return {}
        if not code:
            return {}
        return {"code": code}

    # Odoo 18 valid journal types
    _VALID_JOURNAL_TYPES = {"sale", "purchase", "cash", "bank", "general"}
    # Map removed Odoo 13 types to their Odoo 18 equivalents
    _JOURNAL_TYPE_MAP = {
        "situation": "general",  # opening entries journal
    }

    @only_create
    @mapping
    def type(self, record):
        journal_type = getattr(record, "type", False)
        if callable(journal_type):
            return {}
        if not journal_type:
            return {}
        # Map deprecated types to valid Odoo 18 types
        journal_type = self._JOURNAL_TYPE_MAP.get(journal_type, journal_type)
        if journal_type not in self._VALID_JOURNAL_TYPES:
            _logger.warning(
                "Unknown journal type %r from remote, defaulting to 'general'",
                journal_type,
            )
            journal_type = "general"
        return {"type": journal_type}

    @only_create
    @mapping
    def odoo_id(self, record):
        """Match existing journal by code and type."""
        code = getattr(record, "code", False)
        journal_type = getattr(record, "type", False)
        if not code:
            return {}
        # Also remap type for the search domain
        if journal_type:
            journal_type = self._JOURNAL_TYPE_MAP.get(journal_type, journal_type)
        domain = [("code", "=", code)]
        if journal_type:
            domain.append(("type", "=", journal_type))
        journal = self.env["account.journal"].search(domain, limit=1)
        if journal:
            return {"odoo_id": journal.id}
        return {}

    @mapping
    def currency_id(self, record):
        currency = getattr(record, "currency_id", False)
        if not currency or not getattr(currency, "id", False):
            return {}
        binder = self.binder_for("odoo.res.currency")
        local_currency = binder.to_internal(currency.id, unwrap=True)
        if local_currency:
            return {"currency_id": local_currency.id}
        return {}

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}
