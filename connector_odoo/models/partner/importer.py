# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


def _safe_value(record, name, default=False):
    """Return an attribute value from an odoorpc record safely.

    odoorpc returns a callable rpc_method for missing fields; treat it as missing.
    """
    try:
        value = getattr(record, name)
    except AttributeError:
        return default
    if callable(value):
        return default
    return value


def get_state_from_record(self, record):
    state_id = False
    country_id = False
    country = _safe_value(record, "country_id", False)
    if country:
        country_code = _safe_value(country, "code", False)
    else:
        country_code = "CA"
    country_rec = self.env["res.country"].search([("code", "=", country_code)], limit=1)
    country_id = country_rec.id

    state = _safe_value(record, "state_id", False)
    if state and country_id:
        state_code = _safe_value(state, "code", False)
        state_name = _safe_value(state, "name", False)
        state_rec = False
        if state_code:
            state_rec = self.env["res.country.state"].search(
                [("code", "=", state_code), ("country_id", "=", country_id)], limit=1
            )
        if not state_rec and state_name:
            state_rec = self.env["res.country.state"].search(
                [("name", "=", state_name), ("country_id", "=", country_id)], limit=1
            )
        state_id = state_rec.id if state_rec else False
    return {
        "state_id": state_id,
        "country_id": country_id,
    }


class PartnerBatchImporter(Component):
    """Import the Odoo Partner.

    For every partner in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.res.partner.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.partner"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo partner %s returned %s items", filters, len(external_ids)
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options)


class PartnerImportMapper(Component):
    _name = "odoo.res.partner.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.res.partner"]

    # TODO :     special_price => minimal_price
    direct = [
        ("name", "name"),
        ("website", "website"),
        ("lang", "lang"),
        ("ref", "ref"),
        ("comment", "comment"),
        ("company_type", "company_type"),
        ("zip", "zip"),
        #("delivery_margin", "delivery_margin"),
    ]

    @mapping
    def category_id(self, record):
        categories = _safe_value(record, "category_id", False)
        if categories:
            binder = self.binder_for("odoo.res.partner.category")
            internal_category_ids = []
            for category_id in categories.ids:
                internal_category = binder.to_internal(category_id, unwrap=True)
                if internal_category:
                    internal_category_ids.append(internal_category.id)
            if not internal_category_ids:
                return {}
            return {
                "category_id": [
                    (
                        6,
                        0,
                        [
                            category_id
                            for category_id in internal_category_ids
                        ],
                    )
                ]
            }
        return {}

    @mapping
    def email(self, record):
        email = _safe_value(record, "email", None)
        if email is None:
            return {}
        return {"email": email}

    @mapping
    def street(self, record):
        street = _safe_value(record, "street", None)
        if street is None:
            return {}
        return {"street": street}

    @mapping
    def street2(self, record):
        street2 = _safe_value(record, "street2", None)
        if street2 is None:
            return {}
        return {"street2": street2}

    @mapping
    def phone(self, record):
        phone = _safe_value(record, "phone", None)
        if phone is None:
            return {}
        return {"phone": phone}

    @mapping
    def mobile(self, record):
        mobile = _safe_value(record, "mobile", None)
        if mobile is None:
            return {}
        return {"mobile": mobile}

    @mapping
    def city(self, record):
        city = _safe_value(record, "city", None)
        if city is None:
            return {}
        return {"city": city}

    @mapping
    def state_id(self, record):
        return get_state_from_record(self, record)

    @mapping
    def customer(self, record):
        customer_rank = _safe_value(record, "customer_rank", None)
        if customer_rank is None:
            customer = _safe_value(record, "customer", None)
            if customer is None:
                return {}
            customer_rank = int(bool(customer))
        return {"customer_rank": customer_rank}

    @mapping
    def supplier(self, record):
        supplier_rank = _safe_value(record, "supplier_rank", None)
        if supplier_rank is None:
            supplier = _safe_value(record, "supplier", None)
            if supplier is None:
                return {}
            supplier_rank = int(bool(supplier))
        return {"supplier_rank": supplier_rank}

    @mapping
    def image(self, record):
        image = _safe_value(record, "image_1920", None)
        if image is None:
            image = _safe_value(record, "image", None)
        if image is None:
            return {}
        return {"image_1920": image}

    @mapping
    def parent_id(self, record):
        parent_id = _safe_value(record, "parent_id", False)
        if parent_id:
            binder = self.binder_for("odoo.res.partner")
            parent = binder.to_internal(parent_id.id, unwrap=True)
            if parent:
                return {"parent_id": parent.id}
        return {}

    @mapping
    def company_id(self, record):
        """Map company_id to the current user's company."""
        # Don't import company_id from source - use local company
        return {"company_id": self.env.company.id}

    @mapping
    def user_id(self, record):
        user_id = _safe_value(record, "user_id", False)
        if user_id:
            binder = self.binder_for("odoo.res.users")
            user = binder.to_internal(user_id.id, unwrap=True)
            if user:
                return {"user_id": user.id}
        return {}

    @mapping
    def property_account_payable(self, record):
        if float(self.backend_record.version) >= 9.0:
            property_account_payable_id = _safe_value(
                record, "property_account_payable_id", False
            )
        else:
            property_account_payable_id = _safe_value(
                record, "property_account_payable", False
            )

        if property_account_payable_id:
            binder = self.binder_for("odoo.account.account")
            account = binder.to_internal(property_account_payable_id.id, unwrap=True)
            if account:
                return {"property_account_payable_id": account.id}
        return {}

    @mapping
    def property_account_receivable(self, record):
        if float(self.backend_record.version) >= 9.0:
            property_account_receivable_id = _safe_value(
                record, "property_account_receivable_id", False
            )
        else:
            property_account_receivable_id = _safe_value(
                record, "property_account_receivable", False
            )

        if property_account_receivable_id:
            binder = self.binder_for("odoo.account.account")
            account = binder.to_internal(property_account_receivable_id.id, unwrap=True)
            if account:
                return {"property_account_receivable_id": account.id}
        return {}

    # @mapping
    # def property_purchase_currency_id(self, record):
    #     property_purchase_currency_id = None
    #     if hasattr(record, "property_purchase_currency_id"):
    #         property_purchase_currency_id = record.property_purchase_currency_id
    #     if not property_purchase_currency_id:
    #         if (
    #             record.property_product_pricelist_purchase
    #             and record.property_product_pricelist_purchase.currency_id
    #         ):
    #             property_purchase_currency_id = (
    #                 record.property_product_pricelist_purchase.currency_id
    #             )
    #     if property_purchase_currency_id:
    #         binder = self.binder_for("odoo.res.currency")
    #         currency = binder.to_internal(property_purchase_currency_id.id, unwrap=True)
    #         if currency:
    #             return {"property_purchase_currency_id": currency.id}


