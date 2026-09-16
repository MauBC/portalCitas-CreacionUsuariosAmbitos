"""Error hints distinguish access failures from uncertain remote writes."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from app.config import paths
from app.ui.dialogs.app_dialog import AppDialog
from app.ui.error_guidance import error_guidance
from app.ui.main_window import MainWindow


class ErrorGuidanceTests(unittest.TestCase):
    def test_actionable_known_errors(self):
        cases = (
            ("psycopg2.OperationalError: connection to server failed: timed out", "VPN"),
            ("password authentication failed", "contraseña"),
            ("no pg_hba.conf entry", "administrador"),
            ("Error autenticando con Microsoft: invalid_client", "credenciales"),
            ("Error en llamada Graph | status=403", "permisos"),
            ("401 Client Error: Unauthorized", "autenticación"),
            ("SSLError: CERTIFICATE_VERIFY_FAILED", "No desactives"),
            ("PermissionError: [Errno 13] Permission denied", "Cierra el archivo"),
            ("FileNotFoundError: input.xlsx", "vuelve a seleccionarlo"),
        )
        for error, expected in cases:
            with self.subTest(error=error):
                self.assertIn(expected, error_guidance(error))

    def test_wrapped_error_uses_trace_without_exposing_it_in_hint(self):
        hint = error_guidance("Error en llamada Graph", "requests.ReadTimeout: secret timed out", mode="apply")
        self.assertIn("incierto", hint)
        self.assertNotIn("secret", hint)
        self.assertIn("nuevo preview", hint)
        self.assertNotIn("incierto", error_guidance("ReadTimeout", mode="preview"))

    def test_unknown_business_errors_remain_unclassified(self):
        self.assertEqual(error_guidance("Cliente 403 requiere revisión"), "")
        self.assertEqual(error_guidance("No existen registros con creado=1"), "")
        self.assertEqual(error_guidance("Columnas inválidas"), "")

    def test_all_pages_show_hint_and_keep_redacted_details(self):
        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        try:
            with tempfile.TemporaryDirectory() as directory, \
                    patch.object(paths, "OUTPUT_ROOT", Path(directory)), \
                    patch.object(AppDialog, "error") as dialog:
                error = "OperationalError: connection to server timed out password=test-secret"
                window.users_page._on_failed(error, "psycopg2.OperationalError")
                window.phase2_page._on_failed("preview", error, "psycopg2.OperationalError")
                window.ambitos_page._on_failed("preview", error, "psycopg2.OperationalError")
                self.assertEqual(dialog.call_count, 3)
                for call in dialog.call_args_list:
                    self.assertIn("VPN", call.args[2])
                    self.assertNotIn("test-secret", str(call))
                    self.assertIn("Log guardado en:", call.kwargs["details"])
        finally:
            window.close()
            window.deleteLater()
            app.processEvents()


if __name__ == "__main__":
    unittest.main()
