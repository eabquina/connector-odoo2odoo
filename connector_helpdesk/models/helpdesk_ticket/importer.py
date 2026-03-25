# Copyright 2024 Tech Ops PH, EL Abquina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchTicketImporter(Component):
    """Import the Odoo Helpdesk Tickets.

    For every ticket in the list, a delayed job is created.
    """

    _name = "odoo.helpdesk.ticket.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.helpdesk.ticket"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo helpdesk.ticket %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            self._import_record(external_id, force=force)


class TicketImportMapper(Component):
    _name = "odoo.helpdesk.ticket.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.helpdesk.ticket"]

    direct = [
        ("name", "name"),
        ("priority", "priority"),
        ("partner_name", "partner_name"),
        ("partner_email", "partner_email"),
        ("color", "color"),
        ("active", "active"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """Bind to an existing local ticket when number already exists."""
        binder = self.binder_for("odoo.helpdesk.ticket")
        local = binder.to_internal(record.id, unwrap=True)
        if local:
            return {"odoo_id": local.id}

        number = getattr(record, "number", False)
        if number and number != "/":
            local = self.env["helpdesk.ticket"].search(
                [("number", "=", number)], limit=1
            )
            if local:
                return {"odoo_id": local.id}
        return {}

    @mapping
    def description(self, record):
        return {"description": getattr(record, "description", "") or "No description"}

    @mapping
    def stage_id(self, record):
        if not getattr(record, "stage_id", False):
            return {}
        stage_id = (
            record.stage_id.id
            if hasattr(record.stage_id, "id")
            else record.stage_id
        )
        if not stage_id:
            return {}
        binder = self.binder_for("odoo.helpdesk.ticket.stage")
        local = binder.to_internal(stage_id, unwrap=True)
        if local:
            return {"stage_id": local.id}
        return {}

    @mapping
    def team_id(self, record):
        if not getattr(record, "team_id", False):
            return {}
        team_id = (
            record.team_id.id
            if hasattr(record.team_id, "id")
            else record.team_id
        )
        if not team_id:
            return {}
        binder = self.binder_for("odoo.helpdesk.ticket.team")
        local = binder.to_internal(team_id, unwrap=True)
        if local:
            return {"team_id": local.id}
        return {}

    @mapping
    def category_id(self, record):
        if not getattr(record, "category_id", False):
            return {}
        cat_id = (
            record.category_id.id
            if hasattr(record.category_id, "id")
            else record.category_id
        )
        if not cat_id:
            return {}
        binder = self.binder_for("odoo.helpdesk.ticket.category")
        local = binder.to_internal(cat_id, unwrap=True)
        if local:
            return {"category_id": local.id}
        return {}

    @mapping
    def channel_id(self, record):
        if not getattr(record, "channel_id", False):
            return {}
        ch_id = (
            record.channel_id.id
            if hasattr(record.channel_id, "id")
            else record.channel_id
        )
        if not ch_id:
            return {}
        binder = self.binder_for("odoo.helpdesk.ticket.channel")
        local = binder.to_internal(ch_id, unwrap=True)
        if local:
            return {"channel_id": local.id}
        return {}

    @mapping
    def tag_ids(self, record):
        """Map tag_ids Many2many from v13 to v18."""
        if not getattr(record, "tag_ids", False):
            return {}
        binder = self.binder_for("odoo.helpdesk.ticket.tag")
        tag_ids = []
        raw_ids = (
            record.tag_ids.ids
            if hasattr(record.tag_ids, "ids")
            else record.tag_ids
        )
        for tag_id in raw_ids:
            local = binder.to_internal(tag_id, unwrap=True)
            if local:
                tag_ids.append(local.id)
        if tag_ids:
            return {"tag_ids": [(6, 0, tag_ids)]}
        return {}

    @mapping
    def partner_id(self, record):
        """Map partner_id - resolve via res.partner binding."""
        if not getattr(record, "partner_id", False):
            return {}
        partner_id = (
            record.partner_id.id
            if hasattr(record.partner_id, "id")
            else record.partner_id
        )
        if not partner_id:
            return {}
        binder = self.binder_for("odoo.res.partner")
        local = binder.to_internal(partner_id, unwrap=True)
        if local:
            return {"partner_id": local.id}
        return {}

    @mapping
    def user_id(self, record):
        """Map assigned user - match by login."""
        if not getattr(record, "user_id", False):
            return {}
        user_id = (
            record.user_id.id
            if hasattr(record.user_id, "id")
            else record.user_id
        )
        if not user_id:
            return {}
        try:
            remote_user = self.backend_adapter.read(
                user_id, ["login"], model="res.users"
            )
            if remote_user and remote_user.get("login"):
                local_user = self.env["res.users"].search(
                    [("login", "=", remote_user["login"])], limit=1
                )
                if local_user:
                    return {"user_id": local_user.id}
        except Exception:
            _logger.warning(
                "Could not resolve assigned user for external user ID %s",
                user_id,
            )
        return {}

    @mapping
    def dates(self, record):
        """Map date fields from v13 to v18."""
        vals = {}
        for field in ("last_stage_update", "assigned_date", "closed_date"):
            val = getattr(record, field, False)
            if val:
                vals[field] = val
        return vals

    @mapping
    def kanban_state(self, record):
        val = getattr(record, "kanban_state", False)
        if val:
            return {"kanban_state": val}
        return {}


class TicketImporter(Component):
    _name = "odoo.helpdesk.ticket.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.helpdesk.ticket"]

    def _import_dependencies(self, force=False):
        """Import all dependencies before importing the ticket."""
        _logger.info(
            "Importing dependencies for helpdesk ticket external ID %s",
            self.external_id,
        )
        record = self.odoo_record

        # Import stage dependency
        if getattr(record, "stage_id", False):
            stage_id = (
                record.stage_id.id
                if hasattr(record.stage_id, "id")
                else record.stage_id
            )
            if stage_id:
                self._import_dependency(
                    stage_id, "odoo.helpdesk.ticket.stage", force=force
                )

        # Import team dependency
        if getattr(record, "team_id", False):
            team_id = (
                record.team_id.id
                if hasattr(record.team_id, "id")
                else record.team_id
            )
            if team_id:
                self._import_dependency(
                    team_id, "odoo.helpdesk.ticket.team", force=force
                )

        # Import category dependency
        if getattr(record, "category_id", False):
            cat_id = (
                record.category_id.id
                if hasattr(record.category_id, "id")
                else record.category_id
            )
            if cat_id:
                self._import_dependency(
                    cat_id, "odoo.helpdesk.ticket.category", force=force
                )

        # Import channel dependency
        if getattr(record, "channel_id", False):
            ch_id = (
                record.channel_id.id
                if hasattr(record.channel_id, "id")
                else record.channel_id
            )
            if ch_id:
                self._import_dependency(
                    ch_id, "odoo.helpdesk.ticket.channel", force=force
                )

        # Import tag dependencies
        if getattr(record, "tag_ids", False):
            tag_ids = (
                record.tag_ids.ids
                if hasattr(record.tag_ids, "ids")
                else record.tag_ids
            )
            for tag_id in tag_ids:
                self._import_dependency(
                    tag_id, "odoo.helpdesk.ticket.tag", force=force
                )

        # Import partner dependency
        if getattr(record, "partner_id", False):
            partner_id = (
                record.partner_id.id
                if hasattr(record.partner_id, "id")
                else record.partner_id
            )
            if partner_id:
                self._import_dependency(
                    partner_id, "odoo.res.partner", force=force
                )

        return super()._import_dependencies(force=force)

    def _after_import(self, binding, force=False):
        return super()._after_import(binding, force)
