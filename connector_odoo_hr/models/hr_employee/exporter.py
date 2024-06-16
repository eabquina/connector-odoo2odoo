
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
        ("active", "active"),
        ("activity_date_deadline", "activity_date_deadline"),
        ("activity_exception_decoration", "activity_exception_decoration"),
        ("activity_exception_icon", "activity_exception_icon"),
        ("activity_state", "activity_state"),
        ("activity_summary", "activity_summary"),
        ("activity_type_icon", "activity_type_icon"),
        ("additional_note", "additional_note"),
        ("avatar_1024", "avatar_1024"),
        ("avatar_128", "avatar_128"),
        ("avatar_1920", "avatar_1920"),
        ("avatar_256", "avatar_256"),
        ("avatar_512", "avatar_512"),
        ("barcode", "barcode"),
        ("birthday", "birthday"),
        ("certificate", "certificate"),
        ("children", "children"),
        ("color", "color"),
        ("company_country_code", "company_country_code"),
        ("create_date", "create_date"),
        ("departure_date", "departure_date"),
        ("departure_description", "departure_description"),
        ("display_name", "display_name"),
        ("driving_license", "driving_license"),
        ("emergency_contact", "emergency_contact"),
        ("emergency_phone", "emergency_phone"),
        ("employee_properties", "employee_properties"),
        ("employee_type", "employee_type"),
        ("gender", "gender"),
        ("has_message", "has_message"),
        ("has_work_permit", "has_work_permit"),
        ("hr_presence_state", "hr_presence_state"),
        ("id", "id"),
        ("id_card", "id_card"),
        ("identification_id", "identification_id"),
        ("image_1024", "image_1024"),
        ("image_128", "image_128"),
        ("image_1920", "image_1920"),
        ("image_256", "image_256"),
        ("image_512", "image_512"),
        ("job_title", "job_title"),
        ("km_home_work", "km_home_work"),
        ("lang", "lang"),
        ("last_activity", "last_activity"),
        ("last_activity_time", "last_activity_time"),
        ("marital", "marital"),
        ("member_of_department", "member_of_department"),
        ("message_attachment_count", "message_attachment_count"),
        ("message_has_error", "message_has_error"),
        ("message_has_error_counter", "message_has_error_counter"),
        ("message_is_follower", "message_is_follower"),
        ("message_needaction", "message_needaction"),
        ("message_needaction_counter", "message_needaction_counter"),
        ("mobile_phone", "mobile_phone"),
        ("my_activity_date_deadline", "my_activity_date_deadline"),
        ("name", "name"),
        ("newly_hired", "newly_hired"),
        ("notes", "notes"),
        ("passport_id", "passport_id"),
        ("permit_no", "permit_no"),
        ("pin", "pin"),
        ("place_of_birth", "place_of_birth"),
        ("private_car_plate", "private_car_plate"),
        ("private_city", "private_city"),
        ("private_email", "private_email"),
        ("private_phone", "private_phone"),
        ("private_street", "private_street"),
        ("private_street2", "private_street2"),
        ("private_zip", "private_zip"),
        ("show_hr_icon_display", "show_hr_icon_display"),
        ("sinid", "sinid"),
        ("spouse_birthdate", "spouse_birthdate"),
        ("spouse_complete_name", "spouse_complete_name"),
        ("ssnid", "ssnid"),
        ("study_field", "study_field"),
        ("study_school", "study_school"),
        ("tz", "tz"),
        ("visa_expire", "visa_expire"),
        ("visa_no", "visa_no"),
        ("work_email", "work_email"),
        ("work_permit_expiration_date", "work_permit_expiration_date"),
        ("work_permit_name", "work_permit_name"),
        ("work_permit_scheduled_activity", "work_permit_scheduled_activity"),
        ("work_phone", "work_phone"),
        ("write_date", "write_date"),
    ]

    def get_employee_by_match_field(self, record):
        match_field = "work_email"
        filters = []

        if self.backend_record.matching_employee:
            match_field = self.backend_record.matching_employee_ch

        filters = ast.literal_eval(self.backend_record.external_domain_filter_employee)
        if record[match_field]:
            filters.append((match_field, "=", record[match_field]))

        adapter = self.component(usage="record.exporter").backend_adapter
        employee = adapter.search(filters)
        if len(employee) == 1:
            return employee[0]

        return False


    @only_create
    @mapping
    def odoo_id(self, record):
        external_id = self.get_employee_by_match_field(record)

        if external_id:
            return {"external_id": external_id}
