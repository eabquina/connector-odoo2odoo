import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class ResourceCalendarChangeBatchImporter(Component):
    """Import work schedule change requests from the external Odoo."""

    _name = "odoo.resource.calendar.change.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.resource.calendar.change"]


class ResourceCalendarChangeImportMapper(Component):
    _name = "odoo.resource.calendar.change.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.resource.calendar.change"]

    direct = [
        ("name", "name"),
        ("duration", "duration"),
        ("date_from", "date_from"),
        ("date_to", "date_to"),
        ("purpose", "purpose"),
        ("cancel_reason", "cancel_reason"),
        ("state", "state"),
        ("current_user_boolean", "current_user_boolean"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        if record.name:
            existing = self.env["resource.calendar.change"].search(
                [("name", "=", record.name)], limit=1
            )
            if existing:
                return {"odoo_id": existing.id}
        return {}

    @mapping
    def employee_id(self, record):
        if not record.employee_id:
            return {}
        binder = self.binder_for("odoo.hr.employee")
        employee = binder.to_internal(record.employee_id.id, unwrap=True)
        if not employee:
            return {}
        return {"employee_id": employee.id}

    @mapping
    def type_id(self, record):
        if not record.type_id:
            return {}
        binder = self.binder_for("odoo.resource.calendar.change.type")
        change_type = binder.to_internal(record.type_id.id, unwrap=True)
        if not change_type:
            return {}
        return {"type_id": change_type.id}

    @mapping
    def calendar_to(self, record):
        if not record.calendar_to:
            return {}
        local_calendar = self.env["resource.calendar"].search(
            [("name", "=", record.calendar_to.name)], limit=1
        )
        if not local_calendar:
            _logger.warning(
                "Cannot map external resource.calendar '%s' (id=%s). Create it locally or align names.",
                record.calendar_to.name,
                record.calendar_to.id,
            )
            return {}
        return {"calendar_to": local_calendar.id}


class ResourceCalendarChangeImporter(Component):
    _name = "odoo.resource.calendar.change.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.resource.calendar.change"]

    def _import_dependencies(self, force=False):
        if self.odoo_record.employee_id:
            self._import_dependency(
                self.odoo_record.employee_id.id, "odoo.hr.employee", force=force
            )
        if self.odoo_record.type_id:
            self._import_dependency(
                self.odoo_record.type_id.id,
                "odoo.resource.calendar.change.type",
                force=force,
            )

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if getattr(self.odoo_record, "change_lines", False):
            for line in self.odoo_record.change_lines:
                self.env["odoo.resource.calendar.change.lines"].with_delay().import_record(
                    self.backend_record, line.id, force=force
                )
        return res
