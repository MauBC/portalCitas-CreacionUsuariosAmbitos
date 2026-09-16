"""Offscreen GUI regression: errors remain visible and persist without a console."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from app.config import paths
from app.ui.dialogs.app_dialog import AppDialog
from app.ui.main_window import MainWindow


class GuiErrorsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_all_pages_persist_redacted_errors(self):
        window = MainWindow()
        try:
            window.show()
            window.resize(1020, 680)
            self.app.processEvents()
            with tempfile.TemporaryDirectory() as temp:
                with patch.object(paths, 'OUTPUT_ROOT', Path(temp)):
                    with patch.object(AppDialog, 'error') as dialog:
                        window.users_page._on_failed('password=sample-secret', 'Traceback example')
                        window.phase2_page._on_failed('preview', 'password=sample-secret', 'Traceback example')
                        window.ambitos_page._on_failed('preview', 'password=sample-secret', 'Traceback example')
                    self.assertEqual(dialog.call_count, 3)
                    for call in dialog.call_args_list:
                        self.assertNotIn('sample-secret', str(call))
                        self.assertIn('Log guardado en:', call.kwargs['details'])
                    self.assertEqual(len(list(Path(temp).glob('error_gui_*/error.log'))), 3)
        finally:
            window.close()
            window.deleteLater()
            self.app.processEvents()


if __name__ == '__main__':
    unittest.main()
