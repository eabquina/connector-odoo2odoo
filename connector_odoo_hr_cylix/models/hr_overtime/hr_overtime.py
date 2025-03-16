from odoo import fields, models, _


class HrOvertime(models.Model):
    """Inherit the model to add fields and functions"""
    _name = "hr.overtime"