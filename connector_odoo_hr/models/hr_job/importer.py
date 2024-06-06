import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class JobPositionBatchImporter(Component):
    """Import the Odoo Partner Category.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.hr.job.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.hr.job"]


class JobPositionImportMapper(Component):
    _name = "odoo.hr.job.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.hr.job"]

    direct = [
        ("description", "description"),
        ("active", "active"),
        ("name", "name"),        
        ("color", "color"),
        ("is_favorite", "is_favorite"),
        ("is_published", "is_published"),
        ("can_publish", "can_publish"),
        ("website_url", "website_url"),
        ("job_details", "job_details"),
        ("published_date", "published_date"),
    ]


class JobPositionImporter(Component):
    _name = "odoo.hr.job.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.hr.job"]
