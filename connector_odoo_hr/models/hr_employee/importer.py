
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


def get_state_from_record(self, record):
    state_id = False
    country_id = False
    if record.country_id:
        country_code = record.country_id.code
    else:
        country_code = "CA"
    country = self.env["res.country"].search(
        [
            ("code", "=", country_code),
        ]
    )
    country_id = country.id
    if hasattr(record, "state_id") and record.state_id:
        state = self.env["res.country.state"].search(
            [
                ("code", "=", record.state_id.code),
                ("country_id", "=", country_id),
            ]
        )
        if not state:
            state = self.env["res.country.state"].search(
                [
                    ("name", "=", record.state_id.name),
                    ("country_id", "=", country_id),
                ]
            )
        state_id = state.id
    return {
        "state_id": state_id,
        "country_id": country_id,
    }


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
            "search for odoo partner %s returned %s items", filters, len(external_ids)
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options)


class EmployeeImportMapper(Component):
    _name = "odoo.hr.employee.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.employee"]

    direct = [
        ("name", "name"),
        ("active", "active"),
        ("name", "name"),
        ("avatar_128", "avatar_128"),
        ("avatar_256", "avatar_256"),
        ("avatar_512", "avatar_512"),
        ("color", "color"),
        ("job_title", "job_title"),
        ("work_phone", "work_phone"),
        ("work_email", "work_email"),
        ("category_ids", "category_ids"),
        ("subordinate_ids", "subordinate_ids"),
        ("parent_id", "parent_id"),
        ("coach_id", "coach_id"),
        ("child_ids", "child_ids"),
        ("job_id", "job_id"),
    ]

    @mapping
    def category_ids(self, record):
        if record.category_ids:
            binder = self.binder_for("odoo.hr.employee.category")
            return {
                "category_ids": [
                    (
                        6,
                        0,
                        [
                            binder.to_internal(category_ids, unwrap=True).id
                            for category_ids in record.category_id.ids
                        ],
                    )
                ]
            }

    @mapping
    def subordinate_ids(self, record):
        if record.subordinate_ids:
            binder = self.binder_for("odoo.hr.employee.category")
            return {
                "subordinate_ids": [
                    (
                        6,
                        0,
                        [
                            binder.to_internal(subordinate_ids, unwrap=True).id
                            for subordinate_ids in record.subordinate_ids.ids
                        ],
                    )
                ]
            }

    @mapping
    def parent_id(self, record):
        if record.parent_id:
            binder = self.binder_for("odoo.hr.employee")
            return {
                "parent_id": [
                    (
                        6,
                        0,
                        [
                            binder.to_internal(parent_id, unwrap=True).id
                            for parent_id in record.parent_id.ids
                        ],
                    )
                ]
            }
        
    @mapping
    def coach_id(self, record):
        if record.coach_id:
            binder = self.binder_for("odoo.hr.employee")
            return {
                "coach_id": [
                    (
                        6,
                        0,
                        [
                            binder.to_internal(coach_id, unwrap=True).id
                            for coach_id in record.coach_id.ids
                        ],
                    )
                ]
            }

    @mapping
    def child_ids(self, record):
        if record.child_ids:
            binder = self.binder_for("odoo.hr.employee")
            return {
                "child_ids": [
                    (
                        6,
                        0,
                        [
                            binder.to_internal(child_ids, unwrap=True).id
                            for child_ids in record.child_ids.ids
                        ],
                    )
                ]
            }

    @mapping
    def job_id(self, record):
        if record.job_id:
            binder = self.binder_for("odoo.hr.job")
            return {
                "job_id": [
                    (
                        6,
                        0,
                        [
                            binder.to_internal(job_id, unwrap=True).id
                            for job_id in record.job_id.ids
                        ],
                    )
                ]
            }

    
class EmployeeImporter(Component):
    _name = "odoo.hr.employee.importer"
    _inherit = "odoo.importer"
    _inherits = "AbstractModel"
    _apply_on = ["odoo.hr.employee"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        # import parent
        #_logger.info("Importing dependencies for external ID %s", self.external_id)
        if self.odoo_record.parent_id:
             _logger.info("Importing parent_id Manager")
             self._import_dependency(
                 self.odoo_record.parent_id.id, "odoo.hr.employee", force=force
             )

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
