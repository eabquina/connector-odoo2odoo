import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class HrAttendanceBatchImporter(Component):
    """Import the Odoo HR HrAttendance model.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.attendance.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.attendance"]


class HrAttendanceImportMapper(Component):
    _name = "odoo.hr.attendance.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.attendance"]

    direct = [
        ("check_in", "check_in"),
        ("check_out", "check_out"),
        ("color", "color"),        
        ("create_date", "create_date"),
        ("display_name", "display_name"),
        ("in_browser", "in_browser"),
        ("in_city", "in_city"),
        ("in_country_name", "in_country_name"),
        ("in_ip_address", "in_ip_address"),
        ("in_latitude", "in_latitude"),
        ("in_longitude", "in_longitude"),
        ("out_mode", "out_mode"),
        ("out_browser", "out_browser"),
        ("out_city", "out_city"),
        ("out_country_name", "out_country_name"),
        ("out_ip_address", "out_ip_address"),
        ("out_latitude", "out_latitude"),
        ("out_longitude", "out_longitude"),
        ("out_mode", "out_mode"),
        ("worked_hours", "worked_hours"),
        ("write_date", "write_date")
    ]
    
    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.hr.attendance")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        match_fields = ['employee_id', 'check_in', 'check_out']
        filters = []

        filters = ast.literal_eval(self.backend_record.external_domain_filter_hr_attendance)
        for match_field in match_fields:
            if record[match_field]:
                if match_field in ['check_in', 'check_out']:
                    filters.append((match_field, "=", str(record[match_field].strftime("%Y-%m-%d %H:%M:%S")) ))
                if match_field in ['employee_id']:
                    filters.append((match_field, "=", record[match_field].id))

        attendance_ids = self.env["hr.attendance"].search(filters, limit=1)
        if attendance_ids:
            return {"odoo_id": attendance_ids[0].id}
        return {}
    
    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}
        


class HrAttendanceImporter(Component):
    _name = "odoo.hr.attendance.importer"
    _inherit = "odoo.importer"
    _inherits = "AbstractModel"
    _apply_on = ["odoo.hr.attendance"]
    
    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        
        if self.odoo_record.employee_id:
            _logger.info("Importing employee_id for attendance %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.employee_id.id, "odoo.hr.employee", force=force
            )
