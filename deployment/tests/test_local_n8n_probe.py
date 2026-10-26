"""Security guards for the privately prompted LOCAL-only HTTP probe. No network."""
import contextlib
import importlib.util
import io
import pathlib
import unittest
from unittest.mock import Mock, patch

path = pathlib.Path(__file__).resolve().parents[1] / "n8n" / "probe_local_hook.py"
spec = importlib.util.spec_from_file_location("local_probe", path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeSecurityTests(unittest.TestCase):
    def test_wait_uses_only_uncredentialed_check_until_registered(self):
        check = Mock(side_effect=[{"http_status": 404}, {"http_status": 403}])
        result = probe.wait_for_listener(check=check, clock=lambda: 0, sleeper=lambda _: None)
        self.assertTrue(result["ready"])
        self.assertEqual(result["checks_without_key"], 2)
        self.assertTrue(all(call.args == (3,) for call in check.call_args_list))

    def test_wait_deadline_stops_without_submitting_credentials(self):
        current = [0.0]
        check = Mock(return_value={"http_status": 404})
        result = probe.wait_for_listener(wait_seconds=3, check=check, clock=lambda: current[0],
                                         sleeper=lambda n: current.__setitem__(0, current[0] + n))
        self.assertFalse(result["ready"])
        self.assertEqual(result["error"], "listener_wait_expired")
        self.assertEqual(current[0], 3)

    def test_unprotected_response_does_not_allow_private_submission(self):
        result = probe.wait_for_listener(check=lambda _: {"http_status": 200})
        self.assertFalse(result["ready"])
        self.assertEqual(result["error"], "unexpected_listener_response")

    def test_wait_timeout_never_calls_private_probe(self):
        output = io.StringIO()
        with patch.object(probe.sys.stdin, "isatty", return_value=True), \
                patch.object(probe.getpass, "getpass", return_value="local-unit-only-" + "x" * 32), \
                patch.object(probe, "wait_for_listener", return_value={"ready": False, "error": "listener_wait_expired", "checks_without_key": 2}), \
                patch.object(probe, "probe") as request, contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(["--case", "malformed", "--wait-for-listener"]), 1)
        request.assert_not_called()
        self.assertIn('"credential_submissions": 0', output.getvalue())

    def test_ready_listener_submits_private_probe_exactly_once(self):
        output = io.StringIO()
        secret = "local-unit-only-" + "x" * 32
        with patch.object(probe.sys.stdin, "isatty", return_value=True), \
                patch.object(probe.getpass, "getpass", return_value=secret), \
                patch.object(probe, "wait_for_listener", return_value={"ready": True, "checks_without_key": 2}), \
                patch.object(probe, "probe", return_value={"http_status": 500, "passed": None}) as request, \
                contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(["--case", "malformed", "--wait-for-listener"]), 0)
        request.assert_called_once_with("malformed", secret)
        self.assertNotIn(secret, output.getvalue())
        self.assertIn('"credential_submissions": 1', output.getvalue())

    def test_expired_listener_does_not_judge_private_credential(self):
        response = Mock(status=404)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = response
        with patch.object(probe.urllib.request, "build_opener", return_value=opener):
            result = probe.probe("malformed", "local-unit-only-" + "x" * 32)
        self.assertFalse(result["passed"])
        self.assertEqual(result["error"], "test_webhook_not_registered")
        self.assertEqual(result["authentication_result"], "not_tested")
        self.assertEqual(opener.open.call_count, 1)
        response.read.assert_not_called()

    def test_control_characters_rejected_before_network(self):
        with patch.object(probe.urllib.request, "build_opener") as factory:
            with self.assertRaises(ValueError):
                probe.probe("malformed", "s" * 32 + "\r\nInjected: value")
            factory.assert_not_called()

    def test_unexpected_header_error_never_exposes_key(self):
        secret = "LOCAL-UNIT-SECRET-" + "x" * 32
        output = io.StringIO()
        with patch.object(probe.sys.stdin, "isatty", return_value=True), \
                patch.object(probe.getpass, "getpass", return_value=secret), \
                patch.object(probe, "probe", side_effect=ValueError(secret)), \
                contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(["--case", "malformed"]), 1)
        self.assertNotIn(secret, output.getvalue())
        self.assertIn("probe_failed_no_details_logged", output.getvalue())

    def test_loopback_no_proxy_no_response_body(self):
        response = Mock(status=403)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.side_effect = AssertionError("Body must never be inspected")
        opener = Mock()
        opener.open.return_value = response
        with patch.object(probe.urllib.request, "build_opener", return_value=opener) as factory:
            result = probe.probe("no-header")
        self.assertTrue(result["passed"])
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:5678/webhook-test/defectrag-ca-local-qa")
        self.assertNotIn("X-defectrag-ca-key", request.headers)
        self.assertEqual(factory.call_args.args[0].proxies, {})
        self.assertIsInstance(factory.call_args.args[1], probe.NoRedirect)
        response.read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
