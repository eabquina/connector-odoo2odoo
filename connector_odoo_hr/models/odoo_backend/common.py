
import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooBackend(models.Model):
    _inherit = "odoo.backend"
    

    """
    EMPLOYEE SYNC OPTIONS
    hr.employee
    hr.employee.category
    hr.job
    hr.attendance
    """

    default_export_employee = fields.Boolean("Export Employee")
    default_import_employee = fields.Boolean("Import Employee")
    local_domain_filter_employee = fields.Char(default="[]")
    external_domain_filter_employee = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )

    default_export_hr_employee_category = fields.Boolean("Export Employee Category")
    default_import_hr_employee_category = fields.Boolean("Import Employee Category")
    local_domain_filter_hr_employee_category = fields.Char(default="[]")
    external_domain_filter_hr_employee_category = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )

    default_export_hr_job = fields.Boolean("Export Job Positions")
    default_import_hr_job = fields.Boolean("Import Job Positions")
    local_domain_filter_hr_job = fields.Char(default="[]")
    external_domain_filter_hr_job = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )
    
    default_export_hr_attendance = fields.Boolean("Export Attendances")
    default_import_hr_attendance = fields.Boolean("Import Attendances")
    local_domain_filter_hr_attendance = fields.Char(default="[]")
    external_domain_filter_hr_attendance = fields.Char(
        default="[]",
        help="""Filter in the Odoo Destination
        """,
    )

    import_from_date_employee = fields.Datetime("Import Employee From Date")

    def import_employee(self):
        if not self.default_import_employee:
            return False
        self._import_from_date("odoo.hr.employee", "import_from_date_employee")
        return True
    
    def import_hr_employee_category(self):
        if not self.default_import_hr_employee_category:
            return False
        self._import_from_date("odoo.hr.employee.category", "import_from_date_employee")
        return True
    
    def import_hr_job(self):
        if not self.default_import_hr_job:
            return False
        self._import_from_date("odoo.hr.job", "import_from_date_employee")
        return True
    
    def import_hr_attendance(self):
        if not self.default_import_hr_attendance:
            return False
        self._import_from_date("odoo.hr.attendance", "import_from_date_employee")
        return True