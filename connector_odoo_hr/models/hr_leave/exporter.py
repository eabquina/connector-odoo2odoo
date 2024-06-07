# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class BatchHrHrLeaveExporter(Component):
    _name = "odoo.hr.leave.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.hr.leave"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        loc_filter = ast.literal_eval(self.backend_record.local_hr_attendance_domain_filter)
        filters += loc_filter
        employee_ids = self.env["hr.leave"].search(filters)

        o_ids = self.env["odoo.hr.leave"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        o_employee_ids = self.env["hr.leave"].search(
            [("id", "in", [o.odoo_id.id for o in o_ids])]
        )
        to_bind = employee_ids - o_employee_ids

        for p in to_bind:
            self.env["odoo.hr.leave"].create(
                {
                    "odoo_id": p.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )

        bind_ids = self.env["odoo.hr.leave"].search(
            [
                ("odoo_id", "in", [p.id for p in employee_ids]),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        for hr_attendance in bind_ids:
            job_options = {"max_retries": 0, "priority": 15}
            self._export_record(hr_attendance, job_options=job_options)


class OdooHrHrLeaveExporter(Component):
    _name = "odoo.hr.leave.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.hr.leave"]

    def _export_dependencies(self):
        if not self.binding.parent_id:
            return
        parents = self.binding.parent_id.bind_ids
        parent = self.env["odoo.hr.leave"]

        if parents:
            parent = parents.filtered(lambda c: c.backend_id == self.backend_record)

            hr_attendance = self.binder.to_external(parent, wrap=False)
            self._export_dependency(hr_attendance, "odoo.hr.leave")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = map_record.values(for_create=True, fields=fields, **kwargs)
        return datas


class HrHrLeaveExportMapper(Component):
    _name = "odoo.hr.leave.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.hr.leave"]

    direct = [
        ("check_in", "check_in"),
        ("check_out", "check_out"),
        ("color", "color"),        
        ("create_date", "create_date"),
        ("display_name", "display_name"),
        ("in_browser", "in_browser"),
        ("in_city", "in_city"),
        ("in_country_name", "in_country_name"),
        ("in_ip_address", "in_ip_address"),
        ("in_latitude", "in_latitude"),
        ("in_longitude", "in_longitude"),
        ("out_mode", "out_mode"),
        ("out_browser", "out_browser"),
        ("out_city", "out_city"),
        ("out_country_name", "out_country_name"),
        ("out_ip_address", "out_ip_address"),
        ("out_latitude", "out_latitude"),
        ("out_longitude", "out_longitude"),
        ("out_mode", "out_mode"),
        ("worked_hours", "worked_hours"),
        ("write_date", "write_date")
    ]

    def get_hr_attendance_match_field(self, record):
        match_field = "email"
        filters = []

        if self.backend_record.matching_customer:
            match_field = self.backend_record.matching_customer_ch

        filters = ast.literal_eval(self.backend_record.external_hr_attendance_domain_filter)
        if record[match_field]:
            filters.append((match_field, "=", record[match_field]))
        filters.append("|")
        filters.append(("active", "=", False))
        filters.append(("active", "=", True))

        adapter = self.component(usage="record.exporter").backend_adapter
        hr_attendance = adapter.search(filters)
        if len(hr_attendance) == 1:
            return hr_attendance[0]

        return False

    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}

    @only_create
    @mapping
    def odoo_id(self, record):
        external_id = self.get_hr_attendance_by_match_field(record)

        if external_id:
            return {"external_id": external_id}
