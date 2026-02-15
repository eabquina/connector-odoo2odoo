import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchResourceCalendarChangeTypeExporter(Component):
    _name = "odoo.resource.calendar.change.type.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.resource.calendar.change.type"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        filters = list(filters or [])
        loc_filter = ast.literal_eval(
            self.backend_record.local_domain_filter_resource_calendar_change_type or "[]"
        )
        filters += loc_filter or []

        records = self.env["resource.calendar.change.type"].search(filters)
        for rec in records:
            binding = rec.bind_ids.filtered(lambda b: b.backend_id == self.backend_record)
            if not binding:
                binding = self.env["odoo.resource.calendar.change.type"].with_context(
                    connector_no_export=True
                ).create(
                    {
                        "odoo_id": rec.id,
                        "external_id": 0,
                        "backend_id": self.backend_record.id,
                    }
                )
            else:
                binding = binding[0]

            job_options = {"priority": 15, "max_retries": 0}
            self._export_record(binding, job_options=job_options)


class ResourceCalendarChangeTypeExporter(Component):
    _name = "odoo.resource.calendar.change.type.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.resource.calendar.change.type"]


class ResourceCalendarChangeTypeExportMapper(Component):
    _name = "odoo.resource.calendar.change.type.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.resource.calendar.change.type"]

    direct = [
        ("name", "name"),
        ("code", "code"),
    ]

    @only_create
    @mapping
    def external_id(self, record):
        if not record.code:
            return {}
        adapter = self.component(usage="record.exporter").backend_adapter
        ext_ids = adapter.search([("code", "=", record.code)])
        if ext_ids:
            return {"external_id": ext_ids[0]}
        return {}
