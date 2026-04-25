# Copyright 2017 Florent THOMAS (Mind And Go), Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Connector Odoo - HR",
    "summary": """
        Connector Module for Odoo To Odoo scenarios for HR""",
    "version": "19.0.1.0.0",
    "website": "https://github.com/OCA/connector-odoo2odoo",
    "category": "Connector",
    "license": "AGPL-3",
    "author": "Tech Ops PH, EL Abquina",
    "application": False,
    "installable": True,
    "depends": [
        "connector_odoo",
        "hr_attendance",
        "hr_attendance_late",
        "hr_holidays",
        "hr_expense",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/odoo_backend.xml",
        "views/odoo_connector_menus.xml",
        "views/hr_attendance.xml",
        "views/hr_employee_category.xml",
        "views/hr_employee.xml",
        "views/hr_expense.xml",
        "views/hr_job.xml",
        "views/hr_leave.xml",
    ],
    "demo": [],
}
