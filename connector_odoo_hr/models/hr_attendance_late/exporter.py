# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class BatchHrAttendanceExporter(Component):
    _name = "odoo.hr.attendance.late.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.hr.attendance.late"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        loc_filter = ast.literal_eval(self.backend_record.local_domain_filter_hr_attendance)
        filters += loc_filter
        employee_ids = self.env["hr.attendance.late"].search(filters)

        o_ids = self.env["odoo.hr.attendance.late"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        o_employee_ids = self.env["hr.attendance.late"].search(
            [("id", "in", [o.odoo_id.id for o in o_ids])]
        )
        to_bind = employee_ids - o_employee_ids

        for p in to_bind:
            self.env["odoo.hr.attendance.late"].create(
                {
                    "odoo_id": p.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )

        bind_ids = self.env["odoo.hr.attendance.late"].search(
            [
                ("odoo_id", "in", [p.id for p in employee_ids]),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        for hr_attendance in bind_ids:
            job_options = {"max_retries": 0, "priority": 15}
            self._export_record(hr_attendance, job_options=job_options)


class OdooHrAttendanceExporter(Component):
    _name = "odoo.hr.attendance.late.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.hr.attendance.late"]

    def _export_dependencies(self):
        if not self.binding.parent_id:
            return
        parents = self.binding.parent_id.bind_ids
        parent = self.env["odoo.hr.attendance.late"]

        if parents:
            parent = parents.filtered(lambda c: c.backend_id == self.backend_record)

            hr_attendance = self.binder.to_external(parent, wrap=False)
            self._export_dependency(hr_attendance, "odoo.hr.attendance.late")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = map_record.values(for_create=True, fields=fields, **kwargs)
        return datas


class HrAttendanceExportMapper(Component):
    _name = "odoo.hr.attendance.late.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.hr.attendance.late"]

    direct = [
        ("date", "date"),
        ("name", "name"),
        ("display_name", "display_name"),
        ("state", "state"),
        ("late_minutes", "late_minutes"),
        ("late_minutes_actual", "late_minutes_actual"),
        ("penalty_amount", "penalty_amount"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.hr.attendance.late")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        match_fields = ['employee_id', 'date',]
        filters = []

        filters = ast.literal_eval(self.backend_record.external_domain_filter_hr_attendance)
        for match_field in match_fields:
            if record[match_field]:
                if match_field in ['date']:
                    filters.append((match_field, "=", str(record[match_field].strftime("%Y-%m-%d %H:%M:%S")) ))
                if match_field in ['employee_id']:
                    filters.append((match_field, "=", record[match_field].id))

        attendance_ids = self.env["hr.attendance.late"].search(filters, limit=1)
        if attendance_ids:
            return {"odoo_id": attendance_ids[0].id}
        return {}
    
    @mapping
    def employee_id(self, record):
        if record.employee_id:
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}
    
    @mapping
    def attendance_id(self, record):
        if record.attendance_id:
            binder = self.binder_for("odoo.hr.attendance")
            attendance_id = binder.to_internal(record.attendance_id.id, unwrap=True)
            return {"attendance_id": attendance_id.id}
