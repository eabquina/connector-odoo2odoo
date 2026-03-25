# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchTagImporter(Component):
    """Import the Odoo Helpdesk Ticket Tags.

    For every tag in the list, a delayed job is created.
    """

    _name = "odoo.helpdesk.ticket.tag.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.helpdesk.ticket.tag"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo helpdesk.ticket.tag %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            self._import_record(external_id, force=force)


class TagImportMapper(Component):
    _name = "odoo.helpdesk.ticket.tag.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.helpdesk.ticket.tag"]

    direct = [
        ("name", "name"),
        ("color", "color"),
        ("active", "active"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """Bind to an existing local tag when name already exists."""
        binder = self.binder_for("odoo.helpdesk.ticket.tag")
        local = binder.to_internal(record.id, unwrap=True)
        if local:
            return {"odoo_id": local.id}

        if not getattr(record, "name", False):
            return {}

        local = self.env["helpdesk.ticket.tag"].search(
            [("name", "=", record.name)], limit=1
        )
        if local:
            return {"odoo_id": local.id}
        return {}


class TagImporter(Component):
    _name = "odoo.helpdesk.ticket.tag.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.helpdesk.ticket.tag"]

    def _import_dependencies(self, force=False):
        _logger.info(
            "Importing dependencies for helpdesk tag external ID %s",
            self.external_id,
        )
        return super()._import_dependencies(force=force)

    def _after_import(self, binding, force=False):
        return super()._after_import(binding, force)
