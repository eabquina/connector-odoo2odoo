import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class EmployeeBatchImporter(Component):
    """Import the Odoo Employee.

    For every partner in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.employee.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.employee"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo employee %s returned %s items", filters, len(external_ids)
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options)


class EmployeeImportMapper(Component):
    _name = "odoo.hr.employee.import.mapper"
    _inherit = "odoo.import.mapper"
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

    @only_create
    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.hr.employee")
        if binder.to_internal(record.id, unwrap=True):
            return { "odoo_id" : record.id }
        
        if self.backend_record.matching_employee:
            match_field = self.backend_record.matching_employee_ch

        filters = ast.literal_eval(self.backend_record.local_domain_filter_employee)
        if record[match_field]:
            filters.append((match_field, "=", record[match_field]))

        employee_ids = self.env["hr.employee"].search(filters, limit=1)
        if employee_ids:
            return {"odoo_id": employee_ids[0].id}
        return {}

    # @mapping
    # def category_ids(self, record):
    #     if record.category_ids:
    #         binder = self.binder_for("odoo.hr.employee.category")
    #         return {
    #             "category_ids": [
    #                 (
    #                     6,
    #                     0,
    #                     [
    #                         binder.to_internal(category_ids, unwrap=True).id
    #                         for category_ids in record.category_id.ids
    #                     ],
    #                 )
    #             ]
    #         }

    # @mapping
    # def subordinate_ids(self, record):
    #     if record.subordinate_ids:
    #         binder = self.binder_for("odoo.hr.employee.category")
    #         return {
    #             "subordinate_ids": [
    #                 (
    #                     6,
    #                     0,
    #                     [
    #                         binder.to_internal(subordinate_ids, unwrap=True).id
    #                         for subordinate_ids in record.subordinate_ids.ids
    #                     ],
    #                 )
    #             ]
    #         }

    # @mapping
    # def parent_id(self, record):
    #     if record.parent_id:
    #         binder = self.binder_for("odoo.hr.employee")
    #         return {
    #             "parent_id": [
    #                 (
    #                     6,
    #                     0,
    #                     [
    #                         binder.to_internal(parent_id, unwrap=True).id
    #                         for parent_id in record.parent_id.ids
    #                     ],
    #                 )
    #             ]
    #         }
        
    # @mapping
    # def coach_id(self, record):
    #     if record.coach_id:
    #         binder = self.binder_for("odoo.hr.employee")
    #         return {
    #             "coach_id": [
    #                 (
    #                     6,
    #                     0,
    #                     [
    #                         binder.to_internal(coach_id, unwrap=True).id
    #                         for coach_id in record.coach_id.ids
    #                     ],
    #                 )
    #             ]
    #         }

    # @mapping
    # def child_ids(self, record):
    #     if record.child_ids:
    #         binder = self.binder_for("odoo.hr.employee")
    #         return {
    #             "child_ids": [
    #                 (
    #                     6,
    #                     0,
    #                     [
    #                         binder.to_internal(child_ids, unwrap=True).id
    #                         for child_ids in record.child_ids.ids
    #                     ],
    #                 )
    #             ]
    #         }

    # @mapping
    # def job_id(self, record):
    #     if record.job_id:
    #         binder = self.binder_for("odoo.hr.job")
    #         return {
    #             "job_id": [
    #                 (
    #                     6,
    #                     0,
    #                     [
    #                         binder.to_internal(job_id, unwrap=True).id
    #                         for job_id in record.job_id.ids
    #                     ],
    #                 )
    #             ]
    #         }

    
class EmployeeImporter(Component):
    _name = "odoo.hr.employee.importer"
    _inherit = "odoo.importer"
    _inherits = "AbstractModel"
    _apply_on = ["odoo.hr.employee"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        # import parent
        #_logger.info("Importing dependencies for external ID %s", self.external_id)
        #if self.odoo_record.parent_id:
        #     _logger.info("Importing parent_id Manager")
        #     self._import_dependency(
        #         self.odoo_record.parent_id.id, "odoo.hr.employee", force=force
        #     )

        # if self.odoo_record.user_id:
        #     _logger.info("Importing user")
        #     self._import_dependency(
        #         self.odoo_record.user_id.id, "odoo.res.users", force=force
        #     )

        # _logger.info("Importing categories")
        # for category_id in self.odoo_record.category_id:
        #     self._import_dependency(
        #         category_id.id, "odoo.hr.employee.category", force=force
        #     )

        # if self.odoo_record.property_account_payable:
        #     _logger.info("Importing account payable")
        #     self._import_dependency(
        #         self.odoo_record.property_account_payable_id.id,
        #         "odoo.account.account",
        #         force=force,
        #     )

        # if self.odoo_record.property_account_receivable:
        #     _logger.info("Importing account receivable")
        #     self._import_dependency(
        #         self.odoo_record.property_account_receivable_id.id,
        #         "odoo.account.account",
        #         force=force,
        #     )

        # if (
        #     hasattr(self.odoo_record, "property_purchase_currency_id")
        #     and self.odoo_record.property_purchase_currency_id
        # ):
        #     _logger.info("Importing supplier currency")
        #     self._import_dependency(
        #         self.odoo_record.property_purchase_currency_id.id,
        #         "odoo.res.currency",
        #         force=force,
        #     )

        # if (
        #     self.odoo_record.property_product_pricelist_purchase
        #     and self.odoo_record.property_product_pricelist_purchase.currency_id
        # ):
        #     _logger.info("Importing supplier currency")
        #     self._import_dependency(
        #         self.odoo_record.property_product_pricelist_purchase.currency_id.id,
        #         "odoo.res.currency",
        #         force=force,
        #     )

        result = super()._import_dependencies(force=force)
        #_logger.info("Dependencies imported for external ID %s", self.external_id)
        return result

    def _after_import(self, binding, force=False):
        if self.backend_record.version == "6.1":
            _logger.info(
                "OpenERP detected, importing adresses for external ID %s",
                self.external_id,
            )
            self.env["odoo.hr.employee.address.disappeared"].with_delay().import_record(
                self.backend_record, self.external_id
            )
        return super()._after_import(binding, force)
