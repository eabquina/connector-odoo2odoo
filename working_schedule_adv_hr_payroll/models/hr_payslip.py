import pytz
from pytz import timezone
from datetime import date, datetime
from odoo import api, fields, models, Command


class PayslipScheduleChanges(models.Model):
    """Inherit the model to add fields and functions"""
    _inherit = 'hr.payslip'
    
    request_change_lines = fields.Many2many(
        'resource.calendar.change.lines', 
        string="Work Schedule Changes",
        compute="_compute_request_change_lines",
        store=True,
        help="Get Work Schedule Change records of the employee.")
    
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_request_change_lines(self):
        """Function used for getting Work Schedule request records."""
        for payslip in self:
            if payslip.contract_id:
                calendar = payslip.contract_id.resource_calendar_id
                tz = timezone(calendar.tz)
                dt_from = tz.localize(datetime.combine(payslip.date_from, datetime.min.time()))
                dt_to = tz.localize(datetime.combine(payslip.date_to, datetime.max.time()))
                request_change_lines_domain = [
                        ('employee_id', '=', payslip.employee_id.id),
                        ('date', '>=', dt_from.date().strftime('%Y-%m-%d')),
                        ('date', '<=', dt_to.date().strftime('%Y-%m-%d')),
                        ('request_id.state', '=', 'confirm'),
                    ]
                payslip.request_change_lines = payslip.env['resource.calendar.change.lines'].search(request_change_lines_domain)
      