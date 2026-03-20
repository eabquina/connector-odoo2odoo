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


class AccountPaymentTermBatchImporter(Component):
    _name = "odoo.account.payment.term.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.payment.term"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo payment terms %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 10}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountPaymentTermImporter(Component):
    _name = "odoo.account.payment.term.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.payment.term"]

    def _after_import(self, binding, force=False):
        """Import payment term lines inline."""
        res = super()._after_import(binding, force)
        remote_lines = _safe_value(self.odoo_record, "line_ids", [])
        if not remote_lines:
            return res
        # Read remote lines via RPC
        line_ids = [
            getattr(l, "id", l) for l in remote_lines
            if getattr(l, "id", l)
        ]
        if not line_ids:
            return res
        try:
            remote_line_data = self.work.odoo_api.api.execute_kw(
                "account.payment.term.line",
                "read",
                [line_ids],
                {"fields": ["value", "value_amount", "nb_days"]},
            )
        except Exception:
            _logger.warning(
                "Could not read payment term lines for external term %s",
                self.external_id,
                exc_info=True,
            )
            return res
        if not remote_line_data:
            return res
        # Replace local lines with remote line values
        line_vals = []
        for line in remote_line_data:
            vals = {}
            if "value" in line:
                vals["value"] = line["value"]
            if "value_amount" in line:
                vals["value_amount"] = line["value_amount"]
            if "nb_days" in line:
                vals["nb_days"] = line["nb_days"]
            if vals:
                line_vals.append((0, 0, vals))
        if line_vals:
            # Clear existing lines and write new ones
            binding.odoo_id.with_context(connector_no_export=True).write(
                {"line_ids": [(5, 0, 0)] + line_vals}
            )
        return res


class AccountPaymentTermImportMapper(Component):
    _name = "odoo.account.payment.term.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.payment.term"

    direct = [
        ("name", "name"),
        ("note", "note"),
        ("active", "active"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        name = _safe_value(record, "name", False)
        if not name:
            return {}
        term = self.env["account.payment.term"].search(
            [("name", "=", name)], limit=1
        )
        if term:
            return {"odoo_id": term.id}
        return {}

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}
