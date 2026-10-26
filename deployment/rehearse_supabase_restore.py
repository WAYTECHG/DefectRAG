"""Restore the owner's encrypted-export payload ONLY in an isolated container.

Called by restore_private_backup.ps1 over a binary stdin pipe. No production
connection or host mounts. Private dump/SQL/error payloads never reach stdout.
With the recovery supplement and --native-auth, verifies actual Vault/native
TOTP recovery and original object metadata; parent validates every object byte.
This never restores production or clones the full hosted platform configuration.
"""
import json
import re
import struct
import subprocess
import sys
import time
import uuid

IMAGE = "supabase/postgres@sha256:f371b5f3f2ac0a05703f33d6e6134515fb2498cab708fb948a0aeb7481467c00"
RESTORE_ADMIN = "supabase_admin"


def command(*args, data=None, timeout=120):
    return subprocess.run(["docker", *args], input=data, capture_output=True, timeout=timeout)


def read_payload():
    header = sys.stdin.buffer.read(8)
    if len(header) != 8:
        raise ValueError("Missing private pipe header")
    size = struct.unpack("<Q", header)[0]
    if not 0 < size <= 256 * 1024 * 1024:
        raise ValueError("Unexpected backup payload length")
    value = sys.stdin.buffer.read(size)
    if len(value) != size:
        raise ValueError("Incomplete private pipe payload")
    return value


def safe_errors(value):
    # Classify only, never expose raw SQL, row values or provider credentials.
    text = value.decode("utf8", errors="replace")
    categories = ("already exists", "does not exist", "not available", "must be loaded",
                  "permission denied", "must be superuser", "could not open", "syntax error",
                  "not found", "could not access", "configuration parameter", "extension",
                  "admin option", "reserved role", "grant role", "create role")
    return [kind for kind in categories if kind in text.lower()] or ["private_error_redacted"]


def copy_counts(sql_bytes):
    """Count COPY rows without returning any private row values."""
    counts = {}
    current = None
    for line in sql_bytes.decode("utf8").splitlines():
        match = re.match(r'^COPY ([a-z_0-9]+)\.([a-z_0-9]+) \(.*\) FROM stdin;$', line)
        if match:
            current = match[1] + "." + match[2]
            if current in counts:
                raise ValueError("Duplicate COPY section")
            counts[current] = 0
        elif current and line == r"\.":
            current = None
        elif current:
            counts[current] += 1
    if current:
        raise ValueError("Truncated COPY section")
    return counts


def copy_row_fingerprints(sql_bytes):
    """Private row bytes stay in memory; compare sorted COPY rows by table."""
    import hashlib
    sections = {}
    current = None
    for line in sql_bytes.splitlines():
        match = re.match(rb'^COPY ([a-z_0-9]+)\.([a-z_0-9]+) \(.*\) FROM stdin;$', line)
        if match:
            current = (match[1] + b"." + match[2]).decode()
            if current in sections:
                raise ValueError("Duplicate COPY section")
            sections[current] = []
        elif current and line == b"\\.":
            current = None
        elif current:
            sections[current].append(line)
    if current:
        raise ValueError("Truncated COPY section")
    return {table: hashlib.sha256(b"\n".join(sorted(rows))).digest() for table, rows in sections.items()}


def recovery_tables(expected_counts):
    """Include optional later milestones when present in this actual archive."""
    selected = ["public.shared_inspections", "public.staff_notes", "public.personal_inspections",
                "public.personal_notes", "public.staff_members", "public.staff_access_requests",
                "public.defectrag_gallery_entries", "auth.users", "auth.mfa_factors", "storage.objects"]
    selected.extend(table for table in (
        "public.corrective_action_settings", "public.corrective_actions",
        "public.corrective_action_history", "public.corrective_action_events",
        "public.corrective_action_effects", "public.corrective_action_qa_runs",
        "public.staff_notification_outbox", "public.personal_sync_receipts",
    ) if table in expected_counts)
    return selected


