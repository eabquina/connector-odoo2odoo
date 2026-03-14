# © 2013-2017 Guewen Baconnier,Camptocamp SA,Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OdooBinding(models.AbstractModel):
    """Abstract Model for the Bindings.

    All the models used as bindings between Magento and Odoo
    (``magento.res.partner``, ``magento.product.product``, ...) should
    ``_inherit`` it.
    """

    _name = "odoo.binding"
    _inherit = "external.binding"
    _description = "Odoo Binding (abstract)"

    # odoo_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name="odoo.backend",
        string="Odoo Backend",
        required=True,
        ondelete="restrict",
    )
    external_id = fields.Integer(string="ID on Ext Odoo", default=-1)

    _sql_constraints = [
        (
            "odoo_backend_odoo_uniq",
            "unique(backend_id, odoo_id)",
            "A binding already exists with the same backend for this object.",
        )
    ]

    @api.constrains("backend_id", "external_id")
    def unique_backend_external_id(self):
        for rec in self:
            if rec.external_id <= 0:
                continue
            # Use direct SQL to avoid ORM flush side effects while validating
            # the binding uniqueness.
            self.env.cr.execute(
                f"""
                SELECT 1
                  FROM {self._table}
                 WHERE backend_id = %s
                   AND external_id = %s
                   AND id <> %s
                 LIMIT 1
                """,
                (rec.backend_id.id, rec.external_id, rec.id or 0),
            )
            if self.env.cr.fetchone():
                raise ValidationError(
                    _(
                        "A binding already exists with the same backend '{name}' "
                        "for the external id {external_id} of the model {_name}"
                    ).format(rec.backend_id.name, rec.external_id, rec._name)
                )

    def resync(self):
        return self.with_delay().export_record(self.backend_id)

    def action_resync_selected(self):
        for record in self:
            record.resync()
        return True

    @api.model
    def import_batch(self, backend, filters=None):
        """Prepare the import of records modified on Odoo"""
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage="batch.importer")
            return importer.run(filters=filters, force=backend.force)

    @api.model
    def import_record(self, backend, external_id, force=False):
        """Import a Odoo record"""
        with backend.work_on(self._name) as work:
            importer = work.component(usage="record.importer")
            return importer.run(external_id, force=force)

    @api.model
    def export_batch(self, backend, filters=None):
        """Prepare the import of records modified on Odoo"""
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            exporter = work.component(usage="batch.exporter")
            return exporter.run(filters=filters)

    def export_record(self, backend, fields=None):
        """Export a record on Odoo"""
        self.ensure_one()
        with backend.work_on(self._name) as work:
            exporter = work.component(usage="record.exporter")
            return exporter.run(self)

    def export_delete_record(self, backend, external_id):
        """Delete a record on Odoo"""
        with backend.work_on(self._name) as work:
            deleter = work.component(usage="record.exporter.deleter")
            return deleter.run(external_id)
