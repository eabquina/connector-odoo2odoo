from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNeutralization(TransactionCase):
    def test_both_connection_paths_block_before_transport(self):
        self.env["ir.config_parameter"].sudo().set_param("database.is_neutralized", True)
        backend = self.env["odoo.backend"].new({})
        target = "odoo.addons.connector_odoo.models.odoo_backend.common.OdooAPI"
        with patch(target) as transport:
            with self.assertRaisesRegex(UserError, "neutralized"):
                backend.get_connection()
            with self.assertRaisesRegex(UserError, "neutralized"):
                with backend.work_on("res.partner"):
                    self.fail("Neutralized backend opened a work session")
            transport.assert_not_called()
