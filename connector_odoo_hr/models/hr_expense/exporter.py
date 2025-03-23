# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class BatchHrExpenseExporter(Component):
    _name = "odoo.hr.expense.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.hr.expense"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        loc_filter = ast.literal_eval(self.backend_record.local_domain_filter_hr_expense)
        filters += loc_filter
        employee_ids = self.env["hr.expense"].search(filters)

        o_ids = self.env["odoo.hr.expense"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        o_employee_ids = self.env["hr.expense"].search(
            [("id", "in", [o.odoo_id.id for o in o_ids])]
        )
        to_bind = employee_ids - o_employee_ids

        for p in to_bind:
            self.env["odoo.hr.expense"].create(
                {
                    "odoo_id": p.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )

        bind_ids = self.env["odoo.hr.expense"].search(
            [
                ("odoo_id", "in", [p.id for p in employee_ids]),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        for hr_expense in bind_ids:
            job_options = {"max_retries": 0, "priority": 15}
            self._export_record(hr_expense, job_options=job_options)


class OdooHrAttendanceExporter(Component):
    _name = "odoo.hr.expense.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.hr.expense"]

    def _export_dependencies(self):
        if not self.binding.parent_id:
            return
        parents = self.binding.parent_id.bind_ids
        parent = self.env["odoo.hr.expense"]

        if parents:
            parent = parents.filtered(lambda c: c.backend_id == self.backend_record)

            hr_expense = self.binder.to_external(parent, wrap=False)
            self._export_dependency(hr_expense, "odoo.hr.expense")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = map_record.values(for_create=True, fields=fields, **kwargs)
        return datas


class HrAttendanceExportMapper(Component):
    _name = "odoo.hr.expense.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.hr.expense"]

    direct = [
        ("date", "date"),
        ("name", "name"),
        ("employee_id", "employee_id"),
        ("product_id", "product_id"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.hr.expense")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        match_fields = ['employee_id', 'date',]
        filters = []

        filters = ast.literal_eval(self.backend_record.external_domain_filter_hr_expense)
        for match_field in match_fields:
            if record[match_field]:
                if match_field in ['date']:
                    filters.append((match_field, "=", str(record[match_field].strftime("%Y-%m-%d %H:%M:%S")) ))
                if match_field in ['employee_id']:
                    filters.append((match_field, "=", record[match_field].id))

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
        if record.product_id:
            binder = self.binder_for("odoo.product.product")
            product_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"product_id": product_id.id}