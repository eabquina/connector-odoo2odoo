import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooResourceCalendarChange(models.Model):
    _name = "odoo.resource.calendar.change"
    _inherit = "odoo.binding"
    _inherits = {"resource.calendar.change": "odoo_id"}
    _description = "External Odoo Work Schedule Change Request"

    odoo_id = fields.Many2one(
        comodel_name="resource.calendar.change",
        string="Work Schedule Change Request",
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

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.odoo_id.display_name} (Backend: {rec.backend_id.display_name})"

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        return self.with_delay().import_record(
            self.backend_id, self.external_id, force=True
        )


class ResourceCalendarChange(models.Model):
    _inherit = "resource.calendar.change"

    bind_ids = fields.One2many(
        comodel_name="odoo.resource.calendar.change",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class ResourceCalendarChangeAdapter(Component):
    _name = "odoo.resource.calendar.change.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.resource.calendar.change"

    _odoo_model = "resource.calendar.change"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_domain_filter_resource_calendar_change or "[]")
        )
        filters += ext_filter or []
        return super().search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class ResourceCalendarChangeListener(Component):
    _name = "resource.calendar.change.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["resource.calendar.change"]
    _usage = "event.listener"
