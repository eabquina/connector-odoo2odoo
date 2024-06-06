import logging

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class EmployeeCategoryBatchImporter(Component):
    """Import the Odoo Partner Category.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.employee.category.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.employee.category"]


class EmployeeCategoryImportMapper(Component):
    _name = "odoo.hr.employee.category.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.employee.category"]

    direct = [
        ("name", "name"), 
        ("color", "color"),
        ("display_name", "display_name"),
        ]


class EmployeeCategoryImporter(Component):
    _name = "odoo.hr.employee.category.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.employee.category"]
 
    def _before_import(self,):
        
        category_id = self.env["hr.employee.category"].search(
            [("name", "=", self.odoo_record.name)]
        )
        if not category_id:
            original_category_id = self.env["hr.employee.category"].search(
                [("name", "=", self.odoo_record.name)]
            )
            if not original_category_id:
                raise ValidationError(
                    _("Employee Category %s not found") % self.odoo_record.name
                )
            else:
                self.work.origing_account_id = original_category_id
