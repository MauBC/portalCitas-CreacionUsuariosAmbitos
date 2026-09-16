"""Database resource lifecycle without network access or credentials."""
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.clients.postgres_client import PostgresClient
from app.config.settings import settings


class PostgresConnectionTests(unittest.TestCase):
    def setUp(self):
        self.timeout = patch.object(settings, "DB_CONNECT_TIMEOUT", "15")
        self.timeout.start()
        self.addCleanup(self.timeout.stop)
        self.client = PostgresClient(database_name="offline_test")
        self.connection = MagicMock()
        self.connection.__enter__.return_value = self.connection
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.cursor.description = [("id",), ("nombre",)]
        self.cursor.fetchall.return_value = [(1, "Cliente")]
        self.connect = patch(
            "app.clients.postgres_client.psycopg2.connect", return_value=self.connection
        ).start()
        self.addCleanup(patch.stopall)

    def test_success_preserves_rows_parameters_and_closes_after_transaction(self):
        result = self.client.fetch_all("SELECT id, nombre WHERE id = %s", (1,))
        self.assertEqual(result, [{"id": 1, "nombre": "Cliente"}])
        self.cursor.execute.assert_called_once_with("SELECT id, nombre WHERE id = %s", (1,))
        self.connection.__exit__.assert_called_once_with(None, None, None)
        self.connection.close.assert_called_once_with()
        calls = [call[0] for call in self.connection.mock_calls]
        self.assertLess(calls.index("__exit__"), calls.index("close"))

    def test_query_and_fetch_failures_preserve_error_and_close(self):
        for stage in ("execute", "fetchall"):
            with self.subTest(stage=stage):
                self.connection.reset_mock()
                error = RuntimeError("Simulated query failure")
                getattr(self.cursor, stage).side_effect = error
                with self.assertRaises(RuntimeError) as caught:
                    self.client.fetch_all("SELECT id, nombre")
                self.assertIs(caught.exception, error)
                self.assertIs(self.connection.__exit__.call_args.args[1], error)
                self.connection.close.assert_called_once_with()
                getattr(self.cursor, stage).side_effect = None

    def test_transaction_failure_still_closes(self):
        self.connection.__exit__.side_effect = RuntimeError("Commit failed")
        with self.assertRaisesRegex(RuntimeError, "Commit failed"):
            self.client.fetch_all("SELECT id, nombre")
        self.connection.close.assert_called_once_with()

    def test_timeout_is_forwarded_and_caller_owns_direct_connection(self):
        with patch.object(settings, "DB_CONNECT_TIMEOUT", "25"):
            client = PostgresClient(database_name="offline_test")
        self.assertIs(client.get_connection(), self.connection)
        self.assertEqual(self.connect.call_args.kwargs["connect_timeout"], 25)
        self.connection.close.assert_not_called()

    def test_invalid_timeout_fails_before_connecting(self):
        for value in ("", "no", "1.5", "0", "-1", "1"):
            with self.subTest(value=value), patch.object(settings, "DB_CONNECT_TIMEOUT", value):
                with self.assertRaisesRegex(ValueError, "DB_CONNECT_TIMEOUT"):
                    PostgresClient(database_name="offline_test")
        self.connect.assert_not_called()

    def test_connection_failure_is_preserved(self):
        error = RuntimeError("Simulated connection failure")
        self.connect.side_effect = error
        with self.assertRaises(RuntimeError) as caught:
            self.client.fetch_all("SELECT id, nombre")
        self.assertIs(caught.exception, error)
        self.connection.close.assert_not_called()


if __name__ == "__main__":
    unittest.main()
