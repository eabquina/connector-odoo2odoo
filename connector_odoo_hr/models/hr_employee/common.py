
import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooEmployee(models.Model):
    _name = "odoo.hr.employee"
    _inherit = "odoo.binding"
    _inherits = {"hr.employee": "odoo_id"}
    _description = "External Odoo Employee"

    odoo_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee", required=True, ondelete="cascade"
    )
    
    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]


    def name_get(self):
        result = []
        for op in self:
            name = "{} (Backend: {})".format(
                op.odoo_id.display_name, op.backend_id.display_name
            )
            result.append((op.id, name))

        return result

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class Employee(models.Model):
    _inherit = "hr.employee"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.employee",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class EmployeeAdapter(Component):
    _name = "odoo.hr.employee.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.employee"

    _odoo_model = "hr.employee"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        """Search records according to some criteria
        and returns a list of ids

        :rtype: list
        """
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_partner_domain_filter)
        )
        filters += ext_filter or []
        return super(EmployeeAdapter, self).search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class EmployeeListener(Component):
    _name = "hr.employee.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["hr.employee"]
    _usage = "event.listener"
