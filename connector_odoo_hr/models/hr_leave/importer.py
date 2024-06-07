import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class HrLeaveBatchImporter(Component):
    """Import the Odoo HR HrLeave model.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.leave.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.leave"]


class HrLeaveImportMapper(Component):
    _name = "odoo.hr.leave.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.leave"]

    direct = [
        ("active", "active"),
        ("active_employee", "active_employee"),
        ("activity_date_deadline", "activity_date_deadline"),
        ("activity_exception_decoration", "activity_exception_decoration"),
        ("activity_exception_icon", "activity_exception_icon"),
        ("activity_state", "activity_state"),
        ("activity_summary", "activity_summary"),
        ("activity_type_icon", "activity_type_icon"),
        ("can_approve", "can_approve"),
        ("can_cancel", "can_cancel"),
        ("can_reset", "can_reset"),
        ("color", "color"),
        ("create_date", "create_date"),
        ("date_from", "date_from"),
        ("date_to", "date_to"),
        ("display_name", "display_name"),
        ("duration_display", "duration_display"),
        ("employee_overtime", "employee_overtime"),
        ("has_mandatory_day", "has_mandatory_day"),
        ("has_message", "has_message"),
        ("holiday_type", "holiday_type"),
        ("id", "id"),
        ("is_hatched", "is_hatched"),
        ("is_striked", "is_striked"),
        ("is_user_only_responsible", "is_user_only_responsible"),
        ("last_several_days", "last_several_days"),
        ("leave_type_increases_duration", "leave_type_increases_duration"),
        ("leave_type_request_unit", "leave_type_request_unit"),
        ("leave_type_support_document", "leave_type_support_document"),
        ("message_attachment_count", "message_attachment_count"),
        ("message_has_error", "message_has_error"),
        ("message_has_error_counter", "message_has_error_counter"),
        ("message_has_sms_error", "message_has_sms_error"),
        ("message_is_follower", "message_is_follower"),
        ("message_needaction", "message_needaction"),
        ("message_needaction_counter", "message_needaction_counter"),
        ("multi_employee", "multi_employee"),
        ("my_activity_date_deadline", "my_activity_date_deadline"),
        ("name", "name"),
        ("notes", "notes"),
        ("number_of_days", "number_of_days"),
        ("number_of_days_display", "number_of_days_display"),
        ("number_of_hours", "number_of_hours"),
        ("number_of_hours_display", "number_of_hours_display"),
        ("number_of_hours_text", "number_of_hours_text"),
        ("overtime_deductible", "overtime_deductible"),
        ("private_name", "private_name"),
        ("report_note", "report_note"),
        ("request_date_from", "request_date_from"),
        ("request_date_from_period", "request_date_from_period"),
        ("request_date_to", "request_date_to"),
        ("request_hour_from", "request_hour_from"),
        ("request_hour_to", "request_hour_to"),
        ("request_unit_half", "request_unit_half"),
        ("request_unit_hours", "request_unit_hours"),
        ("state", "state"),
        ("supported_attachment_ids_count", "supported_attachment_ids_count"),
        ("tz", "tz"),
        ("tz_mismatch", "tz_mismatch"),
        ("validation_type", "validation_type"),
        ("write_date", "write_date"),
    ]
    
    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {employee_id: employee_id.id}
    @mapping
    def department_id(self, record):
        if record.department_id:
            binder = self.binder_for("odoo.hr.department")
            department_id = binder.to_internal(record.department_id.id, unwrap=True)
            return {department_id: department_id.id}
    @mapping
    def all_employee_ids(self, record):
        if record.all_employee_ids:
            binder = self.binder_for("odoo.hr.employee")
            all_employee_ids = binder.to_internal(record.all_employee_ids.id, unwrap=True)
            return {all_employee_ids: all_employee_ids.id}
    @mapping
    def employee_ids(self, record):
        if record.employee_ids:
            binder = self.binder_for("odoo.hr.employee")
            employee_ids = binder.to_internal(record.employee_ids.id, unwrap=True)
            return {employee_ids: employee_ids.id}
    @mapping
    def manager_id(self, record):
        if record.manager_id:
            binder = self.binder_for("odoo.hr.employee")
            manager_id = binder.to_internal(record.manager_id.id, unwrap=True)
            return {manager_id: manager_id.id}
    @mapping
    def first_approver_id(self, record):
        if record.first_approver_id:
            binder = self.binder_for("odoo.hr.employee")
            first_approver_id = binder.to_internal(record.first_approver_id.id, unwrap=True)
            return {first_approver_id: first_approver_id.id}
    @mapping
    def second_approver_id(self, record):
        if record.second_approver_id:
            binder = self.binder_for("odoo.hr.employee")
            second_approver_id = binder.to_internal(record.second_approver_id.id, unwrap=True)
            return {second_approver_id: second_approver_id.id}
    @mapping
    def category_id(self, record):
        if record.category_id:
            binder = self.binder_for("odoo.hr.employee.category")
            category_id = binder.to_internal(record.category_id.id, unwrap=True)
            return {category_id: category_id.id}
    @mapping
    def parent_id(self, record):
        if record.parent_id:
            binder = self.binder_for("odoo.hr.leave")
            parent_id = binder.to_internal(record.parent_id.id, unwrap=True)
            return {parent_id: parent_id.id}
    @mapping
    def linked_request_ids(self, record):
        if record.linked_request_ids:
            binder = self.binder_for("odoo.hr.leave")
            linked_request_ids = binder.to_internal(record.linked_request_ids.id, unwrap=True)
            return {linked_request_ids: linked_request_ids.id}
    @mapping
    def holiday_status_id(self, record):
        if record.holiday_status_id:
            binder = self.binder_for("odoo.hr.leave.type")
            holiday_status_id = binder.to_internal(record.holiday_status_id.id, unwrap=True)
            return {holiday_status_id: holiday_status_id.id}        


class HrLeaveImporter(Component):
    _name = "odoo.hr.leave.importer"
    _inherit = "odoo.importer"
    _inherits = "AbstractModel"
    _apply_on = ["odoo.hr.leave"]
    
    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        
        if self.odoo_record.employee_id:
            _logger.info("Importing employee_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.employee_id.id, "odoo.hr.employee", force=force
            )
        if self.odoo_record.department_id:
            _logger.info("Importing department_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.department_id.id, "odoo.hr.department", force=force
            )
        if self.odoo_record.all_employee_ids:
            _logger.info("Importing all_employee_ids for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.all_employee_ids.id, "odoo.hr.employee", force=force
            )
        if self.odoo_record.employee_ids:
            _logger.info("Importing employee_ids for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.employee_ids.id, "odoo.hr.employee", force=force
            )
        if self.odoo_record.manager_id:
            _logger.info("Importing manager_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.manager_id.id, "odoo.hr.employee", force=force
            )
        if self.odoo_record.first_approver_id:
            _logger.info("Importing first_approver_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.first_approver_id.id, "odoo.hr.employee", force=force
            )
        if self.odoo_record.second_approver_id:
            _logger.info("Importing second_approver_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.second_approver_id.id, "odoo.hr.employee", force=force
            )
        if self.odoo_record.category_id:
            _logger.info("Importing category_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.category_id.id, "odoo.hr.employee.category", force=force
            )
        if self.odoo_record.parent_id:
            _logger.info("Importing parent_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.parent_id.id, "odoo.hr.leave", force=force
            )
        if self.odoo_record.linked_request_ids:
            _logger.info("Importing linked_request_ids for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.linked_request_ids.id, "odoo.hr.leave", force=force
            )
        if self.odoo_record.holiday_status_id:
            _logger.info("Importing holiday_status_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.holiday_status_id.id, "odoo.hr.leave.type", force=force
            )