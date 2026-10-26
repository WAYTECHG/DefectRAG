"""One loopback-only negative probe; never supplies a valid event or sends email.

Use --wait-for-listener to prepare private input before the partial run is armed.
The malformed case privately prompts for a LOCAL-only credential, never argv/env.
Only status metadata is printed; response headers/bodies are not read or logged.
"""
import argparse
import getpass
import json
import sys
import time
import urllib.error
import urllib.request

URL = "http://127.0.0.1:5678/webhook-test/defectrag-ca-local-qa"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_secret(local_secret):
    if (not isinstance(local_secret, str) or not 32 <= len(local_secret) <= 256
            or not all(33 <= ord(char) <= 126 for char in local_secret)):
        raise ValueError("Use a local random secret of 32-256 printable ASCII characters without spaces")


def probe(case, local_secret=None, timeout=12):
    headers = {"Content-Type": "application/json"}
    if case == "wrong-header":
        headers["X-DefectRAG-CA-Key"] = "invalid-local-qa-key"
    elif case == "malformed":
        validate_secret(local_secret)
        headers["X-DefectRAG-CA-Key"] = local_secret
    elif case != "no-header":
        raise ValueError("Unsupported probe")
    # No IDs/capability: validation must stop this before any callback/SMTP node.
    payload = b'{"qa_probe":"malformed_event_no_delivery"}'
    req = urllib.request.Request(URL, data=payload, headers=headers, method="POST")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=max(0.1, min(12, timeout))) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"case": case, "error": "local_endpoint_unavailable", "passed": False}
    result = {"case": case, "http_status": status, "loopback_only": True,
              "response_body_read": False, "valid_event_submitted": False}
    if status == 404:
        result.update(passed=False, error="test_webhook_not_registered",
                      authentication_result="not_tested",
                      next_step="Re-arm Execute step on Validate case event, then immediately retry once")
    elif case in ("no-header", "wrong-header"):
        result["passed"] = status == 403
    elif status in (401, 403):
        result.update(passed=False, error="local_header_credential_not_accepted",
                      authentication_result="rejected")
    else:
        result["passed"] = None
        result["requires_node_check"] = "Confirm Validate case event rejected the schema; HTTP status alone is insufficient"
    return result


def wait_for_listener(wait_seconds=180, check=None, clock=time.monotonic, sleeper=time.sleep):
    """Poll with NO credential; never resend an authenticated request."""
    if not 1 <= wait_seconds <= 180:
        raise ValueError("Listener wait must be bounded to 1-180 seconds")
    check = check or (lambda timeout: probe("no-header", timeout=timeout))
    deadline, checks = clock() + wait_seconds, 0
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            return {"ready": False, "error": "listener_wait_expired", "checks_without_key": checks}
        status = check(min(3, remaining))
        checks += 1
        if status.get("http_status") == 403:
            return {"ready": True, "checks_without_key": checks}
        if status.get("http_status") != 404:
            return {"ready": False, "error": "unexpected_listener_response",
                    "http_status": status.get("http_status"), "checks_without_key": checks}
        sleeper(min(2, max(0, deadline - clock())))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=["no-header", "wrong-header", "malformed"])
    parser.add_argument("--wait-for-listener", action="store_true",
                        help="Wait up to 180s using no-key checks, then submit the private probe once")
    args = parser.parse_args(argv)
    if args.wait_for_listener and args.case != "malformed":
        parser.error("--wait-for-listener is only for the private malformed-event test")
    secret = None
    if args.case == "malformed":
        if not sys.stdin.isatty():
            raise SystemExit("Use a private interactive terminal; do not pass credentials through stdin pipes")
        secret = getpass.getpass("LOCAL QA header credential (hidden): ")
    try:
        readiness = None
        if args.wait_for_listener:
            validate_secret(secret)
            print("Waiting for the LOCAL test listener. Reply 'Probe waiting' in chat; leave this terminal running.", flush=True)
            readiness = wait_for_listener()
        if readiness is not None and not readiness["ready"]:
            output = {"case": args.case, "passed": False, **readiness, "credential_submissions": 0}
        else:
            output = probe(args.case, secret)
            if readiness is not None:
                output.update(checks_without_key=readiness["checks_without_key"], credential_submissions=1)
    except Exception:
        # HTTP-client format exceptions can contain a supplied header value.
        # Never print exception details/tracebacks for the privately entered key.
        output = {"case": args.case, "error": "probe_failed_no_details_logged", "passed": False}
    finally:
        secret = None
    print(json.dumps(output, indent=2))
    return 1 if output.get("passed") is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
