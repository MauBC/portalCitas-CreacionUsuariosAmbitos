"""Local regression tests: explicit environment paths and persistent diagnostics."""

import os
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config.env_loader import load_env
from app.config import paths
from app.services.error_report_service import build_error_details, redact_secrets


class ConfigurationAndLogsTests(unittest.TestCase):
    def test_env_uses_runtime_root_and_preserves_process_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / '.env').write_text('TEST_VALUE=file\nTEST_EXTRA=loaded\n')
            with patch('app.config.env_loader.get_runtime_root', return_value=root):
                with patch.dict(os.environ, {'TEST_VALUE': 'process'}, clear=True):
                    self.assertEqual(load_env(), root / '.env')
                    self.assertEqual(os.environ['TEST_VALUE'], 'process')
                    self.assertEqual(os.environ['TEST_EXTRA'], 'loaded')

    def test_missing_env_required_and_optional(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch('app.config.env_loader.get_runtime_root', return_value=Path(temp)):
                with self.assertRaises(FileNotFoundError):
                    load_env()
                self.assertEqual(load_env(required=False), Path(temp) / '.env')

    def test_unrelated_cwd_env_is_not_loaded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unrelated = root / 'unrelated'
            unrelated.mkdir()
            (unrelated / '.env').write_text('TEST_VALUE=wrong\n')
            before = Path.cwd()
            try:
                os.chdir(unrelated)
                with patch('app.config.env_loader.get_runtime_root', return_value=root):
                    with patch.dict(os.environ, {}, clear=True):
                        load_env(required=False)
                        self.assertNotIn('TEST_VALUE', os.environ)
            finally:
                os.chdir(before)

    def test_frozen_runtime_uses_executable_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            executable = Path(temp) / 'Portal.exe'
            with patch.object(sys, 'frozen', True, create=True):
                with patch.object(sys, 'executable', str(executable)):
                    self.assertEqual(paths.get_runtime_root(), Path(temp).resolve())
        with patch.object(sys, 'frozen', False, create=True):
            self.assertEqual(paths.get_runtime_root(), ROOT)

    def test_resource_paths_and_unique_output_directories(self):
        self.assertTrue((paths.TEMPLATES_ROOT / 'subida_usuarios.xlsx').is_file())
        self.assertTrue((paths.CONFIG_ROOT / 'ambitos_config.json').is_file())
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(paths, 'datetime') as clock:
                clock.now.return_value = datetime(2026, 9, 15, 12, 0, 0)
                first = paths.create_run_folder('test', temp)
                second = paths.create_run_folder('test', temp)
            self.assertNotEqual(first, second)
            self.assertTrue(first.is_dir() and second.is_dir())

    def test_secret_redaction(self):
        with patch.dict(os.environ, {'MS_CLIENT_SECRET': 'secret-example', 'DB_PASSWORD': 'db-example'}):
            source = ('secret-example db-example Authorization: Bearer bearer-example\n'
                      'password="quoted password" access_token=token-example&x=1 '
                      "{'client_secret': 'json-example'}")
            redacted = redact_secrets(source)
        for secret in ('secret-example', 'db-example', 'bearer-example',
                       'quoted password', 'token-example', 'json-example'):
            self.assertNotIn(secret, redacted)
        self.assertIn('x=1', redacted)

    def test_report_is_saved_and_path_is_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(paths, 'OUTPUT_ROOT', Path(temp)):
                details = build_error_details(
                    phase='2', country='PER', mode='preview',
                    error_detail='ExampleError', full_trace='password=hidden\nTraceback example',
                )
            files = list(Path(temp).glob('error_gui_*/error.log'))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding='utf-8')
            self.assertIn('Fase: 2\nPais: PER\nModo: preview', content)
            self.assertIn('Traceback example', content)
            self.assertNotIn('hidden', content)
            self.assertIn(str(files[0]), details)

    def test_disk_failure_preserves_diagnostic(self):
        with patch('app.services.error_report_service.create_run_folder', side_effect=PermissionError):
            details = build_error_details(
                phase='1', country='SLV', mode='users',
                error_detail='Original failure', full_trace='Traceback example',
            )
        self.assertIn('No se pudo guardar el log', details)
        self.assertIn('Original failure', details)


if __name__ == '__main__':
    unittest.main()
