import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class HrOvertimeTypeBatchImporter(Component):
    """Import the Odoo Partner Category.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.overtime.type.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.overtime.type"]


class HrOvertimeTypeImportMapper(Component):
    _name = "odoo.overtime.type.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.overtime.type"]

    direct = [
        ("display_name", "display_name"),
        ("name", "name"),
        ("duration_type", "duration_type"),
        ("type", "type"),
    ]
    
    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.overtime.type")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        match_fields = ['name']
        filters = []

        for match_field in match_fields:
            if record[match_field]:
                filters.append((match_field, "=", record[match_field]))

        odoo_ids = self.env["overtime.type"].search(filters, limit=1)
        if odoo_ids:
            return {"odoo_id": odoo_ids[0].id}
        return {}


class HrOvertimeTypeImporter(Component):
    _name = "odoo.overtime.type.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.overtime.type"]
