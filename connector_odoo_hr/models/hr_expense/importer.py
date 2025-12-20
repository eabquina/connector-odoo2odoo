import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class HrExpenseBatchImporter(Component):
    """Import the Odoo HR Attendance model.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.expense.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.expense"]


class HrExpenseImportMapper(Component):
    _name = "odoo.hr.expense.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.expense"]

    direct = [
        ("date", "date"),
        ("create_date", "create_date"),
        ("name", "name"),
        ("product_description", "product_description"),
        ("product_has_cost", "product_has_cost"),
        ("product_has_tax", "product_has_tax"),
        ("quantity", "quantity"),
        ("description", "description"),
        ("state", "state"),
        ("approved_on", "approved_on"),
        ("tax_amount_currency", "tax_amount_currency"),
        ("tax_amount", "tax_amount"),
        ("total_amount_currency", "total_amount_currency"),
        ("untaxed_amount_currency", "untaxed_amount_currency"),
        ("total_amount", "total_amount"),
        ("price_unit", "price_unit"),
        ("payment_mode", "payment_mode"),
        ("accounting_date", "accounting_date"),
        ("is_editable", "is_editable"),
    ]
    
    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.hr.expense")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        match_fields = ['employee_id', 'date', 'create_date', 'name', 'product_id']
        filters = []

        filters = ast.literal_eval(self.backend_record.external_domain_filter_hr_expense)
        for match_field in match_fields:
            if record[match_field]:
                if match_field in ['date']:
                    filters.append((match_field, "=", str(record[match_field].strftime("%Y-%m-%d %H:%M:%S")) ))
                if match_field in ['employee_id']:
                    filters.append((match_field, "=", record[match_field].id))
                if match_field in ['name']:
                    filters.append((match_field, "=", record[match_field]))
                if match_field in ['product_id']:
                    filters.append((match_field, "=", record[match_field].id))
                if match_field in ['create_date']:
                    filters.append((match_field, "=", str(record[match_field].strftime("%Y-%m-%d %H:%M:%S")) ))

        hr_expenses = self.env["hr.expense"].search(filters, limit=1)
        if hr_expenses:
            return {"odoo_id": hr_expenses[0].id}
        return {}
    
    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}
    
    @mapping
    def product_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.product.product")
            product_id = binder.to_internal(record.product_id.id, unwrap=True)
            return {"product_id": product_id.id}

    @mapping
    def sheet_id(self, record):
        if record.sheet_id:
            binder = self.binder_for("odoo.hr.expense.sheet")
            sheet_id = binder.to_internal(record.sheet_id.id, unwrap=True)
            return {"sheet_id": sheet_id.id}

class HrExpenseImporter(Component):
    _name = "odoo.hr.expense.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.expense"]
    
    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        
        if self.odoo_record.employee_id:
            _logger.info("Importing employee_id for expense %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.employee_id.id, "odoo.hr.employee", force=force
            )
            
        if self.odoo_record.product_id:
            _logger.info("Importing product_id for expense %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.product_id.id, "odoo.product.product", force=force
            )
            
        if self.odoo_record.sheet_id:
            _logger.info("Importing sheet_id for expense %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.sheet_id.id, "odoo.hr.expense.sheet", force=force
            )
        