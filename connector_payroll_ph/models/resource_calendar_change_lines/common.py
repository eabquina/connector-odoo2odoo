import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooResourceCalendarChangeLines(models.Model):
    _name = "odoo.resource.calendar.change.lines"
    _inherit = "odoo.binding"
    _inherits = {"resource.calendar.change.lines": "odoo_id"}
    _description = "External Odoo Work Schedule Change Request Line"

    odoo_id = fields.Many2one(
        comodel_name="resource.calendar.change.lines",
        string="Work Schedule Change Request Line",
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


class ResourceCalendarChangeLines(models.Model):
    _inherit = "resource.calendar.change.lines"

    bind_ids = fields.One2many(
        comodel_name="odoo.resource.calendar.change.lines",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class ResourceCalendarChangeLinesAdapter(Component):
    _name = "odoo.resource.calendar.change.lines.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.resource.calendar.change.lines"

    _odoo_model = "resource.calendar.change.lines"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(
                self.backend_record.external_domain_filter_resource_calendar_change_lines
                or "[]"
            )
        )
        filters += ext_filter or []
        return super().search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class ResourceCalendarChangeLinesListener(Component):
    _name = "resource.calendar.change.lines.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["resource.calendar.change.lines"]
    _usage = "event.listener"
