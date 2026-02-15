from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ResourceCalendarChangeLines(models.Model):
    _name = 'resource.calendar.change.lines'
    _description = 'Work Schedule Change Request Lines'
    
    request_id = fields.Many2one('resource.calendar.change', string="Resource Calendar Change")
    
    employee_id = fields.Many2one('hr.employee', string='Employee', related='request_id.employee_id', readonly=True, store=True)
    
    date = fields.Date(string="Date", required=True)
    calendar_from = fields.Many2one('resource.calendar', string="Work Schedule", 
                                    related='request_id.resource_calendar_id', required=True,
                                    help="Current Work Schedule on the time of request")
    calendar_to = fields.Many2one('resource.calendar', string="Work Schedule Change", required=True, help="Alternate Work Schedule")
    reason = fields.Text(string="Reason for Change", help="Reason for the change in the working schedule")
    type_id = fields.Many2one('resource.calendar.change.type', string='Change Type')        
    
    _sql_constraints = [
        ('unique_date', 'unique(request_id, date)', 'Date must be unique per request'),
        ('unique_employee_date', 'unique(employee_id, date)', 'Date must be unique per employee')
    ]



    @api.model
    def create(self, values):    
        if not self.calendar_from:
            self.calendar_from = self.request_id.resource_calendar_id.id
        if not self.type_id:
            self.type_id = self.request_id.type_id.id
        if not self.calendar_to:
            self.calendar_to = self.request_id.calendar_to.id
        return super(ResourceCalendarChangeLines, self.sudo()).create(values)
    
    @api.constrains('date')
    def _check_unique_date_employee(self):
        for rec in self:
            change_lines = self.env['resource.calendar.change.lines'].search([('employee_id', '=', rec.request_id.employee_id.id),
                                                                              ('date', '=', rec.date)])
            if len(change_lines) > 1:
                raise ValidationError(_('Date must be unique per employee. Please check the existing requests with the same dates.'))
      
    @api.constrains('calendar_to')
    def _check_calendar_to(self):
        for rec in self:
            if rec.calendar_to == rec.calendar_from:
                raise ValidationError(_('Work Schedule Change must be different from the current work schedule.'))      