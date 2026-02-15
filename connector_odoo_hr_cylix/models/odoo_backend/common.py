
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
    WORKING SCHEDULE - ADVANCED
    resource.calendar.change.type
    resource.calendar.change
    resource.calendar.change.lines
    """

    import_from_date_resource_calendar_change_type = fields.Datetime(
        "Import Work Schedule Change Types From Date"
    )
    export_from_date_resource_calendar_change_type = fields.Datetime(
        "Export Work Schedule Change Types From Date"
    )
    default_export_resource_calendar_change_type = fields.Boolean(
        "Export Work Schedule Change Types"
    )
    default_import_resource_calendar_change_type = fields.Boolean(
        "Import Work Schedule Change Types"
    )
    local_domain_filter_resource_calendar_change_type = fields.Char(default="[]")
    external_domain_filter_resource_calendar_change_type = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination""",
    )

    import_from_date_resource_calendar_change = fields.Datetime(
        "Import Work Schedule Change Requests From Date"
    )
    export_from_date_resource_calendar_change = fields.Datetime(
        "Export Work Schedule Change Requests From Date"
    )
    default_export_resource_calendar_change = fields.Boolean(
        "Export Work Schedule Change Requests"
    )
    default_import_resource_calendar_change = fields.Boolean(
        "Import Work Schedule Change Requests"
    )
    local_domain_filter_resource_calendar_change = fields.Char(default="[]")
    external_domain_filter_resource_calendar_change = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination""",
    )

    import_from_date_resource_calendar_change_lines = fields.Datetime(
        "Import Work Schedule Change Lines From Date"
    )
    export_from_date_resource_calendar_change_lines = fields.Datetime(
        "Export Work Schedule Change Lines From Date"
    )
    default_export_resource_calendar_change_lines = fields.Boolean(
        "Export Work Schedule Change Lines"
    )
    default_import_resource_calendar_change_lines = fields.Boolean(
        "Import Work Schedule Change Lines"
    )
    local_domain_filter_resource_calendar_change_lines = fields.Char(default="[]")
    external_domain_filter_resource_calendar_change_lines = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination""",
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

    def import_resource_calendar_change_type(self):
        if not self.default_import_resource_calendar_change_type:
            return False
        self._import_from_date(
            "odoo.resource.calendar.change.type",
            "import_from_date_resource_calendar_change_type",
        )
        return True

    def import_resource_calendar_change(self):
        if not self.default_import_resource_calendar_change:
            return False
        self._import_from_date(
            "odoo.resource.calendar.change",
            "import_from_date_resource_calendar_change",
        )
        return True

    def import_resource_calendar_change_lines(self):
        if not self.default_import_resource_calendar_change_lines:
            return False
        self._import_from_date(
            "odoo.resource.calendar.change.lines",
            "import_from_date_resource_calendar_change_lines",
        )
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

    def export_resource_calendar_change_type(self):
        if not self.default_export_resource_calendar_change_type:
            return False
        self._export_from_date(
            "odoo.resource.calendar.change.type",
            "export_from_date_resource_calendar_change_type",
        )
        return True

    def export_resource_calendar_change(self):
        if not self.default_export_resource_calendar_change:
            return False
        self._export_from_date(
            "odoo.resource.calendar.change",
            "export_from_date_resource_calendar_change",
        )
        return True

    def export_resource_calendar_change_lines(self):
        if not self.default_export_resource_calendar_change_lines:
            return False
        self._export_from_date(
            "odoo.resource.calendar.change.lines",
            "export_from_date_resource_calendar_change_lines",
        )
        return True
