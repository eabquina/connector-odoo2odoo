import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class JobPositionBatchImporter(Component):
    """Import the Odoo Department.

    For everyDepartment in the list, a delayed department is created.
    Import from a date
    """

    _name = "odoo.hr.department.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.department"]


class JobPositionImportMapper(Component):
    _name = "odoo.hr.department.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.department"]

    direct = [
        ("name", "name"),
        ("complete_name", "complete_name"),
        ("active", "active"),
        ("parent_id", "parent_id"),
        ("company_id", "company_id"),
    ]


class JobPositionImporter(Component):
    _name = "odoo.hr.department.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.department"]
