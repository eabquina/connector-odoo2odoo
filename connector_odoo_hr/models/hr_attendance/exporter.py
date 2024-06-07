# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

# from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class BatchPartnerExporter(Component):
    _name = "odoo.hr.attendance.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.hr.attendance"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        loc_filter = ast.literal_eval(self.backend_record.local_partner_domain_filter)
        filters += loc_filter
        employee_ids = self.env["hr.attendance"].search(filters)

        o_ids = self.env["odoo.hr.attendance"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        o_employee_ids = self.env["hr.attendance"].search(
            [("id", "in", [o.odoo_id.id for o in o_ids])]
        )
        to_bind = employee_ids - o_employee_ids

        for p in to_bind:
            self.env["odoo.hr.attendance"].create(
                {
                    "odoo_id": p.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )

        bind_ids = self.env["odoo.hr.attendance"].search(
            [
                ("odoo_id", "in", [p.id for p in employee_ids]),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        for partner in bind_ids:
            job_options = {"max_retries": 0, "priority": 15}
            self._export_record(partner, job_options=job_options)


class OdooPartnerExporter(Component):
    _name = "odoo.hr.attendance.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.hr.attendance"]

    def _export_dependencies(self):
        if not self.binding.parent_id:
            return
        parents = self.binding.parent_id.bind_ids
        parent = self.env["odoo.hr.attendance"]

        if parents:
            parent = parents.filtered(lambda c: c.backend_id == self.backend_record)

            partner = self.binder.to_external(parent, wrap=False)
            self._export_dependency(partner, "odoo.hr.attendance")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = map_record.values(for_create=True, fields=fields, **kwargs)
        return datas


class PartnerExportMapper(Component):
    _name = "odoo.hr.attendance.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.hr.attendance"]

    direct = [
        ("name", "name"),
        ("street", "street"),
        ("street2", "street2"),
        ("city", "city"),
        ("website", "website"),
        ("phone", "phone"),
        ("mobile", "mobile"),
        ("email", "email"),
    ]

    def get_partner_by_match_field(self, record):
        match_field = "email"
        filters = []

        if self.backend_record.matching_customer:
            match_field = self.backend_record.matching_customer_ch

        filters = ast.literal_eval(self.backend_record.external_partner_domain_filter)
        if record[match_field]:
            filters.append((match_field, "=", record[match_field]))
        filters.append("|")
        filters.append(("active", "=", False))
        filters.append(("active", "=", True))

        adapter = self.component(usage="record.exporter").backend_adapter
        partner = adapter.search(filters)
        if len(partner) == 1:
            return partner[0]

        return False

    @mapping
    def customer(self, record):
        return {"customer": True}

    @mapping
    def supplier(self, record):
        return {"supplier": True}

    @only_create
    @mapping
    def odoo_id(self, record):
        external_id = self.get_partner_by_match_field(record)

        if external_id:
            return {"external_id": external_id}
