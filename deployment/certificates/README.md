# Supabase public certificate authority

`supabase-prod-ca-2021.crt` is PUBLIC trust material, not a credential.
Downloaded over verified HTTPS on 24 October 2026 from the **Download certificate**
link in the actual project's Database Settings:

https://supabase-downloads.s3-ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt

File SHA256: `700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7`.
The helpers pin this reviewed fingerprint and bind-mount it read-only into Docker
as `/certs/supabase-ca.crt`. libpq retains `sslmode=verify-full`.

The credential-free preflight verifies the actual Session pooler certificate
chain and hostname using this CA. It sends only the PostgreSQL SSLRequest; no
startup/authentication message, password or SQL is sent. TLS1.3 passed live on
24 October 2026. This does not prove database authentication, export permissions
or backup restorability. Future CA rotation requires reviewing the official link,
certificate and updating the pins; do not bypass validation on a mismatch.

See [Supabase TLS guidance](https://supabase.com/docs/guides/database/psql).
