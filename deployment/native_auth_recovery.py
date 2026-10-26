"""Native Auth/TOTP recovery test ONLY inside an existing network=none container.

Uses the restored QA Staff identity/factor internally. Passwords, seed values,
email links, codes and JWTs never leave memory/output into reports. No password
login is claimed: a local-only admin-generated magic link establishes the AAL1
session, then the original backed-up TOTP factor must pass native verification.
"""
import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
import uuid

AUTH_IMAGE = "supabase/gotrue@sha256:1736a63078f5922b198c4cbe50f80ab9a2d3b54fe8b7b6cfb2e9dc5dbbc12c6b"


def encode_jwt(claims, key):
    def part(value):
        return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=")
    signed = part({"alg": "HS256", "typ": "JWT"}) + b"." + part(claims)
    signature = base64.urlsafe_b64encode(hmac.new(key.encode(), signed, hashlib.sha256).digest()).rstrip(b"=")
    return (signed + b"." + signature).decode()


def verified_claims(token, key):
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid local native JWT")
    expected = hmac.new(key.encode(), (parts[0] + "." + parts[1]).encode(), hashlib.sha256).digest()
    actual = base64.urlsafe_b64decode(parts[2] + "=" * (-len(parts[2]) % 4))
    if not hmac.compare_digest(expected, actual):
        raise ValueError("Invalid local native JWT signature")
    return json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))


