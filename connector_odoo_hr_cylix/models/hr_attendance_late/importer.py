import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class AttendanceBatchImporter(Component):
    """Import the Odoo HR Attendance model.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.attendance.late.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.attendance.late"]


class HrAttendanceLateImportMapper(Component):
    _name = "odoo.hr.attendance.late.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.attendance.late"]

    direct = [
        ("date", "date"),
        ("name", "name"),
        ("display_name", "display_name"),
        ("state", "state"),
        ("late_minutes", "late_minutes"),
        ("late_minutes_actual", "late_minutes_actual"),
        ("penalty_amount", "penalty_amount"),
    ]
    
    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.hr.attendance.late")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        match_fields = ['employee_id', 'date',]
        filters = []

        filters = ast.literal_eval(self.backend_record.external_domain_filter_hr_attendance)
        for match_field in match_fields:
            if record[match_field]:
                if match_field in ['date']:
                    filters.append((match_field, "=", str(record[match_field].strftime("%Y-%m-%d %H:%M:%S")) ))
                if match_field in ['employee_id']:
                    filters.append((match_field, "=", record[match_field].id))

        attendance_ids = self.env["hr.attendance.late"].search(filters, limit=1)
        if attendance_ids:
            return {"odoo_id": attendance_ids[0].id}
        return {}
    
    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}
    
    @mapping
    def attendance_id(self, record):
        if record.attendance_id:
            binder = self.binder_for("odoo.hr.attendance")
            attendance_id = binder.to_internal(record.attendance_id.id, unwrap=True)
            return {"attendance_id": attendance_id.id}
        


class HrAttendanceLateImporter(Component):
    _name = "odoo.hr.attendance.late.importer"
    _inherit = "odoo.importer"
    _inherits = "AbstractModel"
    _apply_on = ["odoo.hr.attendance.late"]
    
    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        
        if self.odoo_record.employee_id:
            _logger.info("Importing employee_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.employee_id.id, "odoo.hr.employee", force=force
            )
        
        if self.odoo_record.attendance_id:
            _logger.info("Importing attendance_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.attendance_id.id, "odoo.hr.attendance", force=force
            )
