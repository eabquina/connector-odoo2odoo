import logging

from odoo.addons.component.core import Component

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
        ("code", "code"),
        ("allocation_count", "allocation_count"),
        ("name", "name"),
        ("sequence", "sequence"),
        ("create_calendar_meeting", "create_calendar_meeting"),
        ("color", "color"),
        ("active", "active"),
        ("max_leaves", "max_leaves"),
        ("leaves_taken", "leaves_taken"),
        ("virtual_remaining_leaves", "virtual_remaining_leaves"),
        ("group_days_leave", "group_days_leave"),
        ("leave_validation_type", "leave_validation_type"),
        ("requires_allocation", "requires_allocation"),
        ("employee_requests", "employee_requests"),
        ("allocation_validation_type", "allocation_validation_type"),
        ("has_valid_allocation", "has_valid_allocation"),
        ("time_type", "time_type"),
        ("request_unit", "request_unit"),
        ("unpaid", "unpaid"),
        ("support_document", "support_document"),
        ("accrual_count", "accrual_count"),
        ("allows_negative", "allows_negative"),
        ("max_allowed_negative", "max_allowed_negative"),
        ("id", "id"),
        ("display_name", "display_name"),
        ("create_date", "create_date"),
        ("write_date", "write_date"),
        ("hr_attendance_overtime", "hr_attendance_overtime"),
        ("overtime_deductible", "overtime_deductible"),
        ("timesheet_generate", "timesheet_generate"),
    ]


class HrLeaveTypeImporter(Component):
    _name = "odoo.hr.leave.type.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.leave.type"]
