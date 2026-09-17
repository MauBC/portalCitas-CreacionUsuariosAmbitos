"""Preview gates must not reuse an obsolete successful execution."""
import os
from pathlib import Path
import sys
import tempfile
from time import monotonic
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from app.ui.dialogs.app_dialog import AppDialog
from app.config import paths
from app.ui.pages.phase2_page import Phase2Page
from app.ui.pages.ambitos_page import AmbitosPage


class PreviewFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        patch.object(paths, "OUTPUT_ROOT", Path(temp.name)).start()
        self.pages = (Phase2Page(), AmbitosPage())
        for method in ("success", "warning", "error"):
            patch.object(AppDialog, method).start()
        self.addCleanup(patch.stopall)

    def tearDown(self):
        for page in self.pages:
            page.close()
            page.deleteLater()
        self.app.processEvents()

    def test_replaced_inputs_and_changed_during_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.xlsx"
            for page in self.pages:
                with self.subTest(page=type(page).__name__):
                    source.write_bytes(b"original")
                    field = page.portal_result if isinstance(page, Phase2Page) else page.valid_report
                    field.setText(str(source))
                    original = page._current_signature()
                    page.running_preview_signature = original
                    source.write_bytes(b"changed content")
                    self.assertNotEqual(original, page._current_signature())
                    page._on_finished("preview", {"ok": True})
                    self.assertIsNone(page.last_preview)
                    self.assertIn("cambiaron", page.status_label.text())
                    source.unlink()
                    self.assertNotEqual(original, page._current_signature())

    def test_new_preview_failure_cannot_restore_previous_success(self):
        for page, target in zip(self.pages, (
            "app.ui.workers.phase2_worker.Phase2Worker._run_per",
            "app.ui.workers.phase3_worker.Phase3Worker._run_preview",
        )):
            with self.subTest(page=type(page).__name__):
                page._on_finished("preview", {"ok": True, "listo_para_escritura": True})
                self.assertIsNotNone(page.last_preview)
                with patch(target, side_effect=RuntimeError("Offline test failure")):
                    page._start_worker("preview")
                    self.assertIsNone(page.last_preview)
                    deadline = monotonic() + 5
                    while page.thread is not None and monotonic() < deadline:
                        QTest.qWait(10)
                    self.assertIsNone(page.thread)
                self.assertIsNone(page.last_preview)
                button = page.apply_button if isinstance(page, Phase2Page) else page.final_button
                self.assertFalse(button.isEnabled())

    def test_input_change_clears_previous_artifacts(self):
        phase2, scopes = self.pages
        phase2.last_local_copy = {"candidate_path": "old.xlsx"}
        phase2.last_apply = {"ok": True}
        scopes.last_final = {"template_path": "old-final.xlsx"}
        scopes.review_path.setText("old-review.xlsx")
        phase2.portal_result.setText("new.xlsx")
        scopes.valid_report.setText("new.xlsx")
        self.assertIsNone(phase2.last_local_copy)
        self.assertIsNone(phase2.last_apply)
        self.assertIsNone(scopes.last_final)
        self.assertEqual(scopes.review_path.text(), "")
        self.assertFalse(scopes.open_final_button.isEnabled())
        self.assertFalse(phase2.open_result_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