class PartnerImporter(Component):
    _name = "odoo.res.partner.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.res.partner"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        # import parent
        _logger.info("Importing dependencies for external ID %s", self.external_id)
        parent_id = _safe_value(self.odoo_record, "parent_id", False)
        if parent_id:
            _logger.info("Importing parent")
            self._import_dependency(
                parent_id.id, "odoo.res.partner", force=force
            )

        user_id = _safe_value(self.odoo_record, "user_id", False)
        if user_id:
            _logger.info("Importing user")
            self._import_dependency(
                user_id.id, "odoo.res.users", force=force
            )

        _logger.info("Importing categories")
        categories = _safe_value(self.odoo_record, "category_id", False)
        for category_id in categories or []:
            self._import_dependency(
                category_id.id, "odoo.res.partner.category", force=force
            )

        payable = _safe_value(self.odoo_record, "property_account_payable_id", False)
        if payable:
            _logger.info("Importing account payable")
            self._import_dependency(
                payable.id,
                "odoo.account.account",
                force=force,
            )

        receivable = _safe_value(
            self.odoo_record, "property_account_receivable_id", False
        )
        if receivable:
            _logger.info("Importing account receivable")
            self._import_dependency(
                receivable.id,
                "odoo.account.account",
                force=force,
            )

        purchase_currency = _safe_value(
            self.odoo_record, "property_purchase_currency_id", None
        )
        if purchase_currency:
            _logger.info("Importing supplier currency")
            self._import_dependency(
                purchase_currency.id,
                "odoo.res.currency",
                force=force,
            )

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
        _logger.info("Dependencies imported for external ID %s", self.external_id)
        return result

    def _after_import(self, binding, force=False):
        return super()._after_import(binding, force)
