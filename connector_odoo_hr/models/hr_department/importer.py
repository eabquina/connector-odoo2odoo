import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class HrDepartmentBatchImporter(Component):
    """Import the Odoo Department.

    For everyDepartment in the list, a delayed department is created.
    Import from a date
    """

    _name = "odoo.hr.department.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.department"]


class HrDepartmentImportMapper(Component):
    _name = "odoo.hr.department.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.department"]

    direct = [
        ("absence_of_today", "absence_of_today"),
        ("active", "active"),
        ("allocation_to_approve_count", "allocation_to_approve_count"),
        ("color", "color"),
        ("complete_name", "complete_name"),
        ("create_date", "create_date"),
        ("display_name", "display_name"),
        ("expected_employee", "expected_employee"),
        ("expense_sheets_to_approve_count", "expense_sheets_to_approve_count"),
        ("has_message", "has_message"),
        ("leave_to_approve_count", "leave_to_approve_count"),
        ("message_attachment_count", "message_attachment_count"),
        ("message_has_error", "message_has_error"),
        ("message_has_error_counter", "message_has_error_counter"),
        ("message_has_sms_error", "message_has_sms_error"),
        ("message_is_follower", "message_is_follower"),
        ("message_needaction", "message_needaction"),
        ("message_needaction_counter", "message_needaction_counter"),
        ("name", "name"),
        ("new_applicant_count", "new_applicant_count"),
        ("new_hired_employee", "new_hired_employee"),
        ("note", "note"),
        ("parent_path", "parent_path"),
        ("plans_count", "plans_count"),
        ("total_employee", "total_employee"),
        ("write_date", "write_date"),
    ]


class HrDepartmentImporter(Component):
    _name = "odoo.hr.department.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.department"]
