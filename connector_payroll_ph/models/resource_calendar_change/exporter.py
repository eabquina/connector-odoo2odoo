import ast
import logging

from odoo import fields

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchResourceCalendarChangeExporter(Component):
    _name = "odoo.resource.calendar.change.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.resource.calendar.change"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        filters = list(filters or [])
        loc_filter = ast.literal_eval(
            self.backend_record.local_domain_filter_resource_calendar_change or "[]"
        )
        filters += loc_filter or []

        records = self.env["resource.calendar.change"].search(filters)
        for rec in records:
            binding = rec.bind_ids.filtered(lambda b: b.backend_id == self.backend_record)
            if not binding:
                binding = self.env["odoo.resource.calendar.change"].with_context(
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

            job_options = {"priority": 20, "max_retries": 0}
            self._export_record(binding, job_options=job_options)


class ResourceCalendarChangeExporter(Component):
    _name = "odoo.resource.calendar.change.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.resource.calendar.change"]

    def _export_dependencies(self):
        if self.binding.employee_id:
            self._export_dependency(
                self._get_or_create_binding(self.binding.employee_id, "odoo.hr.employee"),
                "odoo.hr.employee",
            )
        if self.binding.type_id:
            self._export_dependency(
                self._get_or_create_binding(
                    self.binding.type_id, "odoo.resource.calendar.change.type"
                ),
                "odoo.resource.calendar.change.type",
            )

    def _get_or_create_binding(self, record, binding_model):
        binding = record.bind_ids.filtered(lambda b: b.backend_id == self.backend_record)
        if binding:
            return binding[0]
        return self.env[binding_model].with_context(connector_no_export=True).create(
            {"odoo_id": record.id, "external_id": 0, "backend_id": self.backend_record.id}
        )

    def _after_export(self):
        super()._after_export()
        if not getattr(self.binding, "change_lines", False):
            return
        for line in self.binding.change_lines:
            binding_line = line.bind_ids.filtered(
                lambda b: b.backend_id == self.backend_record
            )
            if not binding_line:
                binding_line = self.env[
                    "odoo.resource.calendar.change.lines"
                ].with_context(connector_no_export=True).create(
                    {
                        "odoo_id": line.id,
                        "external_id": 0,
                        "backend_id": self.backend_record.id,
                    }
                )
            else:
                binding_line = binding_line[0]
            binding_line.with_delay(priority=25, max_retries=0).export_record(
                self.backend_record
            )


class ResourceCalendarChangeExportMapper(Component):
    _name = "odoo.resource.calendar.change.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.resource.calendar.change"]

    direct = [
        ("duration", "duration"),
        ("purpose", "purpose"),
        ("cancel_reason", "cancel_reason"),
        ("state", "state"),
        ("current_user_boolean", "current_user_boolean"),
    ]

    @mapping
    def employee_id(self, record):
        if not record.employee_id:
            return {}
        binder = self.binder_for("odoo.hr.employee")
        return {"employee_id": binder.to_external(record.employee_id, wrap=True)}

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
    def name(self, record):
        if not record.name:
            return {}
        return {"name": record.name}

    @mapping
    def date_from(self, record):
        if not record.date_from:
            return {}
        return {"date_from": fields.Date.to_string(record.date_from)}

    @mapping
    def date_to(self, record):
        if not record.date_to:
            return {}
        return {"date_to": fields.Date.to_string(record.date_to)}

    @only_create
    @mapping
    def external_id(self, record):
        if not record.name:
            return {}
        adapter = self.component(usage="record.exporter").backend_adapter
        ext_ids = adapter.search([("name", "=", record.name)], limit=1)
        if ext_ids:
            return {"external_id": ext_ids[0]}
        return {}
