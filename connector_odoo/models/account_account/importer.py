import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class AccountAccountBatchImporter(Component):
    """Import the Odoo Account Account.

    For every Account Account in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.account.account.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.account"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo Account Account %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountAccountImportMapper(Component):
    _name = "odoo.account.account.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.account.account"]

    direct = [
        ("code", "code"),
        ("name", "name"),
        ("reconcile", "reconcile"),
        ("note", "note"),
    ]

    @only_create
    @mapping
    def check_account_account_exists(self, record):
        res = {}

        account_model = self.env["account.account"]
        domain = [("code", "=", record.code)]
        company_id = self.env.user.company_id.id
        if "company_id" in account_model._fields:
            domain.insert(0, ("company_id", "=", company_id))
        elif "company_ids" in account_model._fields:
            domain.insert(0, ("company_ids", "in", [company_id]))
        account_id = account_model.search(domain, limit=1)
        _logger.debug("Account Account found for %s : %s" % (record, account_id))
        if account_id:
            res.update({"odoo_id": account_id.id})
        return res

    @mapping
    def currency_id(self, record):
        if "currency_id" not in self.env["account.account"]._fields:
            return {}
        origin = getattr(self.work, "origing_account_id", False)
        if origin:
            return {"currency_id": origin.currency_id.id}
        try:
            currency = record.currency_id
        except AttributeError:
            currency = False
        if not currency:
            return {}
        currency_name = getattr(currency, "name", False)
        if not currency_name:
            return {}
        local_currency = self.env["res.currency"].search(
            [("name", "=", currency_name)], limit=1
        )
        if local_currency:
            return {"currency_id": local_currency.id}
        return {}

    @mapping
    def deprecated(self, record):
        if "deprecated" not in self.env["account.account"]._fields:
            return {}
        origin = getattr(self.work, "origing_account_id", False)
        if origin:
            return {"deprecated": origin.deprecated}
        try:
            deprecated = record.deprecated
        except AttributeError:
            return {}
        return {"deprecated": deprecated}

    @mapping
    def user_type_id(self, record):
        # Odoo 13: account.account.user_type_id (m2o -> account.account.type)
        # Odoo 14+ (incl. 17/18): user_type_id removed in favor of account_type
        account_model = self.env["account.account"]
        origin = getattr(self.work, "origing_account_id", False)

        if "account_type" in account_model._fields:
            account_type = False

            try:
                account_type = record.account_type
            except AttributeError:
                account_type = False

            if not account_type:
                try:
                    user_type = record.user_type_id
                except AttributeError:
                    user_type = False

                if user_type:
                    try:
                        legacy_type = user_type.type
                    except AttributeError:
                        legacy_type = False
                    try:
                        legacy_group = user_type.internal_group
                    except AttributeError:
                        legacy_group = False

                    if legacy_type == "receivable":
                        account_type = "asset_receivable"
                    elif legacy_type == "payable":
                        account_type = "liability_payable"
                    elif legacy_type == "liquidity":
                        account_type = "asset_cash"
                    elif legacy_group == "asset":
                        account_type = "asset_current"
                    elif legacy_group == "liability":
                        account_type = "liability_current"
                    elif legacy_group == "equity":
                        account_type = "equity"
                    elif legacy_group == "income":
                        account_type = "income"
                    elif legacy_group == "expense":
                        account_type = "expense"
                    elif legacy_group == "off_balance":
                        account_type = "off_balance"

            if not account_type and origin and "account_type" in origin._fields:
                account_type = origin.account_type

            if not account_type:
                try:
                    code = str(record.code or "")
                except AttributeError:
                    code = ""
                if code.startswith("1"):
                    account_type = "asset_current"
                elif code.startswith("2"):
                    account_type = "liability_current"
                elif code.startswith("3"):
                    account_type = "equity"
                elif code.startswith("4"):
                    account_type = "income"
                else:
                    account_type = "expense"

            return {"account_type": account_type}

        if "user_type_id" in account_model._fields and origin and "user_type_id" in origin._fields:
            return {"user_type_id": origin.user_type_id.id}

        return {}

    @mapping
    def tax_ids(self, record):
        if "tax_ids" not in self.env["account.account"]._fields:
            return {}
        origin = getattr(self.work, "origing_account_id", False)
        if not origin:
            return {}
        return {"tax_ids": [(6, 0, origin.tax_ids.ids)]}

    @mapping
    def company_id(self, record):
        account_model = self.env["account.account"]
        company_id = self.env.user.company_id.id
        if "company_id" in account_model._fields:
            return {"company_id": company_id}
        if "company_ids" in account_model._fields:
            return {"company_ids": [(6, 0, [company_id])]}
        return {}

    @mapping
    def tag_ids(self, record):
        if "tag_ids" not in self.env["account.account"]._fields:
            return {}
        origin = getattr(self.work, "origing_account_id", False)
        if not origin:
            return {}
        return {"tag_ids": [(6, 0, origin.tag_ids.ids)]}

    @mapping
    def group_id(self, record):
        if "group_id" not in self.env["account.account"]._fields:
            return {}
        origin = getattr(self.work, "origing_account_id", False)
        if not origin:
            return {}
        return {"group_id": origin.group_id.id}

    @mapping
    def root_id(self, record):
        if "root_id" not in self.env["account.account"]._fields:
            return {}
        origin = getattr(self.work, "origing_account_id", False)
        if not origin:
            return {}
        return {"root_id": origin.root_id.id}

    @mapping
    def allowed_journal_ids(self, record):
        if "allowed_journal_ids" not in self.env["account.account"]._fields:
            return {}
        origin = getattr(self.work, "origing_account_id", False)
        if not origin:
            return {}
        return {"allowed_journal_ids": [(6, 0, origin.allowed_journal_ids.ids)]}


class AccountAccountImporter(Component):
    _name = "odoo.account.account.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.account"]

    def _find_origin_account(self, code):
        code = (code or "").strip()
        if not code:
            return self.env["account.account"]

        account_model = self.env["account.account"]
        company_id = self.env.user.company_id.id
        company_domain = []
        if "company_id" in account_model._fields:
            company_domain = [("company_id", "=", company_id)]
        elif "company_ids" in account_model._fields:
            company_domain = [("company_ids", "in", [company_id])]

        sample = account_model.search(company_domain, limit=1)
        lengths = []
        if sample and sample.code:
            lengths.append(len(sample.code))
        if code:
            lengths.append(len(code))
        lengths = [l for l in dict.fromkeys(lengths) if l > 0]

        candidates = []
        for length in lengths:
            max_prefix = min(len(code), length)
            for prefix_len in range(max_prefix, 0, -1):
                prefix = code[:prefix_len]
                if prefix_len < length:
                    candidates.append(prefix + ("0" * (length - prefix_len)))
                candidates.append(prefix)

        seen = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            origin = account_model.search(
                company_domain + [("code", "=", candidate)], limit=1
            )
            if origin:
                return origin

        return account_model

    def _must_skip(
        self,
    ):
        account_model = self.env["account.account"]
        domain = [("code", "=", self.odoo_record.code)]
        company_id = self.env.user.company_id.id
        if "company_id" in account_model._fields:
            domain.insert(0, ("company_id", "=", company_id))
        elif "company_ids" in account_model._fields:
            domain.insert(0, ("company_ids", "in", [company_id]))
        return account_model.search(domain, limit=1)

    def _before_import(
        self,
    ):
        account_model = self.env["account.account"]
        domain = [("code", "=", self.odoo_record.code)]
        company_id = self.env.user.company_id.id
        if "company_id" in account_model._fields:
            domain.insert(0, ("company_id", "=", company_id))
        elif "company_ids" in account_model._fields:
            domain.insert(0, ("company_ids", "in", [company_id]))
        account_id = account_model.search(domain, limit=1)
        if not account_id:
            origin = self._find_origin_account(getattr(self.odoo_record, "code", ""))
            if origin:
                self.work.origing_account_id = origin
            else:
                self.work.origing_account_id = self.env["account.account"]
                _logger.warning(
                    "No origin account found for code %s; importing with minimal fields.",
                    getattr(self.odoo_record, "code", ""),
                )
