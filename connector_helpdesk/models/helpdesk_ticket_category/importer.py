# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchCategoryImporter(Component):
    """Import the Odoo Helpdesk Ticket Categories.

    For every category in the list, a delayed job is created.
    """

    _name = "odoo.helpdesk.ticket.category.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.helpdesk.ticket.category"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo helpdesk.ticket.category %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            self._import_record(external_id, force=force)


class CategoryImportMapper(Component):
    _name = "odoo.helpdesk.ticket.category.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.helpdesk.ticket.category"]

    direct = [
        ("name", "name"),
        ("active", "active"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """Bind to an existing local category when name already exists."""
        binder = self.binder_for("odoo.helpdesk.ticket.category")
        local = binder.to_internal(record.id, unwrap=True)
        if local:
            return {"odoo_id": local.id}

        if not getattr(record, "name", False):
            return {}

        local = self.env["helpdesk.ticket.category"].search(
            [("name", "=", record.name)], limit=1
        )
        if local:
            return {"odoo_id": local.id}
        return {}


class CategoryImporter(Component):
    _name = "odoo.helpdesk.ticket.category.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.helpdesk.ticket.category"]

    def _import_dependencies(self, force=False):
        _logger.info(
            "Importing dependencies for helpdesk category external ID %s",
            self.external_id,
        )
        return super()._import_dependencies(force=force)

    def _after_import(self, binding, force=False):
        return super()._after_import(binding, force)
