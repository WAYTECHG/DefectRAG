"""Synthetic cryptographic vectors only; no real seeds, tokens or networking."""
import base64
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('native_recovery', Path(__file__).resolve().parents[1] / 'native_auth_recovery.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeRecoveryTests(unittest.TestCase):
    def test_rfc6238_sha1_vector_six_digit_truncation(self):
        seed = base64.b32encode(b'12345678901234567890').decode().rstrip('=')
        self.assertEqual(native.totp(seed, 59), '287082')
        self.assertEqual(native.totp(seed, 1111111109), '081804')

    def test_claims_are_checked_against_the_local_signing_key(self):
        token = native.encode_jwt({'aal': 'aal2'}, 'SYNTHETIC-KEY-ONLY')
        self.assertEqual(native.verified_claims(token, 'SYNTHETIC-KEY-ONLY')['aal'], 'aal2')
        with self.assertRaisesRegex(ValueError, 'signature'):
            native.verified_claims(token, 'DIFFERENT-SYNTHETIC-KEY')


if __name__ == '__main__':
    unittest.main()
