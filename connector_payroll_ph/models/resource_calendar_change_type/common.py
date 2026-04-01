import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooResourceCalendarChangeType(models.Model):
    _name = "odoo.resource.calendar.change.type"
    _inherit = "odoo.binding"
    _inherits = {"resource.calendar.change.type": "odoo_id"}
    _description = "External Odoo Work Schedule Change Type"

    odoo_id = fields.Many2one(
        comodel_name="resource.calendar.change.type",
        string="Work Schedule Change Type",
        required=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        return self.with_delay().import_record(
            self.backend_id, self.external_id, force=True
        )


class ResourceCalendarChangeType(models.Model):
    _inherit = "resource.calendar.change.type"

    bind_ids = fields.One2many(
        comodel_name="odoo.resource.calendar.change.type",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class ResourceCalendarChangeTypeAdapter(Component):
    _name = "odoo.resource.calendar.change.type.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.resource.calendar.change.type"

    _odoo_model = "resource.calendar.change.type"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(
                self.backend_record.external_domain_filter_resource_calendar_change_type
                or "[]"
            )
        )
        filters += ext_filter or []
        return super().search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class ResourceCalendarChangeTypeListener(Component):
    _name = "resource.calendar.change.type.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["resource.calendar.change.type"]
    _usage = "event.listener"
