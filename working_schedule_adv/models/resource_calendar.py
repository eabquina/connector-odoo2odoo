# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import _, api, fields, models



class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    work_changes_count = fields.Integer("# Work Schedule Changes for the schedule", compute='_compute_changes_count', groups="hr_contract.group_hr_contract_manager")
    
    def _compute_changes_count(self):
        count_data = self.env['resource.calendar.change.lines']._read_group(
            [('calendar_to', 'in', self.ids)],
            ['calendar_to'],
            ['__count'])
        mapped_counts = {resource_calendar.id: count for resource_calendar, count in count_data}
        for calendar in self:
            calendar.work_changes_count = mapped_counts.get(calendar.id, 0)

    def action_open_schedule_changes(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("working_schedule_adv.resource_calendar_change_lines_action")
        action.update({'domain': [('calendar_to', '=', self.id)]})
        return action
    