"""Phase 2 presentation refactors must preserve publication and preview gates."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from app.ui.dialogs.app_dialog import AppDialog
from app.ui.pages.phase2_page import Phase2Page
from app.ui.views.phase2_view import Phase2View


class Phase2FlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.page = Phase2Page()
        self.success = patch.object(AppDialog, "success").start()
        self.warning = patch.object(AppDialog, "warning").start()

    def tearDown(self):
        patch.stopall()
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()

    def test_view_can_be_created_without_controller(self):
        view = Phase2View()
        self.assertFalse(view.apply_button.isEnabled())
        self.assertFalse(view.continue_ambitos_button.isEnabled())
        view.deleteLater()

    def test_preview_copy_and_verified_replacement(self):
        self.page._on_finished("preview", {
            "ok": True, "listo_para_escritura": True,
            "actualizaciones_remotas_preview": 2,
            "cuentas_enviadas": 1, "relaciones_total": 2,
        })
        self.assertTrue(self.page.local_copy_button.isEnabled())
        self.assertTrue(self.page.apply_button.isEnabled())
        self.assertFalse(self.page.continue_ambitos_button.isEnabled())
        self.page._on_finished("local_copy", {"ok": True, "candidate_path": "local.xlsx"})
        self.assertFalse(self.page.continue_ambitos_button.isEnabled())
        self.assertFalse(self.page.remote_replacement_verified)
        self.assertEqual(self.page.open_result_button.text(), "Abrir copia local")
        self.page._on_finished("verify_remote", {"replacement_verified": False})
        self.assertFalse(self.page.continue_ambitos_button.isEnabled())
        self.page._on_finished("verify_remote", {"replacement_verified": True})
        self.assertTrue(self.page.continue_ambitos_button.isEnabled())
        self.page.portal_result.setText("changed-result.xlsx")
        self.assertIsNone(self.page.last_preview)
        self.assertFalse(self.page.continue_ambitos_button.isEnabled())

    def test_conflicts_keep_write_actions_disabled(self):
        self.page._on_finished("preview", {
            "ok": True, "listo_para_escritura": True,
            "actualizaciones_remotas_preview": 2, "conflictos_remotos": 1,
        })
        self.assertFalse(self.page.apply_button.isEnabled())
        self.assertFalse(self.page.local_copy_button.isEnabled())

    def test_slv_apply_and_country_switch(self):
        self.page.set_country("SLV")
        self.page._on_finished("preview", {"ok": True, "preview": [{}], "failed": []})
        self.assertTrue(self.page.apply_button.isEnabled())
        self.assertFalse(self.page.local_copy_button.isEnabled())
        self.page._on_finished("apply", {"ok": True, "updated": 1, "total": 1})
        self.assertTrue(self.page.continue_ambitos_button.isEnabled())
        self.page.set_country("PER")
        self.assertFalse(self.page.continue_ambitos_button.isEnabled())
        self.assertTrue(self.page.advanced_panel.isHidden())
        self.page.advanced_toggle_button.click()
        self.assertFalse(self.page.advanced_panel.isHidden())


if __name__ == "__main__":
    unittest.main()
