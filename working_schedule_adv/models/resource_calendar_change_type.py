from odoo import api, models, fields

class ResourceCalendarChangeType(models.Model):
    _name = 'resource.calendar.change.type'
    _description = 'Work Schedule Change Type'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)