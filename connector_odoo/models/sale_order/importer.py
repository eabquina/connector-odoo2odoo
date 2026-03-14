# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class SaleOrderBatchImporter(Component):
    """Import the Odoo Sale Orders.

    For every sale order in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level pricelist imported first.
    """

    _name = "odoo.sale.order.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.sale.order"]
    _usage = "batch.importer"

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo sale orders %s returned %s items",
            filters,
            len(updated_ids),
        )
        base_priority = 10
        for order in updated_ids:
            order_id = self.backend_adapter.read(order)
            job_options = {
                "priority": base_priority,
            }
            self._import_record(order_id.id, job_options=job_options)


class SaleOrderImporter(Component):
    _name = "odoo.sale.order.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.sale.order"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        self._import_dependency(
            self.odoo_record.pricelist_id.id, "odoo.product.pricelist", force=force
        )
        self._import_dependency(
            self.odoo_record.partner_id.id, "odoo.res.partner", force=force
        )
        for partner_id in [
            self.odoo_record.partner_shipping_id,
            self.odoo_record.partner_invoice_id,
        ]:
            self._import_dependency(partner_id.id, "odoo.res.partner", force=force)

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if self.odoo_record.order_line:
            delayed_line_ids = []
            for line_id in self.odoo_record.order_line:
                order_line_model = self.env["odoo.sale.order.line"]
                if self.backend_record.delayed_import_lines:
                    order_line_model = order_line_model.with_delay()
                delayed_line_id = order_line_model.import_record(
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
        if not self.backend_record.delayed_import_lines:
            binding._set_state()
            self.env["odoo.stock.picking"].with_delay().import_batch(
                self.backend_record,
                [("sale_id", "=", self.odoo_record.id)],
            )
        return res


class SaleOrderImportMapper(Component):
    _name = "odoo.sale.order.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.sale.order"

    direct = [
        ("date_order", "backend_date_order"),
        ("name", "name"),
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
        order = self.env["sale.order"].search([("name", "=", record.name)])
        _logger.debug("found sale order %s for record %s" % (record.name, record))
        if len(order) == 1:
            return {"odoo_id": order.id}

        return {}

    @mapping
    def pricelist_id(self, record):
        binder = self.binder_for("odoo.product.pricelist")
        pricelist_id = binder.to_internal(record.pricelist_id.id, unwrap=True)
        return {"pricelist_id": pricelist_id.id}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for("odoo.res.partner")
        return {
            "partner_id": binder.to_internal(record.partner_id.id, unwrap=True).id,
            "partner_invoice_id": binder.to_internal(
                record.partner_invoice_id.id, unwrap=True
            ).id,
            "partner_shipping_id": binder.to_internal(
                record.partner_shipping_id.id, unwrap=True
            ).id,
        }


class SaleOrderLineBatchImporter(Component):
    """Import the Odoo Sale Order Lines.

    For every pricelist item in the list, a delayed job is created.
    """

    _name = "odoo.sale.order.line.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.sale.order.item"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo sale orders %s returned %s items",
            filters,
            len(updated_ids),
        )
        for order in updated_ids:
            order_id = self.backend_adapter.read(order)
            job_options = {
                "priority": 10,
            }
            self._import_record(order_id.id, job_options=job_options)


class SaleOrderLineImporter(Component):
    _name = "odoo.sale.order.line.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.sale.order.line"]

    def _has_product_binding(self, external_product_id):
        self.env.cr.execute(
            """
            SELECT 1
              FROM odoo_product_product
             WHERE backend_id = %s
               AND external_id = %s
             LIMIT 1
            """,
            (self.backend_record.id, external_product_id),
        )
        return bool(self.env.cr.fetchone())

    def _has_order_binding(self, external_order_id):
        self.env.cr.execute(
            """
            SELECT 1
              FROM odoo_sale_order
             WHERE backend_id = %s
               AND external_id = %s
             LIMIT 1
            """,
            (self.backend_record.id, external_order_id),
        )
        return bool(self.env.cr.fetchone())

    def _must_skip(self):
        if getattr(self.odoo_record, "order_id", False):
            external_order_id = self.odoo_record.order_id.id
            if not self._has_order_binding(external_order_id):
                _logger.warning(
                    "Skipping sale order line %s: missing sale order binding "
                    "for backend %s external order %s",
                    self.external_id,
                    self.backend_record.id,
                    external_order_id,
                )
                return True
        # Note/section lines do not need a product binding.
        if getattr(self.odoo_record, "display_type", False):
            return False
        if getattr(self.odoo_record, "product_id", False):
            external_product_id = self.odoo_record.product_id.id
            if not self._has_product_binding(external_product_id):
                _logger.warning(
                    "Skipping sale order line %s: missing product binding "
                    "for backend %s external product %s",
                    self.external_id,
                    self.backend_record.id,
                    external_product_id,
                )
                return True
        return False

    def _import_dependencies(self, force):
        if getattr(self.odoo_record, "order_id", False):
            self._import_dependency(
                self.odoo_record.order_id.id, "odoo.sale.order", force=force
            )
        if getattr(self.odoo_record, "product_id", False):
            self._import_dependency(
                self.odoo_record.product_id.id, "odoo.product.product", force=force
            )
        if getattr(self.odoo_record, "product_uom", False):
            self._import_dependency(
                self.odoo_record.product_uom.id, "odoo.uom.uom", force=force
            )

    def _update(self, binding, data):
        if "product_id" in data and not binding.odoo_id.product_updatable:
            _logger.info(
                "Dropping product_id update for sale order line %s (product not updatable).",
                binding.odoo_id.id,
            )
            data = dict(data)
            data.pop("product_id", None)
        return super()._update(binding, data)

    def _has_pending_sibling_jobs(self, queue_jobs):
        """True when another active line import job is still running."""
        current_job_uuid = self.env.context.get("job_uuid")
        active_states = ("pending", "enqueued", "started", "wait_dependencies")
        pending_jobs = queue_jobs.filtered(lambda job: job.state in active_states)
        if current_job_uuid:
            pending_jobs = pending_jobs.filtered(lambda job: job.uuid != current_job_uuid)
        return bool(pending_jobs)

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if self.backend_record.delayed_import_lines:
            pending = self._has_pending_sibling_jobs(binding.order_id.queue_job_ids)
            if not pending:
                binding = self.env["odoo.sale.order"].search(
                    [("odoo_id", "=", binding.order_id.id)]
                )
                if not len(binding.picking_ids):
                    binding._set_state()
                self.env["odoo.stock.picking"].with_delay().import_batch(
                    self.backend_record,
                    [("sale_id", "=", self.odoo_record.order_id.id)],
                )
        return res


