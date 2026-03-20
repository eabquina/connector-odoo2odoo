# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class AccountTaxGroupBatchImporter(Component):
    _name = "odoo.account.tax.group.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.account.tax.group"]

    def run(self, filters=None, force=False):
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo account tax groups %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 10}
            self._import_record(external_id, job_options=job_options, force=force)


class AccountTaxGroupImporter(Component):
    _name = "odoo.account.tax.group.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.account.tax.group"]


class AccountTaxGroupImportMapper(Component):
    _name = "odoo.account.tax.group.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.tax.group"

    direct = [
        ("name", "name"),
        ("sequence", "sequence"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        name = getattr(record, "name", False)
        if not name or callable(name):
            return {}
        group = self.env["account.tax.group"].search(
            [("name", "=", name)], limit=1
        )
        if group:
            return {"odoo_id": group.id}
        return {}

    @only_create
    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}
