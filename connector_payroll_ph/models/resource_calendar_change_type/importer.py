import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class ResourceCalendarChangeTypeBatchImporter(Component):
    """Import work schedule change types from the external Odoo."""

    _name = "odoo.resource.calendar.change.type.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.resource.calendar.change.type"]


class ResourceCalendarChangeTypeImportMapper(Component):
    _name = "odoo.resource.calendar.change.type.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.resource.calendar.change.type"]

    direct = [
        ("name", "name"),
        ("code", "code"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        if record.code:
            existing = self.env["resource.calendar.change.type"].search(
                [("code", "=", record.code)], limit=1
            )
            if existing:
                return {"odoo_id": existing.id}
        if record.name:
            existing = self.env["resource.calendar.change.type"].search(
                [("name", "=", record.name)], limit=1
            )
            if existing:
                return {"odoo_id": existing.id}
        return {}


class ResourceCalendarChangeTypeImporter(Component):
    _name = "odoo.resource.calendar.change.type.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.resource.calendar.change.type"]
