"""Focused TLS-preflight tests; no network or database authentication."""
import importlib.util
from pathlib import Path
import ssl
import struct
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location(
    "supabase_tls_probe", Path(__file__).resolve().parents[1] / "check_supabase_tls.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class TlsPreflightTests(unittest.TestCase):
    def test_offline_parses_real_pinned_ca_without_network(self):
        with patch.object(probe.socket, "create_connection") as connect:
            self.assertFalse(probe.check(offline=True)["database_authentication_attempted"])
            connect.assert_not_called()

    def test_certificate_tampering_denied_before_network(self):
        with patch.object(probe, "CA_SHA256", "0" * 64), patch.object(probe.socket, "create_connection") as connect:
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                probe.check()
            connect.assert_not_called()

    def test_refusal_stops_before_handshake_or_auth(self):
        raw = MagicMock()
        raw.recv.return_value = b"N"
        with patch.object(probe.socket, "create_connection") as connect:
            connect.return_value.__enter__.return_value = raw
            with self.assertRaisesRegex(ValueError, "TLS negotiation"):
                probe.check()
        raw.sendall.assert_called_once_with(struct.pack("!II", 8, 80877103))

    def test_hostname_certificate_failure_never_sends_startup_or_sql(self):
        raw = MagicMock()
        raw.recv.return_value = b"S"
        context = MagicMock()
        context.cert_store_stats.return_value = {"x509_ca": 1}
        context.wrap_socket.side_effect = ssl.SSLCertVerificationError("untrusted")
        with patch.object(probe.socket, "create_connection") as connect, patch.object(probe.ssl, "create_default_context", return_value=context):
            connect.return_value.__enter__.return_value = raw
            with self.assertRaises(ssl.SSLCertVerificationError):
                probe.check()
        context.wrap_socket.assert_called_once_with(raw, server_hostname=probe.HOST)
        raw.sendall.assert_called_once_with(struct.pack("!II", 8, 80877103))


if __name__ == "__main__":
    unittest.main()
