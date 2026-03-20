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


class AccountFiscalPositionBatchImporter(Component):
    _name = "odoo.account.fiscal.position.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.fiscal.position"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo fiscal positions %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 12}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountFiscalPositionImporter(Component):
    _name = "odoo.account.fiscal.position.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.fiscal.position"]

    def _after_import(self, binding, force=False):
        """Import tax and account mappings inline."""
        res = super()._after_import(binding, force)
        self._sync_tax_mappings(binding)
        self._sync_account_mappings(binding)
        return res

    def _sync_tax_mappings(self, binding):
        remote_tax_ids = _safe_value(self.odoo_record, "tax_ids", [])
        line_ids = [
            getattr(l, "id", l) for l in remote_tax_ids
            if getattr(l, "id", l)
        ]
        if not line_ids:
            return
        try:
            remote_data = self.work.odoo_api.api.execute_kw(
                "account.fiscal.position.tax",
                "read",
                [line_ids],
                {"fields": ["tax_src_id", "tax_dest_id"]},
            )
        except Exception:
            _logger.warning(
                "Could not read fiscal position tax mappings for %s",
                self.external_id,
                exc_info=True,
            )
            return
        tax_binder = self.binder_for("odoo.account.tax")
        line_vals = []
        for line in remote_data:
            src_ext = line.get("tax_src_id")
            if isinstance(src_ext, (list, tuple)):
                src_ext = src_ext[0]
            dst_ext = line.get("tax_dest_id")
            if isinstance(dst_ext, (list, tuple)):
                dst_ext = dst_ext[0]
            if not src_ext:
                continue
            local_src = tax_binder.to_internal(src_ext, unwrap=True)
            if not local_src:
                continue
            vals = {"tax_src_id": local_src.id}
            if dst_ext:
                local_dst = tax_binder.to_internal(dst_ext, unwrap=True)
                if local_dst:
                    vals["tax_dest_id"] = local_dst.id
            line_vals.append((0, 0, vals))
        if line_vals:
            binding.odoo_id.with_context(connector_no_export=True).write(
                {"tax_ids": [(5, 0, 0)] + line_vals}
            )

    def _sync_account_mappings(self, binding):
        remote_account_ids = _safe_value(self.odoo_record, "account_ids", [])
        line_ids = [
            getattr(l, "id", l) for l in remote_account_ids
            if getattr(l, "id", l)
        ]
        if not line_ids:
            return
        try:
            remote_data = self.work.odoo_api.api.execute_kw(
                "account.fiscal.position.account",
                "read",
                [line_ids],
                {"fields": ["account_src_id", "account_dest_id"]},
            )
        except Exception:
            _logger.warning(
                "Could not read fiscal position account mappings for %s",
                self.external_id,
                exc_info=True,
            )
            return
        account_binder = self.binder_for("odoo.account.account")
        line_vals = []
        for line in remote_data:
            src_ext = line.get("account_src_id")
            if isinstance(src_ext, (list, tuple)):
                src_ext = src_ext[0]
            dst_ext = line.get("account_dest_id")
            if isinstance(dst_ext, (list, tuple)):
                dst_ext = dst_ext[0]
            if not src_ext:
                continue
            local_src = account_binder.to_internal(src_ext, unwrap=True)
            if not local_src:
                continue
            vals = {"account_src_id": local_src.id}
            if dst_ext:
                local_dst = account_binder.to_internal(dst_ext, unwrap=True)
                if local_dst:
                    vals["account_dest_id"] = local_dst.id
            line_vals.append((0, 0, vals))
        if line_vals:
            binding.odoo_id.with_context(connector_no_export=True).write(
                {"account_ids": [(5, 0, 0)] + line_vals}
            )


class AccountFiscalPositionImportMapper(Component):
    _name = "odoo.account.fiscal.position.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.fiscal.position"

    direct = [
        ("name", "name"),
        ("auto_apply", "auto_apply"),
        ("note", "note"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        name = _safe_value(record, "name", False)
        if not name:
            return {}
        fp = self.env["account.fiscal.position"].search(
            [("name", "=", name)], limit=1
        )
        if fp:
            return {"odoo_id": fp.id}
        return {}

    @mapping
    def country_id(self, record):
        country = _safe_value(record, "country_id", False)
        if not country or not getattr(country, "id", False):
            return {}
        country_name = _safe_value(country, "name", False)
        if not country_name:
            return {}
        local_country = self.env["res.country"].search(
            [("name", "=", country_name)], limit=1
        )
        if local_country:
            return {"country_id": local_country.id}
        return {}

    @mapping
    def country_group_id(self, record):
        country_group = _safe_value(record, "country_group_id", False)
        if not country_group or not getattr(country_group, "id", False):
            return {}
        group_name = _safe_value(country_group, "name", False)
        if not group_name:
            return {}
        local_group = self.env["res.country.group"].search(
            [("name", "=", group_name)], limit=1
        )
        if local_group:
            return {"country_group_id": local_group.id}
        return {}

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}
