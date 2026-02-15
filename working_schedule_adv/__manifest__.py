# -*- coding: utf-8 -*-
{
    'name': 'Work Schedule - Advanced',
    'category': 'Human Resources',
    'depends': [
        'resource',
        'hr_contract',
    ],
    'version': '17.0',
    'price': '88.00',
    'currency': 'USD',
    'license': 'OPL-1',
    'author': 'Tech Ops PH, EL Abquina',
    'description': """

    Work Schedule Request - Form to Request Schedule Changes and Other Integrations
========================
    """,
    'data': [
        "security/ir.model.access.csv",
        "security/resource_calendar_change.xml",
        "data/resource_calendar_change_type.xml",
        "data/resource_calendar_change.xml",
        "views/resource_calendar_change_lines.xml",
        "views/resource_calendar_change.xml",
        "views/resource_calendar.xml",
    ],
    'license': 'LGPL-3',
}