class SaleOrderLineImportMapper(Component):
    _name = "odoo.sale.order.line.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.sale.order.line"

    direct = [
        ("name", "name"),
        ("price_unit", "price_unit"),
        ("product_uom_qty", "product_uom_qty"),
        ("product_qty", "product_qty"),
        ("display_type", "display_type"),
        ("customer_lead", "customer_lead"),
        ("discount", "discount"),
    ]

    def _lookup_odoo_id(self, table, external_id):
        self.env.cr.execute(
            f"""
            SELECT odoo_id
              FROM {table}
             WHERE backend_id = %s
               AND external_id = %s
             ORDER BY id DESC
             LIMIT 1
            """,
            (self.backend_record.id, external_id),
        )
        row = self.env.cr.fetchone()
        return row[0] if row else False

    def _extract_external_id(self, record, field_name):
        value = getattr(record, field_name, False)
        if not value:
            return False
        value_id = getattr(value, "id", False)
        if callable(value_id):
            return False
        return value_id or False

    @mapping
    def product_id(self, record):
        external_product_id = self._extract_external_id(record, "product_id")
        if not external_product_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_product_product", external_product_id)
        if not odoo_id:
            _logger.warning(
                "Skipping product_id mapping for sale line %s: missing product binding "
                "for backend %s external product %s",
                getattr(record, "id", "n/a"),
                self.backend_record.id,
                external_product_id,
            )
            return {}
        return {
            "product_id": odoo_id,
        }

    @mapping
    def order_id(self, record):
        external_order_id = self._extract_external_id(record, "order_id")
        if not external_order_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_sale_order", external_order_id)
        if not odoo_id:
            _logger.warning(
                "Skipping order_id mapping for sale line %s: missing sale order binding "
                "for backend %s external order %s",
                getattr(record, "id", "n/a"),
                self.backend_record.id,
                external_order_id,
            )
            return {}
        return {
            "order_id": odoo_id,
        }

    @mapping
    def product_uom(self, record):
        external_uom_id = self._extract_external_id(record, "product_uom")
        if not external_uom_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_uom_uom", external_uom_id)
        if not odoo_id:
            _logger.warning(
                "Skipping product_uom mapping for sale line %s: missing UoM binding "
                "for backend %s external UoM %s",
                getattr(record, "id", "n/a"),
                self.backend_record.id,
                external_uom_id,
            )
            return {}
        return {
            "product_uom": odoo_id,
        }
