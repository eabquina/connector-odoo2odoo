
import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class BatchEmployeeExporter(Component):
    _name = "odoo.hr.employee.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.hr.employee"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        loc_filter = ast.literal_eval(self.backend_record.local_employee_domain_filter)
        filters += loc_filter
        employee_ids = self.env["hr.employee"].search(filters)

        o_ids = self.env["odoo.hr.employee"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        o_employee_ids = self.env["hr.employee"].search(
            [("id", "in", [o.odoo_id.id for o in o_ids])]
        )
        to_bind = employee_ids - o_employee_ids

        for p in to_bind:
            self.env["odoo.hr.employee"].create(
                {
                    "odoo_id": p.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )

        bind_ids = self.env["odoo.hr.employee"].search(
            [
                ("odoo_id", "in", [p.id for p in employee_ids]),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        for employee in bind_ids:
            job_options = {"max_retries": 0, "priority": 15}
            self._export_record(employee, job_options=job_options)


class OdooEmployeeExporter(Component):
    _name = "odoo.hr.employee.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.hr.employee"]

    def _export_dependencies(self):
        if not self.binding.parent_id:
            return
        parents = self.binding.parent_id.bind_ids
        parent = self.env["odoo.hr.employee"]

        if parents:
            parent = parents.filtered(lambda c: c.backend_id == self.backend_record)

            employee = self.binder.to_external(parent, wrap=False)
            self._export_dependency(employee, "odoo.hr.employee")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = map_record.values(for_create=True, fields=fields, **kwargs)
        return datas


class EmployeeExportMapper(Component):
    _name = "odoo.hr.employee.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.hr.employee"]

    direct = [
        ("name", "name"),
        ("street", "street"),
        ("street2", "street2"),
        ("city", "city"),
        ("website", "website"),
        ("phone", "phone"),
        ("mobile", "mobile"),
        ("email", "email"),
    ]

    def get_employee_by_match_field(self, record):
        match_field = "email"
        filters = []

        if self.backend_record.matching_customer:
            match_field = self.backend_record.matching_customer_ch

        filters = ast.literal_eval(self.backend_record.external_employee_domain_filter)
        if record[match_field]:
            filters.append((match_field, "=", record[match_field]))
        filters.append("|")
        filters.append(("active", "=", False))
        filters.append(("active", "=", True))

        adapter = self.component(usage="record.exporter").backend_adapter
        employee = adapter.search(filters)
        if len(employee) == 1:
            return employee[0]

        return False

    @mapping
    def customer(self, record):
        return {"customer": True}

    @mapping
    def supplier(self, record):
        return {"supplier": True}

    @only_create
    @mapping
    def odoo_id(self, record):
        external_id = self.get_employee_by_match_field(record)

        if external_id:
            return {"external_id": external_id}
