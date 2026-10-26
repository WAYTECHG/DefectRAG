"""Verify the project pooler's TLS before any database login. Standard library only.

Sends ONLY PostgreSQL's eight-byte SSLRequest, never a StartupMessage, user,
password or SQL. --offline validates the pinned public CA without networking.
"""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import ssl
import struct

HOST = "aws-0-ap-northeast-1.pooler.supabase.com"
CA_SHA256 = "700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7"
CA = Path(__file__).parent / "certificates" / "supabase-prod-ca-2021.crt"


def check(offline=False):
    if hashlib.sha256(CA.read_bytes()).hexdigest() != CA_SHA256:
        raise ValueError("Public CA fingerprint changed; review the official certificate before use")
    context = ssl.create_default_context(cafile=str(CA))
    if not context.cert_store_stats()["x509_ca"]:
        raise ValueError("Certificate file contains no trusted CA")
    result = {"ca_sha256": CA_SHA256, "database_authentication_attempted": False,
              "certificate_and_hostname_verified": False, "offline": offline}
    if not offline:
        with socket.create_connection((HOST, 5432), timeout=15) as raw:
            raw.sendall(struct.pack("!II", 8, 80877103))
            if raw.recv(1) != b"S":
                raise ValueError("Pooler did not accept PostgreSQL TLS negotiation")
            with context.wrap_socket(raw, server_hostname=HOST) as secured:
                result.update(certificate_and_hostname_verified=True,
                              tls_version=secured.version(), host=HOST)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.offline)))
    except (OSError, ValueError) as error:
        parser.exit(1, f"TLS preflight failed before database authentication: {error}\n")
