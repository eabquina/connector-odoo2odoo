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


class HrEmployeeBatchImporter(Component):
    _name = "odoo.hr.employee.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.employee"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo employees %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 10}
            self._import_record(external_id, job_options=job_options, force=force)


class HrEmployeeImporter(Component):
    _name = "odoo.hr.employee.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.employee"]

    def _import_dependencies(self, force=False):
        user = _safe_value(self.odoo_record, "user_id", False)
        if user and getattr(user, "id", False):
            self._import_dependency(user.id, "odoo.res.users", force=force)


class HrEmployeeImportMapper(Component):
    _name = "odoo.hr.employee.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.hr.employee"

    direct = [
        ("name", "name"),
        ("work_email", "work_email"),
        ("work_phone", "work_phone"),
        ("job_title", "job_title"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """Match by linked user or by name + work_email."""
        user = _safe_value(record, "user_id", False)
        if user and getattr(user, "id", False):
            binder = self.binder_for("odoo.res.users")
            local_user = binder.to_internal(user.id, unwrap=True)
            if local_user:
                employee = self.env["hr.employee"].search(
                    [("user_id", "=", local_user.id)], limit=1
                )
                if employee:
                    return {"odoo_id": employee.id}
        name = _safe_value(record, "name", False)
        if name:
            employee = self.env["hr.employee"].search(
                [("name", "=", name)], limit=1
            )
            if employee:
                return {"odoo_id": employee.id}
        return {}

    @mapping
    def user_id(self, record):
        user = _safe_value(record, "user_id", False)
        if not user or not getattr(user, "id", False):
            return {}
        binder = self.binder_for("odoo.res.users")
        local_user = binder.to_internal(user.id, unwrap=True)
        if local_user:
            return {"user_id": local_user.id}
        return {}

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}
