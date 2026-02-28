# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class StockPickingBatchImporter(Component):
    _name = "odoo.stock.picking.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.stock.picking"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        external_ids = self.backend_adapter.search(
            filters,
        )
        _logger.info(
            "search for odoo Warehouse %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {
                "priority": 15,
            }
            self._import_record(external_id, job_options=job_options)


class StockPickingImporter(Component):
    _name = "odoo.stock.picking.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.stock.picking"]

    def _must_skip(
        self,
    ):
        have_lines = len(self.odoo_record["move_lines"]) > 0
        if not have_lines:
            return True
        binding = self._get_binding()
        if binding and binding.state in ["done", "cancel"]:
            return True
        return False

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        for move_id in self.odoo_record["move_lines"]:
            self._import_dependency(
                move_id.location_id.id, "odoo.stock.location", force=force
            )

            self._import_dependency(
                move_id.location_dest_id.id, "odoo.stock.location", force=force
            )
            break
        if self.odoo_record["partner_id"]:
            self._import_dependency(
                self.odoo_record["partner_id"].id, "odoo.res.partner", force=force
            )

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force)
        if self.odoo_record.move_lines:
            delayed_line_ids = []
            for line_id in self.odoo_record.move_lines:
                stock_move_model = self.env["odoo.stock.move"]
                if self.backend_record.delayed_import_lines:
                    stock_move_model = stock_move_model.with_delay()
                delayed_line_id = stock_move_model.import_record(
                    self.backend_record, line_id.id, force=True
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
                binding.with_delay()._set_state()
        return res

    def _get_binding_odoo_id_changed(self, binding):
        if binding:
            return binding
        record = self.odoo_record
        mapper = self.component(usage="import.mapper")

        # Reuse existing binding when mapper already resolved a local picking.
        mapped_odoo_id = mapper.odoo_id(record).get("odoo_id")
        if mapped_odoo_id:
            existing_binding = self.env["odoo.stock.picking"].search(
                [
                    ("backend_id", "=", self.backend_record.id),
                    ("odoo_id", "=", mapped_odoo_id),
                ],
                limit=1,
            )
            if existing_binding:
                return existing_binding

        if record.sale_id and record.move_lines:
            # If picking is created when changing state importing of sale order
            binder = self.binder_for("odoo.sale.order")
            sale_id = binder.to_internal(record.sale_id.id, unwrap=True)
            move_id = False
            for move in record.move_lines:
                move_id = move
                break
            existing_picking_id = self.env["stock.picking"]
            try:
                picking_type_id = mapper.get_picking_type_from_external_locations(
                    "picking", record, move_id.location_id, move_id.location_dest_id
                )
                existing_picking_id = sale_id.picking_ids.filtered(
                    lambda x: x.picking_type_id == picking_type_id
                )
            except ValidationError:
                # Fallback: when no picking type mapping can be resolved, try to
                # bind to the already created sale picking by exact name.
                if getattr(record, "name", False):
                    existing_picking_id = sale_id.picking_ids.filtered(
                        lambda x: x.name == record.name
                    )
                if not existing_picking_id and getattr(record, "origin", False):
                    existing_picking_id = sale_id.picking_ids.filtered(
                        lambda x: x.origin == record.origin
                    )
            if existing_picking_id:
                existing_binding = self.env["odoo.stock.picking"].search(
                    [
                        ("backend_id", "=", self.backend_record.id),
                        ("odoo_id", "=", existing_picking_id.id),
                    ],
                    limit=1,
                )
                if existing_binding:
                    return existing_binding
                return self.env["odoo.stock.picking"].create(
                    {
                        "odoo_id": existing_picking_id.id,
                        "backend_id": self.backend_record.id,
                        "external_id": record.id,
                    }
                )
        return binding


class OdooPickingMapper(Component):
    _name = "odoo.stock.picking.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.stock.picking"

    direct = [("name", "name"), ("origin", "origin"), ("state", "backend_state")]

    def _get_external_picking_type(self, record):
        """Return a normalized picking type code from external picking."""
        picking_type = False
        for field_name in ("picking_type_code", "type"):
            value = getattr(record, field_name, False)
            if value and not callable(value):
                picking_type = value
                break

        if (
            not picking_type
            and getattr(record, "picking_type_id", False)
            and not callable(record.picking_type_id)
        ):
            code = getattr(record.picking_type_id, "code", False)
            if code and not callable(code):
                picking_type = code

        if isinstance(picking_type, str):
            return picking_type.strip().lower()
        return False

    def _get_local_picking_fallback(self, record):
        """Find an existing local picking by exact name/origin."""
        if getattr(record, "name", False):
            local_pickings = self.env["stock.picking"].search(
                [("name", "=", record.name)], limit=2
            )
            if len(local_pickings) == 1:
                return local_pickings
        if getattr(record, "origin", False):
            local_pickings = self.env["stock.picking"].search(
                [("origin", "=", record.origin)], limit=2
            )
            if len(local_pickings) == 1:
                return local_pickings
        return self.env["stock.picking"]

    def _get_sale_picking_type_fallback(self, record, picking_type):
        """Fallback picking type from already imported local sale pickings."""
        if not getattr(record, "sale_id", False):
            return self.env["stock.picking.type"]

        sale_binding = self.binder_for("odoo.sale.order").to_internal(
            record.sale_id.id, unwrap=True
        )
        if not sale_binding:
            return self.env["stock.picking.type"]

        sale_pickings = sale_binding.picking_ids
        if getattr(record, "name", False):
            named = sale_pickings.filtered(lambda p: p.name == record.name)
            if len(named) == 1:
                return named.picking_type_id
        if getattr(record, "origin", False):
            origin = sale_pickings.filtered(lambda p: p.origin == record.origin)
            if len(origin) == 1:
                return origin.picking_type_id
        if picking_type:
            by_code = sale_pickings.filtered(
                lambda p: p.picking_type_id.code == picking_type
            )
            if len(by_code) == 1:
                return by_code.picking_type_id
        return self.env["stock.picking.type"]

    def _get_local_picking_type_fallback(
        self, picking_type, source_location, dest_location, warehouse_id=False
    ):
        """Fallback to a unique local picking type when mapping table has no hit."""
        if not picking_type:
            return self.env["stock.picking.type"]

        picking_types = self.env["stock.picking.type"].search([("code", "=", picking_type)])
        if warehouse_id:
            picking_types = picking_types.filtered(
                lambda pt: pt.warehouse_id == warehouse_id
            )
        if len(picking_types) == 1:
            return picking_types

        if source_location:
            picking_types = picking_types.filtered(
                lambda pt: pt.default_location_src_id.usage == source_location.usage
            )
        if len(picking_types) == 1:
            return picking_types

        if dest_location:
            picking_types = picking_types.filtered(
                lambda pt: pt.default_location_dest_id.usage == dest_location.usage
            )
        if len(picking_types) == 1:
            return picking_types

        return self.env["stock.picking.type"]

    def _get_any_local_picking_type_fallback(self, picking_type):
        """Last-resort fallback: pick one local picking type by code."""
        if not picking_type:
            # Absolute fallback to keep import non-blocking.
            return self.env["stock.picking.type"].search([], order="sequence, id", limit=1)

        # 1) Try current company first.
        company = self.env.user.company_id
        picking_types = self.env["stock.picking.type"].search(
            [("code", "=", picking_type), ("company_id", "in", [False, company.id])],
            order="warehouse_id, sequence, id",
            limit=1,
        )
        # 2) Fallback to any company.
        if not picking_types:
            picking_types = self.env["stock.picking.type"].search(
                [("code", "=", picking_type)],
                order="company_id, warehouse_id, sequence, id",
                limit=1,
            )
        # 3) Absolute fallback to first available picking type.
        if not picking_types:
            picking_types = self.env["stock.picking.type"].search(
                [], order="company_id, warehouse_id, sequence, id", limit=1
            )
        if picking_types:
            _logger.warning(
                "Using last-resort local picking type fallback for code %s: %s (%s)",
                picking_type,
                picking_types.display_name,
                picking_types.id,
            )
        return picking_types

    @mapping
    def odoo_id(self, record):
        local_picking = self._get_local_picking_fallback(record)
        if local_picking:
            return {"odoo_id": local_picking.id}
        if record.sale_id and record.move_lines:
            binder = self.binder_for("odoo.stock.picking")
            picking_id = binder.to_internal(record.id, unwrap=True)
            if picking_id:
                return {"odoo_id": picking_id.id}
            else:
                # If picking is created when changing state importing sale order
                binder = self.binder_for("odoo.sale.order")
                sale_id = binder.to_internal(record.sale_id.id, unwrap=True)
                move_id = False
                for move in record.move_lines:
                    move_id = move
                    break
                existing_picking_id = self.env["stock.picking"]
                try:
                    picking_type_id = self.get_picking_type_from_external_locations(
                        "picking", record, move_id.location_id, move_id.location_dest_id
                    )
                    existing_picking_id = sale_id.picking_ids.filtered(
                        lambda x: x.picking_type_id == picking_type_id
                    )
                except ValidationError:
                    if getattr(record, "name", False):
                        existing_picking_id = sale_id.picking_ids.filtered(
                            lambda x: x.name == record.name
                        )
                    if not existing_picking_id and getattr(record, "origin", False):
                        existing_picking_id = sale_id.picking_ids.filtered(
                            lambda x: x.origin == record.origin
                        )
                if existing_picking_id:
                    return {"odoo_id": existing_picking_id.id}
        return {}

    def get_picking_type_from_external_locations(
        self, model_label, record, location_id, location_dest_id
    ):
        binder = self.binder_for("odoo.stock.location")
        source_location = binder.to_internal(location_id.id, unwrap=True)
        dest_location = binder.to_internal(location_dest_id.id, unwrap=True)
        warehouse_id = source_location.warehouse_id or dest_location.warehouse_id
        picking_type = self._get_external_picking_type(record)
        warehouse_ref = warehouse_id.id if warehouse_id else False
        warehouse_name = warehouse_id.name if warehouse_id else False

        domain = [("type", "=", picking_type)]
        if warehouse_id:
            domain.append(("warehouse_id.odoo_id.id", "=", warehouse_id.id))
        picking_type_mapping_candidates = self.env["openerp.picking.type"].search(domain)
        picking_type_mapping_id = picking_type_mapping_candidates
        if len(picking_type_mapping_id) != 1 and source_location:
            picking_type_mapping_id = picking_type_mapping_id.filtered(
                lambda x: x.origin_location_usage == source_location.usage
            )
        if len(picking_type_mapping_id) != 1 and dest_location:
            picking_type_mapping_id = picking_type_mapping_id.filtered(
                lambda x: x.dest_location_usage == dest_location.usage
            )
        # If usage-based filtering removed all candidates but there is a single
        # mapping for the resolved type(+warehouse), use it as safe fallback.
        if not picking_type_mapping_id and len(picking_type_mapping_candidates) == 1:
            picking_type_mapping_id = picking_type_mapping_candidates

        if not picking_type_mapping_id:
            fallback_picking_type_id = self._get_sale_picking_type_fallback(
                record, picking_type
            )
            if fallback_picking_type_id:
                return fallback_picking_type_id
            fallback_picking_type_id = self._get_local_picking_type_fallback(
                picking_type, source_location, dest_location, warehouse_id
            )
            if fallback_picking_type_id:
                return fallback_picking_type_id
            fallback_picking_type_id = self._get_any_local_picking_type_fallback(
                picking_type
            )
            if fallback_picking_type_id:
                return fallback_picking_type_id
            raise ValidationError(
                _(
                    "No local or mapped picking type found for warehouse {}-{} "
                    "and type {} from {} {}-{}."
                ).format(
                    warehouse_ref,
                    warehouse_name,
                    picking_type,
                    model_label,
                    record["id"],
                    record["name"],
                )
            )
        if len(picking_type_mapping_id) > 1:
            fallback_picking_type_id = self._get_any_local_picking_type_fallback(
                picking_type
            )
            if fallback_picking_type_id:
                return fallback_picking_type_id
            # Deterministic fallback to keep import non-blocking.
            return picking_type_mapping_id.sorted("id")[0].picking_type_id
        return picking_type_mapping_id.picking_type_id

    @mapping
    def picking_type_id(self, record):
        picking_binder = self.binder_for("odoo.stock.picking").to_internal(record["id"])
        if picking_binder:
            return {}
        local_picking = self._get_local_picking_fallback(record)
        if local_picking:
            return {}
        if len(record["move_lines"]) <= 0:
            return {}
        for move in record["move_lines"]:
            move_id = move
            break
        picking_type_id = self.get_picking_type_from_external_locations(
            "picking", record, move_id.location_id, move_id.location_dest_id
        )
        return {"picking_type_id": picking_type_id.id}

    @mapping
    def location_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        location_id = False
        move_id = list(record["move_lines"])[0]
        location_id = binder.to_internal(move_id.location_id.id, unwrap=True)
        return {"location_id": location_id.id}

    @mapping
    def location_dest_id(self, record):
        binder = self.binder_for("odoo.stock.location")
        move_id = list(record["move_lines"])[0]
        location_dest_id = binder.to_internal(move_id.location_dest_id.id, unwrap=True)
        return {"location_dest_id": location_dest_id.id}

    @mapping
    def partner_id(self, record):
        if record["partner_id"]:
            binder = self.binder_for("odoo.res.partner")
            partner_id = binder.to_internal(record["partner_id"].id, unwrap=True)
            return {"partner_id": partner_id.id if partner_id else False}