def reuse_bootstrap_role(roles):
    """The original Supabase grantor must be PostgreSQL's bootstrap role.

    PostgreSQL17 allows this bootstrap role to grant memberships without
    separate ADMIN-option edges. Recreating it as an ordinary second superuser
    changes that behavior. Reuse the initdb-created role; preserve every ALTER
    ROLE and every original GRANT/GRANTED BY statement unchanged.
    """
    text = roles.decode("utf8")
    if not re.search(r'(?m)^ALTER ROLE supabase_admin WITH SUPERUSER\b', text):
        raise ValueError("Archived bootstrap role contract differs; stop for review")
    result, count = re.subn(r'(?m)^CREATE ROLE supabase_admin;\r?$', '', text)
    if count != 1:
        raise ValueError("Expected one archived bootstrap-role CREATE statement")
    return result.encode("utf8")


def main():
    archive, roles = read_payload(), read_payload()
    if set(sys.argv[1:]) - {"--with-recovery", "--native-auth"}:
        raise ValueError("Unsupported rehearsal option")
    with_recovery = "--with-recovery" in sys.argv[1:]
    native_auth = "--native-auth" in sys.argv[1:]
    if native_auth and not with_recovery:
        raise ValueError("Native Auth requires recovery supplement")
    root_key = read_payload() if with_recovery else None
    inventory = json.loads(read_payload()) if with_recovery else None
    if root_key is not None and not re.fullmatch(b"[0-9a-fA-F]{64}", root_key):
        raise ValueError("Invalid private recovery key format")
    if not archive.startswith(b"PGDMP"):
        raise ValueError("Unexpected archive header")
    if command("image", "inspect", IMAGE).returncode:
        raise ValueError("Reviewed Supabase image missing; no automatic download")
    name = "defectrag-private-restore-" + uuid.uuid4().hex[:12]
    report = {"status": "not_restored", "image": IMAGE, "network": "none",
              "host_mounts": False, "published_ports": False,
              "cron_jobs_launched": False, "production_connection": False,
              "native_auth_mfa_verified": False, "storage_bytes_verified": False,
              "root_encryption_key_verified": False}
    created = False
    try:
        # No vendor bootstrap schemas: restore the original schemas/roles into
        # a fresh cluster with vendor extensions and the matching bootstrap
        # superuser. Cron is disabled even though it is restored as data.
        wait_for_key = "while ! test -f /tmp/recovery-key-ready; do sleep 0.1; done; " if with_recovery else ""
        vault_config = " -c vault.getkey_script=/tmp/recovery-root-key.sh" if with_recovery else ""
        preload = "pg_cron,pg_stat_statements,pg_net" + (",supabase_vault" if with_recovery else "")
        listen = "127.0.0.1" if native_auth else "''"
        launch = command("run", "-d", "--pull", "never", "--network", "none",
                         "--name", name, "--user", "postgres", "--cap-drop", "ALL",
                         "--security-opt", "no-new-privileges", "--memory", "1g", "--cpus", "2",
                         "--entrypoint", "sh", IMAGE, "-c",
                         "initdb -D /tmp/restore-data -U supabase_admin --auth=trust >/tmp/init.log 2>&1 && " + wait_for_key +
                         "exec postgres -D /tmp/restore-data -k /tmp -c listen_addresses=" + listen + " " +
                         "-c shared_preload_libraries=" + preload + " " +
                         "-c cron.database_name=postgres -c cron.launch_active_jobs=off "
                         "-c wal_level=logical -c log_statement=none -c session_preload_libraries=''" + vault_config)
        if launch.returncode:
            report.update(status="container_start_failed", error_categories=safe_errors(launch.stderr))
            return report
        created = True
        if with_recovery:
            # Existing root key reaches only this disposable offline container
            # via stdin. It never appears in arguments, env or host plaintext.
            supplied = command("exec", "-i", name, "sh", "-c",
                               "umask 077; cat > /tmp/recovery-root.key && "
                               "printf '#!/bin/sh\\ncat /tmp/recovery-root.key\\n' > /tmp/recovery-root-key.sh && "
                               "chmod 700 /tmp/recovery-root-key.sh && touch /tmp/recovery-key-ready",
                               data=root_key)
            if supplied.returncode:
                report["status"] = "isolated_key_input_failed"
                return report
        for _ in range(30):
            if command("exec", name, "pg_isready", "-h", "/tmp", "-U", RESTORE_ADMIN).returncode == 0:
                break
            time.sleep(1)
        else:
            log = command("logs", name)
            report.update(status="database_start_failed", error_categories=safe_errors(log.stderr + log.stdout))
            return report

        def sql(query):
            return command("exec", "-i", name, "psql", "-X", "-h", "/tmp", "-U", RESTORE_ADMIN,
                           "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-At", data=query.encode("utf8"))

        restore_roles = command("exec", "-i", name, "psql", "-X", "-h", "/tmp", "-U", RESTORE_ADMIN,
                                "-d", "postgres", "-1", "-v", "ON_ERROR_STOP=1", data=reuse_bootstrap_role(roles))
        if restore_roles.returncode:
            report.update(status="role_restore_failed", error_categories=safe_errors(restore_roles.stderr))
            return report
        report["bootstrap_role_reused"] = RESTORE_ADMIN
        report["archived_role_grantors_preserved"] = True
        report["local_only_membership_grantors_rebound"] = 0
        report["original_role_membership_statements_replayed"] = len(re.findall(rb'(?m)^GRANT [^;\r\n]+;', roles))
        report["global_roles_restored"] = True
        restored = command("exec", "-i", "--env", "PGOPTIONS=-c session_replication_role=replica",
                           name, "pg_restore", "--exit-on-error", "--single-transaction", "-h", "/tmp",
                           "-U", RESTORE_ADMIN, "-d", "postgres", data=archive)
        if restored.returncode:
            report.update(status="database_restore_failed", error_categories=safe_errors(restored.stderr))
            # Only schema/extension identifiers from the error class are public
            # metadata. Never return a quoted row value or statement body.
            error_text = restored.stderr.decode("utf8", errors="replace")
            report["missing_extensions"] = sorted(set(re.findall(r'extension "([a-z_0-9-]+)" is not available', error_text)))
            # Schema-phase extension diagnostics only; whitelist identifiers
            # and redact all other quoted strings, never SQL command/context.
            allowed = {"pg_cron", "pg_net", "pg_stat_statements", "pgcrypto", "supabase_vault", "uuid-ossp", "pgsodium"}
            details = []
            for line in error_text.splitlines():
                if "ERROR:" in line and "extension" in line:
                    message = line.split("ERROR:", 1)[1].strip()
                    message = re.sub(r'"([^"\n]+)"', lambda m: m.group(0) if m.group(1) in allowed else '"[redacted]"', message)
                    message = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+|[a-fA-F0-9]{24,}", "[redacted]", message)
                    details.append(message[:180])
            report["extension_error_metadata"] = details[:1]
            first_line = error_text.splitlines()[0] if error_text else "no diagnostic"
            first_line = re.sub(r'"[^"\n]+"|\'[^\'\n]+\'|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+|[a-fA-F0-9]{24,}', '[redacted]', first_line)
            report["first_error_classification"] = first_line[:220]
            return report
        report["database_archive_restored"] = True
        source_data = command("exec", "-i", name, "pg_restore", "--data-only", "--file", "-", data=archive)
        if source_data.returncode:
            report["status"] = "source_count_extraction_failed"
            return report
        expected_counts = copy_counts(source_data.stdout)
        selected = recovery_tables(expected_counts)
        counts = {}
        for table in selected:
            result = sql(f"SELECT count(*) FROM {table};")
            if result.returncode:
                report.update(status="post_restore_count_failed", error_categories=safe_errors(result.stderr))
                return report
            counts[table] = int(result.stdout.strip())
        source_matches = {table: counts[table] == expected_counts.get(table) for table in selected}
        report["counts_match_encrypted_archive"] = source_matches
        if not all(source_matches.values()):
            report["status"] = "restored_count_mismatch"
            return report
        source_fingerprints = copy_row_fingerprints(source_data.stdout)
        dump_args = ["exec", name, "pg_dump", "-h", "/tmp", "-U", RESTORE_ADMIN, "-d", "postgres", "--data-only"]
        for table in selected + ["vault.secrets"]:
            dump_args.extend(["--table", table])
        restored_data = command(*dump_args)
        if restored_data.returncode:
            report["status"] = "restored_content_read_failed"
            return report
        fingerprints = copy_row_fingerprints(restored_data.stdout)
        content_matches = {table: fingerprints.get(table) == source_fingerprints.get(table) and table in fingerprints
                           for table in selected + ["vault.secrets"]}
        report["restored_row_content_matches_archive_before_auth_test"] = content_matches
        if not all(content_matches.values()):
            report["status"] = "restored_row_content_mismatch"
            return report
        checks = sql("SELECT json_build_object('cron_disabled',current_setting('cron.launch_active_jobs')='off',"
                     "'personal_rls',(SELECT relrowsecurity FROM pg_class WHERE oid='public.personal_inspections'::regclass),"
                     "'team_rls',(SELECT relrowsecurity FROM pg_class WHERE oid='public.shared_inspections'::regclass),"
                     "'policies',(SELECT count(*) FROM pg_policy),"
                     "'registration_enabled',(SELECT registration_enabled FROM public.defectrag_auth_settings WHERE singleton),"
                     "'mfa_required',(SELECT mfa_required FROM public.defectrag_auth_settings WHERE singleton));")
        if checks.returncode:
            report.update(status="post_restore_metadata_failed", error_categories=safe_errors(checks.stderr))
            return report
        report.update(status="database_rehearsal_passed_remaining_recovery_gates", restored_counts=counts,
                      metadata=json.loads(checks.stdout))
        if with_recovery:
            # Fetch only metadata in memory, never return object paths/IDs or
            # any Vault plaintext from the private rehearsal.
            metadata = sql("SELECT coalesce(json_agg(json_build_object('bucket',bucket_id,'path',name,'id',id,'metadata',metadata)),'[]') FROM storage.objects;")
            if metadata.returncode:
                report["status"] = "storage_metadata_read_failed"
                return report
            original_objects = json.loads(metadata.stdout)
            backed_up = {(obj["bucket"], obj["path"]): obj for obj in inventory["objects"]}
            original = {(obj["bucket"], obj["path"]): obj for obj in original_objects}
            exact_paths = len(backed_up) == len(inventory["objects"]) and backed_up.keys() == original.keys()
            exact_ids = exact_paths and all(str(backed_up[key]["metadata"]["id"]) == str(original[key]["id"]) for key in original)
            exact_sizes = exact_paths and all(backed_up[key]["plaintext_bytes"] == original[key]["metadata"]["size"] for key in original)
            report["storage_snapshot_checks"] = {"paths_match": exact_paths, "ids_match": exact_ids, "sizes_match": exact_sizes,
                                                "objects": len(backed_up), "decrypted_file_sha256_checks": "passed_by_parent"}
            report["storage_bytes_verified"] = exact_paths and exact_ids and exact_sizes
            vault = sql("SELECT json_build_object('encrypted_rows',(SELECT count(*) FROM vault.secrets),"
                        "'decryptable_rows',count(*),'all_nonempty',coalesce(bool_and(length(decrypted_secret)>0),false)) FROM vault.decrypted_secrets;")
            if vault.returncode:
                report.update(status="vault_recovery_failed", vault_error_categories=safe_errors(vault.stderr))
                return report
            vault_result = json.loads(vault.stdout)
            report["vault_recovery"] = vault_result
            report["root_encryption_key_verified"] = vault_result["encrypted_rows"] > 0 and vault_result["encrypted_rows"] == vault_result["decryptable_rows"] and vault_result["all_nonempty"]
            factors = sql("SELECT json_build_object('verified_totp_factors',count(*),"
                          "'base32_seed_rows',count(*) FILTER (WHERE secret ~ '^[A-Z2-7]+=*$')) "
                          "FROM auth.mfa_factors WHERE factor_type='totp' AND status='verified';")
            if factors.returncode == 0:
                report["restored_factor_metadata"] = json.loads(factors.stdout)
            if not report["storage_bytes_verified"] or not report["root_encryption_key_verified"]:
                report["status"] = "supplement_recovery_incomplete"
            elif native_auth:
                from native_auth_recovery import check_native_auth
                report["native_auth_recovery"] = check_native_auth(command, name, sql)
                report["native_auth_mfa_verified"] = report["native_auth_recovery"]["passed"]
                if not report["native_auth_mfa_verified"]:
                    report["status"] = "native_auth_recovery_failed"
        return report
    finally:
        if created:
            # Exact unique disposable container created above only, never an
            # existing user's database, n8n container, volume or backup file.
            cleanup = command("rm", "-f", "-v", name)
            report["disposable_container_removed"] = cleanup.returncode == 0


if __name__ == "__main__":
    try:
        outcome = main()
        print(json.dumps(outcome))
        sys.exit(0 if outcome["status"] == "database_rehearsal_passed_remaining_recovery_gates" else 1)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        print(json.dumps({"status": "rehearsal_failed", "private_error_details": "not displayed"}))
        sys.exit(1)
