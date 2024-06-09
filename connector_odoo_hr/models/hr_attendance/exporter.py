# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from datetime import datetime

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class BatchHrAttendanceExporter(Component):
    _name = "odoo.hr.attendance.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.hr.attendance"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        loc_filter = ast.literal_eval(self.backend_record.local_domain_filter_hr_attendance)
        filters += loc_filter
        attendance_ids = self.env["hr.attendance"].search(filters)

        o_ids = self.env["odoo.hr.attendance"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        o_attendance_ids = self.env["hr.attendance"].search(
            [("id", "in", [o.odoo_id.id for o in o_ids])]
        )
        to_bind = attendance_ids - o_attendance_ids

        for p in to_bind:
            self.env["odoo.hr.attendance"].create(
                {
                    "odoo_id": p.id,
                    "external_id": p.id,
                    "backend_id": self.backend_record.id,
                }
            )

        bind_ids = self.env["odoo.hr.attendance"].search(
            [
                ("odoo_id", "in", [p.id for p in attendance_ids]),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        for hr_attendance in bind_ids:
            job_options = {"max_retries": 0, "priority": 15}
            self._export_record(hr_attendance, job_options=job_options)


class OdooHrAttendanceExporter(Component):
    _name = "odoo.hr.attendance.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.hr.attendance"]

    def _export_dependencies(self):
        if not self.binding.employee_id:
            return
        parents = self.binding.employee_id.bind_ids
        parent = self.env["odoo.hr.attendance"]

        if parents:
            parent = parents.filtered(lambda c: c.backend_id == self.backend_record)

            hr_attendance = self.binder.to_external(parent, wrap=False)
            self._export_dependency(hr_attendance, "odoo.hr.attendance")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = map_record.values(for_create=True, fields=fields, **kwargs)
        return datas


class HrAttendanceExportMapper(Component):
    _name = "odoo.hr.attendance.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.hr.attendance"]

    direct = [
        #("check_in", "check_in"),
        #("check_out", "check_out"),
        #("create_date", "create_date"),
        #("write_date", "write_date"),
        ("color", "color"),        
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
        
    ]

    def get_hr_attendance_by_match_field(self, record):
        match_fields = ['employee_id', 'check_in', 'check_out']
        filters = []

        filters = ast.literal_eval(self.backend_record.external_domain_filter_hr_attendance)
        for match_field in match_fields:
            if record[match_field]:
                if match_field in ['check_in', 'check_out']:
                    filters.append((match_field, "=", str(record[match_field].strftime("%Y-%m-%d %H:%M:%S")) ))
                if match_field in ['employee_id']:
                    filters.append((match_field, "=", record[match_field].id))
        adapter = self.component(usage="record.exporter").backend_adapter
        hr_attendance = adapter.search(filters)
        if len(hr_attendance) > 0:
            return hr_attendance[0]
        else:
            return False

    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.attendance")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}
    
    @mapping
    def check_in(self, record):
        return {"check_in": record.check_in.strftime("%Y-%m-%d %H:%M:%S")}
    
    @mapping
    def check_out(self, record):
        return {"check_out": record.check_out.strftime("%Y-%m-%d %H:%M:%S")}


    @only_create
    @mapping
    def odoo_id(self, record):
        external_id = self.get_hr_attendance_by_match_field(record)

        if external_id:
            return {"external_id": external_id}
