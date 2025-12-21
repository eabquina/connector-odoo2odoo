
import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooBackend(models.Model):
    _inherit = "odoo.backend"
    

    """
    EMPLOYEE SYNC OPTIONS
    hr.attendance.late
    hr.overtime
    """
    
    
    import_from_date_hr_overtime = fields.Datetime("Import HR Overtime From Date")
    export_from_date_hr_overtime = fields.Datetime("Export HR Overtime From Date")
    default_export_hr_overtime = fields.Boolean("Export HR Overtime")
    default_import_hr_overtime = fields.Boolean("Import HR Overtime")
    local_domain_filter_hr_overtime = fields.Char(default="[]")
    external_domain_filter_hr_overtime = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )
    
    import_from_date_hr_attendance_late = fields.Datetime("Import HR Attendance Late From Date")
    export_from_date_hr_attendance_late = fields.Datetime("Export HR Attendance Late From Date")
    default_export_hr_attendance_late = fields.Boolean("Export HR Attendance Late")
    default_import_hr_attendance_late = fields.Boolean("Import HR Attendance Late")
    local_domain_filter_hr_attendance_late = fields.Char(default="[]")
    external_domain_filter_hr_attendance_late = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )

    
    
    

    
    """
        Import Actions
    """

    def import_hr_overtime(self):
        if not self.default_import_hr_overtime:
            return False
        self._import_from_date("odoo.hr.overtime", "import_from_date_hr_overtime")
        return True
    
    def import_hr_attendance_late(self):
        if not self.default_import_hr_attendance_late:
            return False
        self._import_from_date("odoo.hr.attendance.late", "import_from_date_hr_attendance_late")
        return True
    
    
    
    """
        Export Actions
    """
    
    def export_hr_overtime(self):
        if not self.default_export_hr_overtime:
            return False
        self._export_from_date("odoo.hr.overtime", "export_from_date_hr_overtime")
        return True
    
    def export_hr_attendance_late(self):
        if not self.default_export_hr_attendance_late:
            return False
        self._export_from_date("odoo.hr.attendance.late", "export_from_date_hr_attendance_late")
        return True
