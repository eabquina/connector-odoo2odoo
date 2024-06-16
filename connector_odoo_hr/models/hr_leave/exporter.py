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
        loc_filter = ast.literal_eval(self.backend_record.local_domain_filter_hr_leave)
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
        ("active_employee", "active_employee"),
        ("activity_date_deadline", "activity_date_deadline"),
        ("activity_exception_decoration", "activity_exception_decoration"),
        ("activity_exception_icon", "activity_exception_icon"),
        ("activity_state", "activity_state"),
        ("activity_summary", "activity_summary"),
        ("activity_type_icon", "activity_type_icon"),
        ("can_approve", "can_approve"),
        ("can_cancel", "can_cancel"),
        ("can_reset", "can_reset"),
        ("color", "color"),
        ("date_from", "date_from"),
        ("date_to", "date_to"),
        ("display_name", "display_name"),
        ("duration_display", "duration_display"),
        ("has_mandatory_day", "has_mandatory_day"),
        ("has_message", "has_message"),
        ("holiday_type", "holiday_type"),
        ("is_hatched", "is_hatched"),
        ("is_striked", "is_striked"),
        ("is_user_only_responsible", "is_user_only_responsible"),
        ("last_several_days", "last_several_days"),
        ("leave_type_increases_duration", "leave_type_increases_duration"),
        ("leave_type_request_unit", "leave_type_request_unit"),
        ("leave_type_support_document", "leave_type_support_document"),
        ("multi_employee", "multi_employee"),
        ("name", "name"),
        ("notes", "notes"),
        ("number_of_days", "number_of_days"),
        ("number_of_days_display", "number_of_days_display"),
        ("number_of_hours", "number_of_hours"),
        ("number_of_hours_display", "number_of_hours_display"),
        ("number_of_hours_text", "number_of_hours_text"),
        ("private_name", "private_name"),
        ("report_note", "report_note"),
        ("request_date_from", "request_date_from"),
        ("request_date_from_period", "request_date_from_period"),
        ("request_date_to", "request_date_to"),
        ("request_hour_from", "request_hour_from"),
        ("request_hour_to", "request_hour_to"),
        ("request_unit_half", "request_unit_half"),
        ("request_unit_hours", "request_unit_hours"),
        ("supported_attachment_ids_count", "supported_attachment_ids_count"),
        ("tz", "tz"),
        ("tz_mismatch", "tz_mismatch"),
        ("validation_type", "validation_type"),
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
