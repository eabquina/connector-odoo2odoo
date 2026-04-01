# Copyright 2017 Florent THOMAS (Mind And Go), Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Connector Odoo - Payroll PH",
    "summary": """
        Connector Module for Odoo To Odoo scenarios for Payroll PH""",
    "version": "17.0.1.0.0",
    "website": "https://github.com/OCA/connector-odoo2odoo",
    "category": "Connector",
    "license": "AGPL-3",
    "author": "Tech Ops PH, EL Abquina",
    "application": False,
    "installable": True,
    "depends": [
        "working_schedule_adv",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/odoo_backend.xml",
        "views/odoo_connector_menus.xml",
        "views/resource_calendar_change_type.xml",
        "views/resource_calendar_change.xml",
        "views/resource_calendar_change_lines.xml",
    ],
    "demo": [],
    "qweb": [],
}
