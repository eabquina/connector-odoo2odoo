import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class HrExpenseSheetBatchImporter(Component):
    """Import the Odoo HR Expense Sheet model.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.expense.sheet.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.expense.sheet"]


class HrExpenseSheetImportMapper(Component):
    _name = "odoo.hr.expense.sheet.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.expense.sheet"]

    direct = [
        ("name", "name"),
        ("approval_state", "approval_state"),
        ("activity_summary", "activity_summary"),
    ]
    
    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.hr.expense.sheet")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        match_fields = ['employee_id', 'create_date', 'name']
        filters = []

        filters = ast.literal_eval(self.backend_record.external_domain_filter_hr_expense_sheet)
        for match_field in match_fields:
            if record[match_field]:
                if match_field in ['create_date']:
                    filters.append((match_field, "=", str(record[match_field].strftime("%Y-%m-%d %H:%M:%S")) ))
                if match_field in ['employee_id']:
                    filters.append((match_field, "=", record[match_field].id))
                if match_field in ['name']:
                    filters.append((match_field, "=", record[match_field]))

        hr_expense_sheets = self.env["hr.expense.sheet"].search(filters, limit=1)
        if hr_expense_sheets:
            return {"odoo_id": hr_expense_sheets[0].id}
        return {}
    
    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}
        
#    @mapping
#    def expense_line_ids(self, record):
#        print("HELLO EXPENSE")
#        if record.expense_line_ids:
#            binder = self.binder_for("odoo.hr.expense")
#            expense_line_ids = binder.to_internal(record.expense_line_ids.id, unwrap=True)
#            print(expense_line_ids)
#            return {"expense_line_ids": expense_line_ids}
        


class HrExpenseSheetImporter(Component):
    _name = "odoo.hr.expense.sheet.importer"
    _inherit = "odoo.importer"
    _inherits = "AbstractModel"
    _apply_on = ["odoo.hr.expense.sheet"]
    
    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        
        if self.odoo_record.employee_id:
            _logger.info("Importing employee_id for Expense Report %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.employee_id.id, "odoo.hr.employee", force=force
            )