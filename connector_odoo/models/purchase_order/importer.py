# Copyright 2022 GreenIce, S.L. <https://greenice.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


def _safe_value(record, name, default=False):
    value = getattr(record, name, default)
    if callable(value):
        return default
    return value


class PurchaseOrderBatchImporter(Component):
    """Import the Odoo Purchase Orders.

    For every purchase order in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level pricelist imported first.
    """

    _name = "odoo.purchase.order.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.purchase.order"]
    _usage = "batch.importer"

    def _import_record(self, external_id, job_options=None, force=False):
        """Delay a job for the import"""
        return super()._import_record(external_id, job_options=job_options, force=force)

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo purchase orders %s returned %s items",
            filters,
            len(updated_ids),
        )
        base_priority = 10
        for external_id in updated_ids:
            job_options = {
                "priority": base_priority,
            }
            self._import_record(external_id, job_options=job_options, force=force)


class PurchaseOrderImporter(Component):
    _name = "odoo.purchase.order.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.purchase.order"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        partner = _safe_value(self.odoo_record, "partner_id", False)
        if partner and getattr(partner, "id", False):
            self._import_dependency(
                partner.id, "odoo.res.partner", force=force
            )

        pricelist = _safe_value(self.odoo_record, "pricelist_id", False)
        pricelist_currency = False
        if pricelist:
            pricelist_currency = _safe_value(pricelist, "currency_id", False)
        if pricelist_currency and getattr(pricelist_currency, "id", False):
            self._import_dependency(
                pricelist_currency.id, "odoo.res.currency", force=False
            )

        currency = _safe_value(self.odoo_record, "currency_id", False)
        if currency and getattr(currency, "id", False):
            self._import_dependency(currency.id, "odoo.res.currency", force=False)

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if self.odoo_record.order_line:
            delayed_line_ids = []
            for line_id in self.odoo_record.order_line:
                purchase_order_line_model = self.env["odoo.purchase.order.line"]
                if self.backend_record.delayed_import_lines:
                    purchase_order_line_model = purchase_order_line_model.with_delay()
                delayed_line_id = purchase_order_line_model.import_record(
                    self.backend_record, line_id.id, force
                )
                if self.backend_record.delayed_import_lines:
                    delayed_line_id = self.env["queue.job"].search(
                        [("uuid", "=", delayed_line_id.uuid)]
                    )
                    delayed_line_ids.append(delayed_line_id.id)
            if self.backend_record.delayed_import_lines:
                binding.queue_job_ids = [
                    (6, 0, (delayed_line_ids + binding.queue_job_ids.ids))
                ]
            else:
                self.env["odoo.stock.picking"].import_batch(
                    self.backend_record, [("purchase_id", "=", self.odoo_record.id)]
                )
                binding.with_delay()._set_state()
        return res


