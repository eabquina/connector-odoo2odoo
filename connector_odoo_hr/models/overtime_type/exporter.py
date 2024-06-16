# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchHrOvertimeTypeExporter(Component):
    _name = "odoo.overtime.type.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.overtime.type"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        filters += [("backend_id", "=", self.backend_record.id)]
        prod_ids = self.env["odoo.overtime.type"].search(filters)
        for prod in prod_ids:
            job_options = {
                "max_retries": 0,
                "priority": 5 + prod.odoo_id.parent_id,
            }
            self._export_record(prod, job_options=job_options)


class OdooHrOvertimeTypeExporter(Component):
    _name = "odoo.overtime.type.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.overtime.type"]

    def _export_dependencies(self):
        if not self.binding.parent_id:
            return
        parents = self.binding.parent_id.bind_ids
        parent = self.env["odoo.hr.employee"]

        if parents:
            parent = parents.filtered(lambda c: c.backend_id == self.backend_record)

            employee = self.binder.to_external(parent, wrap=False)
            self._export_dependency(employee, "odoo.hr.employee")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = map_record.values(for_create=True, fields=fields, **kwargs)
        return datas


class ProductExportCategoryMapper(Component):
    _name = "odoo.overtime.type.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.overtime.type"]

    direct = [
        ("display_name", "display_name"),
        ("name", "name"),
        ("duration_type", "duration_type"),
        ("type", "type"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        categ_ids = []
        domain = [("name", "=", record["name"])]
        adapter = self.component(usage="record.exporter").backend_adapter
        categ_ids = adapter.search(domain)
        if len(categ_ids) == 1:
            return {"external_id": categ_ids[0]}
        return {}