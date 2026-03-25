# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Connector Odoo - Helpdesk",
    "summary": """
        Connector Module for syncing OCA Helpdesk records from Odoo 13 to Odoo 18""",
    "version": "18.0.1.0.0",
    "website": "https://github.com/OCA/connector-odoo2odoo",
    "category": "Connector",
    "license": "AGPL-3",
    "author": "Pantheon, EL Abquina",
    "application": False,
    "installable": True,
    "depends": [
        "connector_odoo",
        "helpdesk_mgmt",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/odoo_backend.xml",
    ],
    "demo": [],
}