class PurchaseOrderImportMapper(Component):
    _name = "odoo.purchase.order.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.purchase.order"

    direct = [
        ("name", "name"),
        ("partner_ref", "partner_ref"),
        ("origin", "origin"),
        ("date_order", "date_order"),
        ("state", "backend_state"),
    ]

    @mapping
    def backend_amount_total(self, record):
        return {"backend_amount_total": record.amount_total}

    @mapping
    def backend_amount_tax(self, record):
        return {"backend_amount_tax": record.amount_tax}

    @mapping
    def backend_picking_count(self, record):
        return {"backend_picking_count": len(record.picking_ids)}

    @only_create
    @mapping
    def odoo_id(self, record):
        order = self.env["purchase.order"].search(
            [
                ("name", "=", record.name),
            ]
        )
        _logger.debug("found purchase order %s for record %s" % (record.name, record))
        if len(order) == 1:
            return {"odoo_id": order.id}
        return {}

    @mapping
    def currency_id(self, record):
        currency_id = self.env.user.company_id.currency_id
        binder = self.binder_for("odoo.res.currency")
        currency_id = binder.to_internal(record.currency_id.id, unwrap=True)
        return {"currency_id": currency_id.id}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for("odoo.res.partner")
        partner_id = binder.to_internal(record.partner_id.id, unwrap=True)
        return {
            "partner_id": partner_id.id,
        }

    @mapping
    def date_planned(self, record):
        if hasattr(record, "date_planned"):
            return {"date_planned": record.date_planned}

    @mapping
    def picking_type_id(self, record):
        remote_picking_type = _safe_value(record, "picking_type_id", False)
        if not remote_picking_type:
            return {}

        # Optional binding model: not always installed in every connector setup.
        if "odoo.stock.picking.type" in self.env.registry.models:
            binder = self.binder_for("odoo.stock.picking.type")
            mapped = binder.to_internal(remote_picking_type.id, unwrap=True)
            if mapped:
                return {"picking_type_id": mapped.id}

        # Fallback to local stock.picking.type using stable identifiers.
        code = _safe_value(remote_picking_type, "code", False)
        if code:
            local_type = self.env["stock.picking.type"].search([("code", "=", code)], limit=1)
            if local_type:
                return {"picking_type_id": local_type.id}

        name = _safe_value(remote_picking_type, "name", False)
        if name:
            local_type = self.env["stock.picking.type"].search([("name", "=", name)], limit=1)
            if local_type:
                return {"picking_type_id": local_type.id}

        _logger.warning(
            "Skipping purchase order picking_type_id mapping for external record %s: "
            "no local picking type match found.",
            _safe_value(record, "id", "n/a"),
        )
        return {}


class PurchaseOrderLineBatchImporter(Component):
    """Import the Odoo Purchase Order Lines.

    For every pricelist item in the list, a delayed job is created.
    """

    _name = "odoo.purchase.order.line.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.purchase.order.item"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo purchase orders %s returned %s items",
            filters,
            len(updated_ids),
        )
        for external_id in updated_ids:
            job_options = {
                "priority": 10,
            }
            self._import_record(external_id, job_options=job_options, force=force)


class PurchaseOrderLineImporter(Component):
    _name = "odoo.purchase.order.line.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.purchase.order.line"]

    def _import_dependencies(self, force):
        """Import the dependencies for the record"""
        self._import_dependency(
            self.odoo_record.product_id.id, "odoo.product.product", force=force
        )
        self._import_dependency(
            self.odoo_record.product_uom.id, "odoo.uom.uom", force=force
        )

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if self.backend_record.delayed_import_lines:
            pending = binding.order_id.queue_job_ids.filtered(
                lambda x: x.state != "done" and x.args[1] != self.odoo_record.id
            )
            if not pending:
                binding = self.env["odoo.purchase.order"].search(
                    [("odoo_id", "=", binding.order_id.id)]
                )
                if not len(binding.picking_ids):
                    binding.with_delay()._set_state()
                self.env["odoo.stock.picking"].with_delay().import_batch(
                    self.backend_record,
                    [("purchase_id", "=", self.odoo_record.order_id.id)],
                )
        return res


class PurchaseOrderLineImportMapper(Component):
    _name = "odoo.purchase.order.line.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.purchase.order.line"

    direct = [
        ("name", "name"),
        ("price_unit", "price_unit"),
        ("product_uom_qty", "product_uom_qty"),
        ("product_qty", "product_qty"),
        ("date_planned", "date_planned"),
        ("display_type", "display_type"),
    ]

    @mapping
    def order_id(self, record):
        binder = self.binder_for("odoo.purchase.order")
        return {"order_id": binder.to_internal(record.order_id.id, unwrap=True).id}

    @mapping
    def product_id(self, record):
        binder = self.binder_for("odoo.product.product")
        return {
            "product_id": binder.to_internal(record.product_id.id, unwrap=True).id,
        }

    @mapping
    def product_uom(self, record):
        binder = self.binder_for("odoo.uom.uom")
        return {
            "product_uom": binder.to_internal(record.product_uom.id, unwrap=True).id,
        }
