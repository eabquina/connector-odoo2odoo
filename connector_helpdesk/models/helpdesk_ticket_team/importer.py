# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchTeamImporter(Component):
    """Import the Odoo Helpdesk Ticket Teams.

    For every team in the list, a delayed job is created.
    """

    _name = "odoo.helpdesk.ticket.team.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.helpdesk.ticket.team"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo helpdesk.ticket.team %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            self._import_record(external_id, force=force)


class TeamImportMapper(Component):
    _name = "odoo.helpdesk.ticket.team.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.helpdesk.ticket.team"]

    direct = [
        ("name", "name"),
        ("active", "active"),
        ("color", "color"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """Bind to an existing local team when name already exists."""
        binder = self.binder_for("odoo.helpdesk.ticket.team")
        local = binder.to_internal(record.id, unwrap=True)
        if local:
            return {"odoo_id": local.id}

        if not getattr(record, "name", False):
            return {}

        local = self.env["helpdesk.ticket.team"].search(
            [("name", "=", record.name)], limit=1
        )
        if local:
            return {"odoo_id": local.id}
        return {}

    @mapping
    def category_ids(self, record):
        """Map category_ids Many2many from v13 to v18."""
        if not getattr(record, "category_ids", False):
            return {}
        binder = self.binder_for("odoo.helpdesk.ticket.category")
        category_ids = []
        raw_ids = (
            record.category_ids.ids
            if hasattr(record.category_ids, "ids")
            else record.category_ids
        )
        for cat_id in raw_ids:
            local = binder.to_internal(cat_id, unwrap=True)
            if local:
                category_ids.append(local.id)
        if category_ids:
            return {"category_ids": [(6, 0, category_ids)]}
        return {}

    @mapping
    def user_id(self, record):
        """Map team leader - match by login."""
        if not getattr(record, "user_id", False):
            return {}
        remote_user_id = (
            record.user_id.id
            if hasattr(record.user_id, "id")
            else record.user_id
        )
        if not remote_user_id:
            return {}
        try:
            remote_user = self.backend_adapter.read(
                remote_user_id, ["login"], model="res.users"
            )
            if remote_user and remote_user.get("login"):
                local_user = self.env["res.users"].search(
                    [("login", "=", remote_user["login"])], limit=1
                )
                if local_user:
                    return {"user_id": local_user.id}
        except Exception:
            _logger.warning(
                "Could not resolve team leader for external user ID %s",
                remote_user_id,
            )
        return {}


class TeamImporter(Component):
    _name = "odoo.helpdesk.ticket.team.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.helpdesk.ticket.team"]

    def _import_dependencies(self, force=False):
        """Import category dependencies before importing the team."""
        _logger.info(
            "Importing dependencies for helpdesk team external ID %s",
            self.external_id,
        )
        record = self.odoo_record
        if getattr(record, "category_ids", False):
            cat_ids = (
                record.category_ids.ids
                if hasattr(record.category_ids, "ids")
                else record.category_ids
            )
            for cat_id in cat_ids:
                self._import_dependency(
                    cat_id, "odoo.helpdesk.ticket.category", force=force
                )
        return super()._import_dependencies(force=force)

    def _after_import(self, binding, force=False):
        return super()._after_import(binding, force)
