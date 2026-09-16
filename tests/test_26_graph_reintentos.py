"""HTTP retry policy with real response parsing and no external requests."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from app.clients.graph_client import GraphClient


def response(status, body=b'{"ok": true}', headers=None):
    result = requests.Response()
    result.status_code = status
    result._content = body
    result._content_consumed = True
    result.headers.update({"Content-Type": "application/json", **(headers or {})})
    return result


class GraphRetryTests(unittest.TestCase):
    def setUp(self):
        patch("app.clients.graph_client.MsalAuthService").start()
        self.request = patch("app.clients.graph_client.requests.request").start()
        self.sleep = patch("app.clients.graph_client.time.sleep").start()
        self.addCleanup(patch.stopall)
        self.client = GraphClient()

    def test_permanent_http_errors_fail_without_retry(self):
        for status in (400, 401, 403, 404, 409, 422):
            with self.subTest(status=status):
                self.request.reset_mock()
                self.request.return_value = response(status)
                with self.assertRaises(RuntimeError) as caught:
                    self.client.get("/test")
                self.assertIsInstance(caught.exception.__cause__, requests.HTTPError)
                self.request.assert_called_once()
                self.sleep.assert_not_called()

    def test_throttle_honors_retry_after(self):
        self.request.side_effect = [response(429, headers={"Retry-After": "7"}), response(200)]
        self.assertEqual(self.client.get("/test"), {"ok": True})
        self.sleep.assert_called_once_with(7)

    def test_transient_errors_stop_at_limit_without_final_sleep(self):
        self.request.return_value = response(503)
        with self.assertRaises(RuntimeError):
            self.client._request("GET", "https://example.test", max_retries=3)
        self.assertEqual(self.request.call_count, 3)
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [1, 2])

    def test_read_timeout_retries_but_write_timeout_does_not(self):
        self.request.side_effect = [requests.Timeout("Read timed out"), response(200)]
        self.assertEqual(self.client.get("/test"), {"ok": True})
        self.assertEqual(self.request.call_count, 2)
        self.request.reset_mock()
        self.sleep.reset_mock()
        self.request.side_effect = requests.Timeout("Write outcome unknown")
        with self.assertRaises(RuntimeError) as caught:
            self.client.patch("/test", {"state": 1})
        self.assertIsInstance(caught.exception.__cause__, requests.Timeout)
        self.request.assert_called_once()
        self.sleep.assert_not_called()

    def test_invalid_json_and_certificate_errors_are_not_retried(self):
        self.request.return_value = response(200, b'not json')
        with self.assertRaises(RuntimeError):
            self.client.get("/test")
        self.request.assert_called_once()
        self.request.reset_mock()
        self.request.side_effect = requests.exceptions.SSLError("Invalid certificate")
        with self.assertRaises(RuntimeError):
            self.client.get("/test")
        self.request.assert_called_once()
        self.sleep.assert_not_called()

    def test_empty_response_and_attempt_validation(self):
        self.request.return_value = response(204, b'')
        self.assertIsNone(self.client.patch("/test", {}))
        self.request.reset_mock()
        with self.assertRaises(ValueError):
            self.client._request("GET", "https://example.test", max_retries=0)
        self.request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
