# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class BatchHrHrOvertimeExporter(Component):
    _name = "odoo.hr.overtime.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.hr.overtime"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        loc_filter = ast.literal_eval(self.backend_record.local_domain_filter_hr_leave)
        filters += loc_filter
        employee_ids = self.env["hr.overtime"].search(filters)

        o_ids = self.env["odoo.hr.overtime"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        o_employee_ids = self.env["hr.overtime"].search(
            [("id", "in", [o.odoo_id.id for o in o_ids])]
        )
        to_bind = employee_ids - o_employee_ids

        for p in to_bind:
            self.env["odoo.hr.overtime"].create(
                {
                    "odoo_id": p.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )

        bind_ids = self.env["odoo.hr.overtime"].search(
            [
                ("odoo_id", "in", [p.id for p in employee_ids]),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        for hr_attendance in bind_ids:
            job_options = {"max_retries": 0, "priority": 15}
            self._export_record(hr_attendance, job_options=job_options)


class OdooHrHrOvertimeExporter(Component):
    _name = "odoo.hr.overtime.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.hr.overtime"]

    def _export_dependencies(self):
        if not self.binding.parent_id:
            return
        parents = self.binding.parent_id.bind_ids
        parent = self.env["odoo.hr.overtime"]

        if parents:
            parent = parents.filtered(lambda c: c.backend_id == self.backend_record)

            hr_attendance = self.binder.to_external(parent, wrap=False)
            self._export_dependency(hr_attendance, "odoo.hr.overtime")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = map_record.values(for_create=True, fields=fields, **kwargs)
        return datas


class HrHrOvertimeExportMapper(Component):
    _name = "odoo.hr.overtime.export.mapper"
    _inherit = "odoo.export.mapper"
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
            binder = self.binder_for("odoo.hr.employee")
            employee_id = binder.to_internal(record.employee_id.id, unwrap=True)
            return {"employee_id": employee_id.id}

    @only_create
    @mapping
    def odoo_id(self, record):
        external_id = self.get_hr_attendance_by_match_field(record)

        if external_id:
            return {"external_id": external_id}
