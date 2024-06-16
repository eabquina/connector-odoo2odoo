import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class HrLeaveTypeBatchImporter(Component):
    """Import the Odoo Partner Category.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.leave.type.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.leave.type"]


class HrLeaveTypeImportMapper(Component):
    _name = "odoo.hr.leave.type.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.leave.type"]

    direct = [
        ("accrual_count", "accrual_count"),
        ("active", "active"),
        ("allocation_count", "allocation_count"),
        ("allocation_validation_type", "allocation_validation_type"),
        ("allows_negative", "allows_negative"),
        ("color", "color"),
        ("create_calendar_meeting", "create_calendar_meeting"),
        ("create_date", "create_date"),
        ("display_name", "display_name"),
        ("employee_requests", "employee_requests"),
        ("group_days_leave", "group_days_leave"),
        ("has_valid_allocation", "has_valid_allocation"),
        ("id", "id"),
        ("leave_validation_type", "leave_validation_type"),
        ("leaves_taken", "leaves_taken"),
        ("max_allowed_negative", "max_allowed_negative"),
        ("max_leaves", "max_leaves"),
        ("name", "name"),
        ("request_unit", "request_unit"),
        ("requires_allocation", "requires_allocation"),
        ("sequence", "sequence"),
        ("support_document", "support_document"),
        ("time_type", "time_type"),
        ("unpaid", "unpaid"),
        ("virtual_remaining_leaves", "virtual_remaining_leaves"),
        ("write_date", "write_date"),
    ]
    
    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.hr.leave.type")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        match_fields = ['name']
        filters = []

        for match_field in match_fields:
            if record[match_field]:
                filters.append((match_field, "=", record[match_field]))

        odoo_ids = self.env["hr.leave.type"].search(filters, limit=1)
        if odoo_ids:
            return {"odoo_id": odoo_ids[0].id}
        return {}


class HrLeaveTypeImporter(Component):
    _name = "odoo.hr.leave.type.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.leave.type"]
