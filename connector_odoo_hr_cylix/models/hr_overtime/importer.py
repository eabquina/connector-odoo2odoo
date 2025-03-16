import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class HrOvertimeBatchImporter(Component):
    """Import the Odoo HR HrOvertime model.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.overtime.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.overtime"]


class HrOvertimeImportMapper(Component):
    _name = "odoo.hr.overtime.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.overtime"]

    direct = [
        ("name", "name"),
        ("date_from", "date_from"),
        ("date_to", "date_to"),
        ("state", "state"),
        ("type", "type"),
        ("duration_type", "duration_type"),
        ("attchd_copy", "attchd_copy"),
        ("attchd_copy_name", "attchd_copy_name"),
        ("days_no", "days_no"),
        ("desc", "desc"),
        ("cancel_reason", "cancel_reason"),
        ("current_user_boolean", "current_user_boolean"),
        ("display_name", "display_name"),
        ("public_holiday", "public_holiday"),
    ]
    
    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}
    @mapping
    def overtime_type_id(self, record):
        if record.overtime_type_id:
            binder = self.binder_for("odoo.overtime.type")
            overtime_type_id = binder.to_internal(record.overtime_type_id.id, unwrap=True)
            return {"overtime_type_id": overtime_type_id.id}        


class HrOvertimeImporter(Component):
    _name = "odoo.hr.overtime.importer"
    _inherit = "odoo.importer"
    _inherits = "AbstractModel"
    _apply_on = ["odoo.hr.overtime"]
    
    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        
        if self.odoo_record.employee_id:
            _logger.info("Importing employee_id for leave %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.employee_id.id, "odoo.hr.employee", force=force
            )
        if self.odoo_record.overtime_type_id:
            _logger.info("Importing overtime_type_id for leave %s", self.odoo_record.id)
            self._import_dependency(
                self.odoo_record.overtime_type_id.id, "odoo.overtime.type", force=force
            )
            
    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        
        return res
       