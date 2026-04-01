import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class ResourceCalendarChangeLinesBatchImporter(Component):
    """Import work schedule change request lines from the external Odoo."""

    _name = "odoo.resource.calendar.change.lines.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.resource.calendar.change.lines"]


class ResourceCalendarChangeLinesImportMapper(Component):
    _name = "odoo.resource.calendar.change.lines.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.resource.calendar.change.lines"]

    direct = [
        ("date", "date"),
        ("reason", "reason"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        if not record.request_id or not record.date:
            return {}
        req_binder = self.binder_for("odoo.resource.calendar.change")
        local_request = req_binder.to_internal(record.request_id.id, unwrap=True)
        if not local_request:
            return {}
        existing = self.env["resource.calendar.change.lines"].search(
            [("request_id", "=", local_request.id), ("date", "=", record.date)],
            limit=1,
        )
        if existing:
            return {"odoo_id": existing.id}
        return {}

    @mapping
    def request_id(self, record):
        if not record.request_id:
            return {}
        binder = self.binder_for("odoo.resource.calendar.change")
        local_request = binder.to_internal(record.request_id.id, unwrap=True)
        if not local_request:
            return {}
        return {"request_id": local_request.id}

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


class ResourceCalendarChangeLinesImporter(Component):
    _name = "odoo.resource.calendar.change.lines.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.resource.calendar.change.lines"]

    def _import_dependencies(self, force=False):
        if self.odoo_record.request_id:
            self._import_dependency(
                self.odoo_record.request_id.id,
                "odoo.resource.calendar.change",
                force=force,
            )
        if self.odoo_record.type_id:
            self._import_dependency(
                self.odoo_record.type_id.id,
                "odoo.resource.calendar.change.type",
                force=force,
            )
