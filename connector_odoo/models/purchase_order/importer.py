# Copyright 2022 GreenIce, S.L. <https://greenice.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


def _safe_value(record, name, default=False):
    try:
        value = getattr(record, name, default)
    except Exception:  # odoorpc can raise RPCError on broken remote fields/methods
        return default
    if callable(value):
        return default
    return value


class _RemoteRelationValue:
    def __init__(self, value):
        self.id = value


class _RemoteRecordValue:
    def __init__(self, values):
        self._values = {}
        for key, value in values.items():
            self._values[key] = self._wrap(value)

    def _wrap(self, value):
        if not value:
            return value
        if isinstance(value, tuple) and len(value) == 2:
            return _RemoteRelationValue(value[0])
        if isinstance(value, list):
            if len(value) == 2 and isinstance(value[0], int):
                return _RemoteRelationValue(value[0])
            if value and all(isinstance(item, int) for item in value):
                return [_RemoteRelationValue(item) for item in value]
        return value

    def __getattr__(self, name):
        if name in self._values:
            return self._values[name]
        raise AttributeError(name)

    def __getitem__(self, name):
        return self._values[name]

    def get(self, name, default=False):
        return self._values.get(name, default)


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

    def _is_uptodate(self, binding):
        if binding:
            remote_line_count = len(binding._get_remote_order_line_ids())
            if remote_line_count != binding.synced_order_line_count:
                _logger.info(
                    "Purchase order %s is not up-to-date: remote lines=%s synced lines=%s",
                    self.external_id,
                    remote_line_count,
                    binding.synced_order_line_count,
                )
                return False
        return super()._is_uptodate(binding)

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
        order_line_ids = binding._get_remote_order_line_ids()
        binding.backend_order_line_count = len(order_line_ids)
        if order_line_ids:
            delayed_line_ids = []
            for line_id in order_line_ids:
                purchase_order_line_model = self.env["odoo.purchase.order.line"]
                if self.backend_record.delayed_import_lines:
                    purchase_order_line_model = purchase_order_line_model.with_delay()
                delayed_line_id = purchase_order_line_model.import_record(
                    self.backend_record, line_id, force
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
    _apply_on = ["odoo.purchase.order.line"]

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

    def _read_remote_fields(self, fields):
        rows = self.work.odoo_api.api.execute_kw(
            "purchase.order.line",
            "read",
            [[int(self.external_id)]],
            {"fields": fields},
        )
        if isinstance(rows, dict):
            rows = [rows]
        if not rows:
            raise IDMissingInBackend
        return rows[0]

    def _get_odoo_data(self):
        data = self._read_remote_fields(
            [
                "id",
                "name",
                "price_unit",
                "date_planned",
                "display_type",
                "order_id",
                "product_id",
                "product_uom",
            ]
        )
        for quantity_field in ("product_qty", "product_uom_qty"):
            try:
                data.update(self._read_remote_fields([quantity_field]))
            except Exception as exc:
                _logger.warning(
                    "Could not read %s for remote purchase.order.line %s: %s",
                    quantity_field,
                    self.external_id,
                    exc,
                )
        return _RemoteRecordValue(data)

    def _import_dependencies(self, force):
        """Import the dependencies for the record"""
        if getattr(self.odoo_record, "product_id", False):
            self._import_dependency(
                self.odoo_record.product_id.id, "odoo.product.product", force=force
            )
        if getattr(self.odoo_record, "product_uom", False):
            self._import_dependency(
                self.odoo_record.product_uom.id, "odoo.uom.uom", force=force
            )

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
        ("price_unit", "price_unit"),
        ("date_planned", "date_planned"),
        ("display_type", "display_type"),
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
        value = _safe_value(record, field_name, False)
        if not value:
            return False
        value_id = getattr(value, "id", False)
        if callable(value_id):
            return False
        return value_id or False

    @mapping
    def name(self, record):
        name = _safe_value(record, "name", False)
        if name:
            return {"name": name}
        product = _safe_value(record, "product_id", False)
        if product and getattr(product, "display_name", False):
            return {"name": product.display_name}
        return {"name": "N/A"}

    @mapping
    def order_id(self, record):
        external_order_id = self._extract_external_id(record, "order_id")
        if not external_order_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_purchase_order", external_order_id)
        if not odoo_id:
            _logger.warning(
                "Skipping order_id mapping for purchase line %s: missing purchase order binding "
                "for backend %s external order %s",
                getattr(record, "id", "n/a"),
                self.backend_record.id,
                external_order_id,
            )
            return {}
        return {"order_id": odoo_id}

    @mapping
    def product_id(self, record):
        if _safe_value(record, "display_type", False):
            return {}
        external_product_id = self._extract_external_id(record, "product_id")
        if not external_product_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_product_product", external_product_id)
        if not odoo_id:
            _logger.warning(
                "Skipping product_id mapping for purchase line %s: missing product binding "
                "for backend %s external product %s",
                getattr(record, "id", "n/a"),
                self.backend_record.id,
                external_product_id,
            )
            return {}
        return {"product_id": odoo_id}

    @mapping
    def product_uom(self, record):
        if _safe_value(record, "display_type", False):
            return {}
        external_uom_id = self._extract_external_id(record, "product_uom")
        if not external_uom_id:
            return {}
        odoo_id = self._lookup_odoo_id("odoo_uom_uom", external_uom_id)
        if not odoo_id:
            _logger.warning(
                "Skipping product_uom mapping for purchase line %s: missing UoM binding "
                "for backend %s external UoM %s",
                getattr(record, "id", "n/a"),
                self.backend_record.id,
                external_uom_id,
            )
            return {}
        return {"product_uom": odoo_id}

    @mapping
    def quantity(self, record):
        if _safe_value(record, "display_type", False):
            return {}

        line_fields = self.env["purchase.order.line"]._fields
        quantity = _safe_value(record, "product_qty", False)
        if quantity is False:
            quantity = _safe_value(record, "product_uom_qty", False)

        if quantity is False:
            return {}
        if "product_qty" in line_fields:
            return {"product_qty": quantity}
        if "product_uom_qty" in line_fields:
            return {"product_uom_qty": quantity}
        return {}
