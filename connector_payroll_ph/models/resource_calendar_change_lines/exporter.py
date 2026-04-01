import ast
import logging

from odoo import fields

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchResourceCalendarChangeLinesExporter(Component):
    _name = "odoo.resource.calendar.change.lines.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.resource.calendar.change.lines"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        filters = list(filters or [])
        loc_filter = ast.literal_eval(
            self.backend_record.local_domain_filter_resource_calendar_change_lines or "[]"
        )
        filters += loc_filter or []

        records = self.env["resource.calendar.change.lines"].search(filters)
        for rec in records:
            binding = rec.bind_ids.filtered(lambda b: b.backend_id == self.backend_record)
            if not binding:
                binding = self.env["odoo.resource.calendar.change.lines"].with_context(
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

            job_options = {"priority": 25, "max_retries": 0}
            self._export_record(binding, job_options=job_options)


class ResourceCalendarChangeLinesExporter(Component):
    _name = "odoo.resource.calendar.change.lines.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.resource.calendar.change.lines"]

    def _export_dependencies(self):
        if self.binding.request_id:
            req_binding = self._get_or_create_binding(
                self.binding.request_id, "odoo.resource.calendar.change"
            )
            self._export_dependency(req_binding, "odoo.resource.calendar.change")
        if self.binding.type_id:
            type_binding = self._get_or_create_binding(
                self.binding.type_id, "odoo.resource.calendar.change.type"
            )
            self._export_dependency(
                type_binding, "odoo.resource.calendar.change.type"
            )

    def _get_or_create_binding(self, record, binding_model):
        binding = record.bind_ids.filtered(lambda b: b.backend_id == self.backend_record)
        if binding:
            return binding[0]
        return self.env[binding_model].with_context(connector_no_export=True).create(
            {"odoo_id": record.id, "external_id": 0, "backend_id": self.backend_record.id}
        )


class ResourceCalendarChangeLinesExportMapper(Component):
    _name = "odoo.resource.calendar.change.lines.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.resource.calendar.change.lines"]

    direct = [
        ("reason", "reason"),
    ]

    @mapping
    def request_id(self, record):
        if not record.request_id:
            return {}
        binder = self.binder_for("odoo.resource.calendar.change")
        return {"request_id": binder.to_external(record.request_id, wrap=True)}

    @mapping
    def type_id(self, record):
        if not record.type_id:
            return {}
        binder = self.binder_for("odoo.resource.calendar.change.type")
        return {"type_id": binder.to_external(record.type_id, wrap=True)}

    @mapping
    def calendar_to(self, record):
        if not record.calendar_to:
            return {}
        odoo_api = self.work.odoo_api.api
        cal_model = odoo_api.env["resource.calendar"]
        ext_ids = cal_model.search([("name", "=", record.calendar_to.name)], limit=1)
        if not ext_ids:
            raise ValueError(
                "External resource.calendar not found: %s" % record.calendar_to.name
            )
        return {"calendar_to": ext_ids[0]}

    @mapping
    def date(self, record):
        if not record.date:
            return {}
        return {"date": fields.Date.to_string(record.date)}

    @only_create
    @mapping
    def external_id(self, record):
        if not record.request_id or not record.date:
            return {}
        binder = self.binder_for("odoo.resource.calendar.change")
        ext_request_id = binder.to_external(record.request_id, wrap=True)
        if not ext_request_id:
            return {}

        adapter = self.component(usage="record.exporter").backend_adapter
        ext_ids = adapter.search(
            [
                ("request_id", "=", ext_request_id),
                ("date", "=", fields.Date.to_string(record.date)),
            ],
            limit=1,
        )
        if ext_ids:
            return {"external_id": ext_ids[0]}
        return {}
