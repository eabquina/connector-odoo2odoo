from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResourceCalendarChange(models.Model):
    _name = 'resource.calendar.change'
    _description = 'Work Schedule Change Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain
    
    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id.id, required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job Position", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    current_user = fields.Many2one('res.users', string="Current User",
                                   related='employee_id.user_id',
                                   default=lambda self: self.env.uid,
                                   store=True)
    current_user_boolean = fields.Boolean()
    
    company_id = fields.Many2one('res.company', string='Company', help="Company")

    contract_id = fields.Many2one('hr.contract', string="Contract", 
                                  related="employee_id.contract_id")
    resource_calendar_id = fields.Many2one('resource.calendar', string="Work Schedule",
                                          related="contract_id.resource_calendar_id")
    
    type_id = fields.Many2one('resource.calendar.change.type', string='Change Type', required=True)
    
    duration = fields.Selection([
        ('day', 'Day'),
        ('week', 'Week'),
        ('semi-monthly', 'Semi-Monthly'),
        ('month', 'Month'),
        ], string='Duration Type', required=True)
    
    date_from = fields.Date('Period Date From')
    date_to = fields.Date('Period Date To')
    calendar_to = fields.Many2one('resource.calendar', string="Calendar To")
    
    purpose = fields.Text('Purpose', tracking=True, help="Purpose of the work schedule change")
    cancel_reason = fields.Text('Refuse / Cancel Reason', tracking=True, 
                                help="Reason for refusal or cancellation")
    
    change_lines = fields.One2many('resource.calendar.change.lines',
                            'request_id', 
                            string="Work Schedule Change Request Lines",
                            copy=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('confirm', 'Confirmed'),
        ('refuse', 'Refused'),
        ('cancel', 'Cancelled'),
        ], string='Status', default='draft', tracking=True)
    

    def check_work_day(self, date):
        """Check if the date is a work day or not."""
        calendar = self.resource_calendar_id
        schedule = set(calendar.attendance_ids.filtered(lambda r: r.day_period != 'lunch').mapped('dayofweek'))
        if str(date.weekday()) in schedule:
            return True
        else:
            return False

    # Computes
    @api.onchange('duration')
    def _onchange_duration(self):
        
        ## Unset Date To and From 
        self.date_from = False
        self.date_to = False
        
        if not self.date_to and not self.date_from:
            if self.duration == 'week':
                self.date_from = fields.Date.today()
                self.date_to = fields.Date.today() + timedelta(days=7)
            elif self.duration == 'semi-monthly':
                self.date_from = fields.Date.today()
                self.date_to = fields.Date.today() + timedelta(days=15)
            elif self.duration == 'month':
                self.date_from = fields.Date.today()
                self.date_to = fields.Date.today() + timedelta(days=30)
            
            ## Choose any Calendar other than the current
            other_calendars = self.env['resource.calendar'].search([('id', '!=', self.resource_calendar_id.id)], limit=1)
            self.calendar_to = other_calendars[0].id
    
    @api.onchange('date_from')
    def _onchange_date_from(self):
        ## Reset Change Lines
        if len(self.change_lines) > 0:
            self.change_lines = [(5, 0, 0)]
                
        date_from = self.date_from
        if self.duration == 'week':
            date_to = date_from + relativedelta(days=6)
        elif self.duration == 'semi-monthly':
            date_to = date_from + relativedelta(days=14)
        elif self.duration == 'month':
            date_to = date_from + relativedelta(month=1)
        elif self.duration == 'day':
            date_to = date_from
    
        if self.duration in ['week', 'semi-monthly', 'month']:
            self.date_to = date_to
            duration_length = abs((date_to - date_from).days + 1)
            add_lines = []
            for i in range(duration_length):
                ## Check if the date is not required to be added based on work schedule
                date_to_add = self.date_from + relativedelta(days=i)
                date_schedule_check = self.check_work_day(date_to_add)
                if date_schedule_check:
                    add_lines.append((0, 0, {
                        'request_id': self.id,
                        'employee_id': self.employee_id.id,
                        'date': date_to_add,
                        'calendar_to': self.calendar_to.id,
                        'calendar_from': self.resource_calendar_id.id,
                        'type_id': self.type_id.id,
                    }))
            self.change_lines = add_lines

   
    @api.onchange('calendar_to')
    def _onchange_calendar_to(self):
        self._onchange_date_from()  
    
    
    @api.onchange('type_id')
    def _onchange_type_id(self):
        for line in self.change_lines:
            if not line.type_id:
                line.type_id = self.type_id.id
    
    @api.onchange('change_lines')
    def _onchange_change_lines(self):
        for line in self.change_lines:
            if not line.calendar_from:
                line.calendar_from = self.resource_calendar_id.id
            if not line.type_id:
                line.type_id = self.type_id.id
            if not line.calendar_to:
                line.calendar_to = self.calendar_to.id
            if not line.employee_id:
                line.employee_id = self.employee_id.id
    
    @api.model
    def create(self, values):
        if not values.get('name'):
            seq = self.env['ir.sequence'].next_by_code('resource.calendar.change') or '/'
            values['name'] = seq
        return super(ResourceCalendarChange, self.sudo()).create(values)
        
    
    @api.model
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft', 'cancel']:
                raise UserError(_("You can only delete draft or cancelled requests."))
        return super(ResourceCalendarChange, self).unlink()
    
    
    # -- Actions --
    def submit(self):
        # notification to employee
        recipient_partners = [(4, self.current_user.partner_id.id)]
        body = "Your Work Schedule Change Request Waiting for Approval .."
        msg = _(body)

        # notification to Manager and HR :
        #group = self.env.ref('', False)
        recipient_partners = []

        body = "You Got New Work Schedule Change Request From Employee : " + str(
            self.employee_id.name)
        msg = _(body)
        return self.sudo().write({
            'state': 'sent'
        })
        
    def confirm(self):
        # notification to employee :
        recipient_partners = [(4, self.current_user.partner_id.id)]
        body = "Your Work Schedule Request Has been Confirmed ..."
        msg = _(body)
        return self.sudo().write({
            'state': 'confirm',
        })

    def reject(self):
        self.state = 'refuse'
        if not self.cancel_reason:
            raise UserError(_("Please provide a reason for the refusal for the schedule."))

    def cancel(self):
        self.state = 'cancel'
        
    def draft(self):
        self.state = 'draft'
