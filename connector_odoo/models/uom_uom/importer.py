# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class UomBatchImporter(Component):
    _name = "odoo.uom.uom.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.uom.uom"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        external_ids = self.backend_adapter.search(
            filters,
        )
        _logger.info(
            "search for odoo uom %s returned %s items", filters, len(external_ids)
        )
        for external_id in external_ids:
            job_options = {
                "priority": 15,
            }
            self._import_record(external_id, job_options=job_options)


class UomMapper(Component):
    _name = "odoo.uom.uom.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.uom.uom"

    direct = [
        ("name", "name"),
        ("factor_inv", "factor_inv"),
        ("factor", "factor"),
        ("uom_type", "uom_type"),
        ("rounding", "rounding"),
    ]

    # TODO: Improve and check family, factor etc...

    @mapping
    def category_id(self, record):
        category_id = record.category_id
        return {"category_id": category_id.id}

    @only_create
    @mapping
    def check_uom_exists(self, record):
        res = {}
        category_name = record.category_id.name
        lang = (
            self.backend_record.default_lang_id.code
            or self.env.user.lang
            or self.env.context["lang"]
            or "en_US"
        )
        _logger.info("CHECK ONLY CREATE UOM %s with lang %s" % (record["name"], lang))

        local_uom_id = (
            self.env["uom.uom"]
            .with_context(lang=lang)
            .search(
                [("name", "=", record.name), ("category_id.name", "=", category_name)]
            )
        )
        _logger.info("UOM found for %s : %s" % (record, local_uom_id))
        if len(local_uom_id) == 1:
            res.update({"odoo_id": local_uom_id.id})
        # If not found test if UOM was renamed and is "reference" for its category
        if record.uom_type == "reference":
            local_uom_id = (
                self.env["uom.uom"]
                .with_context(lang=lang)
                .search(
                    [
                        ("factor", "=", record.factor),
                        ("category_id.name", "=", category_name),
                    ]
                )
            )
            if len(local_uom_id) == 1:
                res.update({"odoo_id": local_uom_id.id})
            else:   
                res.update({"odoo_id": 1}) 
                # raise ValidationError(
                #     _(
                #         "Unable to find Reference UOM with format {format}\
                #     for category {category_name}. \
                #     It is possible that the UOM {name} was renamed. \
                #     Defaulting to the first UOM found in the category. \
                #     Please check the UOM in Odoo. \
                #     If you want to import the UOM, please rename it in Odoo \
                #     and reimport it. \
                #     If you want to skip it, please set the UOM as not reference \
                #     in the Odoo backend. \
                #     UOM found : {local_uom_id} \
                #     UOM to import : {record} \
                #     UOM to import name : {name} \
                #     UOM to import factor : {factor} \
                #     UOM to import category : {category_name} \
                #     UOM to import uom_type : {uom_type} \
                #     UOM to import rounding : {rounding} \
                #     UOM to import factor_inv : {factor_inv} \
                #     UOM to import factor : {factor} \   "
                #     )
                # )
        return res


class UoMImporter(Component):
    """Import Odoo UOM"""

    _name = "odoo.uom.uom.importer"
    _inherit = "odoo.importer"
    _apply_on = "odoo.uom.uom"

    _protected_existing_uom_fields = {
        "factor",
        "factor_inv",
        "uom_type",
        "category_id",
        "rounding",
    }

    def _strip_protected_uom_fields(self, values, existing_odoo_id=False):
        """Avoid forbidden ratio writes on already-used local UoM records."""
        if not existing_odoo_id:
            return values
        sanitized = dict(values)
        for field_name in self._protected_existing_uom_fields:
            sanitized.pop(field_name, None)
        return sanitized

    def _create_data(self, map_record, **kwargs):
        values = super()._create_data(map_record, **kwargs)
        return self._strip_protected_uom_fields(
            values, existing_odoo_id=bool(values.get("odoo_id"))
        )

    def _update_data(self, map_record, **kwargs):
        values = super()._update_data(map_record, **kwargs)
        binding = self.binder.to_internal(self.external_id)
        existing_odoo_id = bool(binding and binding.odoo_id)
        return self._strip_protected_uom_fields(
            values, existing_odoo_id=existing_odoo_id
        )
