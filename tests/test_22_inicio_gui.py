"""Entrypoint checks run in separate processes without touching external services."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EntrypointTests(unittest.TestCase):
    def test_offline_self_check_from_another_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "report.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "run_gui.py"), "--self-check", str(report)],
                cwd=temp, capture_output=True, text=True, timeout=45,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(data["ok"])
            self.assertIn("subida_usuarios.xlsx", data["checks"])
            self.assertEqual(Path(data["runtime_root"]), ROOT)

    def test_missing_configuration_shows_actionable_error(self):
        code = '''
from unittest.mock import patch
from run_gui import main
with patch("run_gui.load_env", side_effect=FileNotFoundError("missing .env")):
    with patch("app.ui.dialogs.app_dialog.AppDialog.error") as dialog:
        assert main([]) == 1
        dialog.assert_called_once()
        assert ".env" in dialog.call_args.args[2]
'''
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
