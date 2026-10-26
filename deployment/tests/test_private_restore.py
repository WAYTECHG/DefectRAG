"""Focused no-network tests of private restore framing/counts/redaction."""
import importlib.util
import io
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "private_restore", Path(__file__).resolve().parents[1] / "rehearse_supabase_restore.py")
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


class PrivateRestoreTests(unittest.TestCase):
    def test_current_case_ledger_and_outbox_are_verified_when_backed_up(self):
        tables = restore.recovery_tables({"public.corrective_actions": 1,
            "public.corrective_action_events": 9, "public.corrective_action_effects": 0,
            "public.staff_notification_outbox": 6, "public.personal_sync_receipts": 4})
        for name in ("public.corrective_actions", "public.corrective_action_events",
                     "public.corrective_action_effects", "public.staff_notification_outbox",
                     "public.personal_sync_receipts"):
            self.assertIn(name, tables)
        self.assertNotIn("public.corrective_action_qa_runs", tables)

    def test_bootstrap_reuse_preserves_exact_original_permissions_and_grantor(self):
        roles = b'CREATE ROLE supabase_admin;\nALTER ROLE supabase_admin WITH SUPERUSER INHERIT;\nCREATE ROLE anon;\nGRANT anon TO postgres GRANTED BY supabase_admin;\n'
        restored = restore.reuse_bootstrap_role(roles)
        self.assertNotIn(b'CREATE ROLE supabase_admin;', restored)
        self.assertIn(b'ALTER ROLE supabase_admin WITH SUPERUSER INHERIT;', restored)
        self.assertIn(b'GRANT anon TO postgres GRANTED BY supabase_admin;', restored)

    def test_bootstrap_contract_changes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'contract differs'):
            restore.reuse_bootstrap_role(b'CREATE ROLE supabase_admin;\nALTER ROLE supabase_admin WITH NOSUPERUSER;\n')

    def test_private_row_content_comparison_ignores_order_but_detects_changes(self):
        first = b'COPY auth.users (id) FROM stdin;\nfirst\nsecond\n\\.\n'
        reordered = b'COPY auth.users (id) FROM stdin;\nsecond\nfirst\n\\.\n'
        changed = b'COPY auth.users (id) FROM stdin;\nsecond\nthird\n\\.\n'
        self.assertEqual(restore.copy_row_fingerprints(first), restore.copy_row_fingerprints(reordered))
        self.assertNotEqual(restore.copy_row_fingerprints(first), restore.copy_row_fingerprints(changed))
    def test_copy_count_handles_escaped_newlines_and_empty_tables(self):
        fixture = b'COPY public.personal_inspections (id, note) FROM stdin;\n1\tline\\nline\n2\t\\N\n\\.\nCOPY auth.users (id) FROM stdin;\n\\.\n'
        self.assertEqual(restore.copy_counts(fixture), {"public.personal_inspections": 2, "auth.users": 0})

    def test_truncated_or_duplicate_data_is_denied(self):
        with self.assertRaisesRegex(ValueError, "Truncated"):
            restore.copy_counts(b'COPY auth.users (id) FROM stdin;\nrow\n')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            restore.copy_counts(b'COPY auth.users (id) FROM stdin;\n\\.\nCOPY auth.users (id) FROM stdin;\n\\.\n')

    def test_private_payload_is_not_in_error_classification(self):
        output = restore.safe_errors(b'ERROR: permission denied; private-person@example.invalid SECRET_VALUE')
        self.assertEqual(output, ["permission denied"])

    def test_pipe_length_guard_rejects_truncation_before_any_command(self):
        stream = type("Input", (), {"buffer": io.BytesIO(struct.pack("<Q", 8) + b"short")})()
        with patch.object(restore.sys, "stdin", stream), patch.object(restore, "command") as command:
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                restore.read_payload()
            command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
