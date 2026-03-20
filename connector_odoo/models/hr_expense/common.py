# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


# -- hr.expense.sheet --


class OdooHrExpenseSheet(models.Model):
    _name = "odoo.hr.expense.sheet"
    _inherit = "odoo.binding"
    _inherits = {"hr.expense.sheet": "odoo_id"}
    _description = "External Odoo Expense Report"

    odoo_id = fields.Many2one(
        comodel_name="hr.expense.sheet",
        string="Expense Report",
        required=True,
        ondelete="cascade",
    )

    backend_total_amount = fields.Float()
    backend_state = fields.Char()
    backend_expense_count = fields.Integer(string="Backend Expense Count")
    synced_expense_count = fields.Integer(
        string="Synced Expense Count",
        compute="_compute_synced_expense_count",
    )

    def _compute_synced_expense_count(self):
        expense_model = self.env["odoo.hr.expense"]
        for sheet in self:
            sheet.synced_expense_count = expense_model.search_count(
                [
                    ("backend_id", "=", sheet.backend_id.id),
                    ("sheet_id", "=", sheet.odoo_id.id),
                ]
            )

    def _compute_import_state(self):
        for sheet in self:
            if sheet.backend_expense_count != sheet.synced_expense_count:
                sheet.import_state = "error_sync"
            elif (
                sheet.backend_total_amount
                and round(sheet.backend_total_amount, 2)
                != round(sheet.total_amount, 2)
            ):
                sheet.import_state = "error_amount"
            else:
                sheet.import_state = "done"

    import_state = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("error_sync", "Sync Error"),
            ("error_amount", "Amounts Error"),
            ("done", "Done"),
        ],
        default="waiting",
        compute=_compute_import_state,
    )

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        return self.with_delay().import_record(
            self.backend_id, self.external_id, force=True
        )

    def _get_remote_expense_ids(self):
        self.ensure_one()
        if self.external_id <= 0:
            return []
        with self.backend_id.work_on("odoo.hr.expense") as work:
            adapter = work.component(usage="backend.adapter")
            return adapter.search(
                [("sheet_id", "=", self.external_id)],
                order="id",
            )

    def sync_expenses(self):
        for binding in self:
            remote_expense_ids = binding._get_remote_expense_ids()
            binding.backend_expense_count = len(remote_expense_ids)
            for remote_expense_id in remote_expense_ids:
                self.env["odoo.hr.expense"].with_delay().import_record(
                    binding.backend_id, remote_expense_id, force=True
                )
        return True

    def _approve_if_needed(self):
        for binding in self:
            if binding.backend_state in ("approve", "post", "done"):
                if binding.odoo_id.state == "draft":
                    try:
                        binding.odoo_id.action_submit_sheet()
                    except Exception:
                        _logger.warning(
                            "Could not submit expense sheet %s",
                            binding.odoo_id.id,
                            exc_info=True,
                        )
                if binding.odoo_id.state == "submit":
                    try:
                        binding.odoo_id.approve_expense_sheets()
                    except Exception:
                        _logger.warning(
                            "Could not approve expense sheet %s",
                            binding.odoo_id.id,
                            exc_info=True,
                        )


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.expense.sheet",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HrExpenseSheetAdapter(Component):
    _name = "odoo.hr.expense.sheet.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.expense.sheet"
    _odoo_model = "hr.expense.sheet"


# -- hr.expense --


class OdooHrExpense(models.Model):
    _name = "odoo.hr.expense"
    _inherit = "odoo.binding"
    _inherits = {"hr.expense": "odoo_id"}
    _description = "External Odoo Expense"

    odoo_id = fields.Many2one(
        comodel_name="hr.expense",
        string="Expense",
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
        return self.with_delay().import_record(
            self.backend_id, self.external_id, force=True
        )


class HrExpense(models.Model):
    _inherit = "hr.expense"

    bind_ids = fields.One2many(
        comodel_name="odoo.hr.expense",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class HrExpenseAdapter(Component):
    _name = "odoo.hr.expense.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.hr.expense"
    _odoo_model = "hr.expense"