def totp(seed, timestamp):
    key = base64.b32decode(seed + "=" * (-len(seed) % 8), casefold=True)
    digest = hmac.new(key, struct.pack("!Q", int(timestamp) // 30), hashlib.sha1).digest()
    offset = digest[-1] & 15
    return f"{(struct.unpack('!I', digest[offset:offset+4])[0] & 0x7fffffff) % 1000000:06d}"


def check_native_auth(command, name, sql):
    report = {"auth_image": AUTH_IMAGE, "passed": False, "production_access": False,
              "emails_sent": False, "existing_password_login_tested": False,
              "session_method": "local_native_admin_generated_magiclink_no_email"}
    if command("image", "inspect", AUTH_IMAGE).returncode:
        report["stage"] = "auth_image_not_cached"
        return report
    source_name = "defectrag-auth-binary-" + uuid.uuid4().hex[:12]
    created = False
    try:
        if command("create", "--name", source_name, AUTH_IMAGE).returncode:
            report["stage"] = "auth_binary_source_failed"
            return report
        created = True
        for source in ("/usr/local/bin/auth", "/usr/local/etc/auth/migrations"):
            archive = command("cp", source_name + ":" + source, "-")
            if archive.returncode or command("exec", "-i", name, "tar", "-x", "--no-same-owner", "-C", "/tmp", data=archive.stdout).returncode:
                report["stage"] = "auth_binary_copy_failed"
                return report
        key = secrets.token_urlsafe(48)  # New disposable runtime key, never the project signing key.
        config = {
            "API_EXTERNAL_URL": "http://127.0.0.1:9999",
            "GOTRUE_API_HOST": "127.0.0.1", "GOTRUE_API_PORT": "9999",
            "GOTRUE_DB_DRIVER": "postgres",
            "GOTRUE_DB_DATABASE_URL": "postgres://supabase_auth_admin@127.0.0.1:5432/postgres?sslmode=disable",
            "GOTRUE_DB_MIGRATIONS_PATH": "/tmp/migrations",
            "GOTRUE_SITE_URL": "http://127.0.0.1:9999", "GOTRUE_DISABLE_SIGNUP": "true",
            "GOTRUE_JWT_SECRET": key, "GOTRUE_JWT_AUD": "authenticated",
            "GOTRUE_JWT_ADMIN_ROLES": "service_role", "GOTRUE_JWT_DEFAULT_GROUP_NAME": "authenticated",
            "GOTRUE_EXTERNAL_EMAIL_ENABLED": "true", "GOTRUE_MAILER_AUTOCONFIRM": "false",
            "GOTRUE_MFA_TOTP_ENROLL_ENABLED": "true", "GOTRUE_MFA_TOTP_VERIFY_ENABLED": "true",
            "GOTRUE_LOG_LEVEL": "error",
        }
        import shlex
        launcher = "#!/bin/sh\n" + "\n".join("export " + k + "=" + shlex.quote(v) for k, v in config.items()) + "\nexec /tmp/auth\n"
        installed = command("exec", "-i", name, "sh", "-c", "umask 077; cat > /tmp/native-auth-start.sh; chmod 700 /tmp/native-auth-start.sh", data=launcher.encode())
        if installed.returncode or command("exec", "-d", name, "sh", "-c", "/tmp/native-auth-start.sh >/tmp/native-auth.log 2>&1").returncode:
            report["stage"] = "auth_start_failed"
            return report

        def request(method, path, payload=None, token=None):
            # curl receives sensitive test values through stdin config only.
            lines = ["silent", "show-error", "max-time = 10", "request = " + json.dumps(method),
                     "url = " + json.dumps("http://127.0.0.1:9999" + path),
                     'header = "Content-Type: application/json"', 'write-out = "\\n%{http_code}"']
            if token:
                lines.append("header = " + json.dumps("Authorization: Bearer " + token))
            if payload is not None:
                lines.append("data = " + json.dumps(json.dumps(payload)))
            result = command("exec", "-i", name, "curl", "--config", "-", data=("\n".join(lines) + "\n").encode())
            if result.returncode:
                return 0, {}
            body, status = result.stdout.rsplit(b"\n", 1)
            try:
                return int(status), json.loads(body)
            except (ValueError, TypeError):
                return int(status), {}

        for _ in range(30):
            if request("GET", "/health")[0] == 200:
                break
            time.sleep(0.5)
        else:
            report["stage"] = "auth_health_failed"
            return report
        candidate = sql("SELECT json_build_object('email',u.email,'factor_id',f.id,'seed',f.secret) "
                        "FROM public.staff_members s JOIN auth.users u ON u.id=s.user_id "
                        "JOIN auth.mfa_factors f ON f.user_id=u.id WHERE s.role='staff' AND s.revoked_at IS NULL "
                        "AND f.factor_type='totp' AND f.status='verified' AND u.email_confirmed_at IS NOT NULL LIMIT 1;")
        if candidate.returncode or not candidate.stdout.strip():
            report["stage"] = "restored_qa_factor_not_available"
            return report
        qa = json.loads(candidate.stdout)
        admin = encode_jwt({"role": "service_role", "aud": "authenticated", "iat": int(time.time()), "exp": int(time.time()) + 600}, key)
        status, link = request("POST", "/admin/generate_link", {"type": "magiclink", "email": qa["email"]}, admin)
        report["local_link_generation_http"] = status
        if status != 200:
            report["stage"] = "local_link_generation_failed"
            return report
        status, session = request("POST", "/verify", {"type": "magiclink", "token_hash": link.get("hashed_token")})
        report["native_session_http"] = status
        if status != 200 or not session.get("access_token"):
            report["stage"] = "native_session_failed"
            return report
        token = session["access_token"]
        aal1 = verified_claims(token, key)
        report["native_aal1"] = aal1.get("aal") == "aal1"

        def staff_allowed(claims):
            literal = json.dumps(claims).replace("'", "''")
            result = sql("BEGIN; SET LOCAL ROLE authenticated; SET LOCAL request.jwt.claims='" + literal + "'; "
                         "SELECT public.defectrag_is_staff(); ROLLBACK;")
            if result.returncode:
                return None  # A query failure is never evidence of authorization denial.
            return b"t" in result.stdout.splitlines()

        report["restored_staff_helper_denies_aal1"] = staff_allowed(aal1) is False
        factor = "/factors/" + str(qa["factor_id"])
        status, challenge = request("POST", factor + "/challenge", {}, token)
        if status != 200:
            report.update(stage="native_challenge_failed", native_challenge_http=status)
            return report
        now = time.time()
        valid_window = {totp(qa["seed"], now + step * 30) for step in range(-2, 3)}
        invalid = next(f"{code:06d}" for code in range(100) if f"{code:06d}" not in valid_window)
        status, _ = request("POST", factor + "/verify", {"challenge_id": challenge["id"], "code": invalid}, token)
        report["invalid_totp_rejected"] = status in (400, 401, 403, 422)
        report["invalid_totp_http"] = status
        status, challenge = request("POST", factor + "/challenge", {}, token)
        if status != 200:
            report.update(stage="second_native_challenge_failed", native_challenge_http=status)
            return report
        status, upgraded = request("POST", factor + "/verify", {"challenge_id": challenge["id"], "code": totp(qa["seed"], time.time())}, token)
        report["valid_totp_http"] = status
        if status != 200 or not upgraded.get("access_token"):
            report["stage"] = "valid_native_totp_failed"
            return report
        aal2 = verified_claims(upgraded["access_token"], key)
        report["native_aal2"] = aal2.get("aal") == "aal2"
        report["restored_staff_helper_accepts_aal2"] = staff_allowed(aal2)
        report["passed"] = all(report.get(field) is True for field in (
            "native_aal1", "restored_staff_helper_denies_aal1", "invalid_totp_rejected",
            "native_aal2", "restored_staff_helper_accepts_aal2"))
        report["stage"] = "native_totp_recovery_passed" if report["passed"] else "native_totp_boundary_failed"
        return report
    finally:
        if created:
            command("rm", "-v", source_name)  # Exact new binary-source container only.
