# Community demo gallery

An optional public gallery lets visitors inspect without signing up, then
explicitly publish a separate snapshot. Closing a browser does not remove a
published snapshot stored in Supabase. Normal inspection history remains private.

## What becomes public

| Shared after consent | Remains private |
| --- | --- |
| Resized image and measured heatmap | Original private inspection ID and filename |
| Product category, verdict, score, threshold, model metadata | Batch label, account identity, conversations |
| Random public ID and publication time | Staff notes, review decisions, signed artifact URLs |

Previews are newly encoded JPEGs, at most 512 pixels on the longest edge, without
EXIF. Visible personal details or text **inside** an image are not redacted.
Visitors must have permission to share the image. Do not publish sensitive images.
No historical/private inspection is automatically added to this gallery.

## Setup: manual database change and one dedicated Space secret

The source SQL is [deployment/supabase_public_gallery.sql](../deployment/supabase_public_gallery.sql).
It does not modify existing staff tables, records, policies, RPCs or storage.
No database operation is executed by the preparation script.

From the existing application folder in PowerShell:

```powershell
Set-Location 'C:\Users\User\Desktop\DefectRAG-v2'
.\deployment\Prepare-Gallery.ps1
```

The script generates a separate random 256-bit gallery capability and writes:

- `runtime/gallery-setup/gallery-setup.sql`: complete migration plus key configuration.
- `runtime/gallery-setup/gallery-key.txt`: same private key for HF Settings.

Rerunning preserves the existing key. Keep these generated files private; runtime
is excluded from Git. No Supabase service-role key/database password is needed.

1. Review `deployment/supabase_public_gallery.sql`, and the generated setup SQL.
2. Copy **the generated** `runtime/gallery-setup/gallery-setup.sql` into the
   existing Supabase project's SQL Editor and execute manually as project owner.
3. In [Hugging Face Space settings](https://huggingface.co/spaces/Wizzas/DefectRAG/settings),
   add **Secret** `DEFECTRAG_GALLERY_KEY`, with the content of `gallery-key.txt`.
   This must be a secret, never a public Space variable or frontend config value.
4. Add **Variable** `DEFECTRAG_GALLERY_ENABLED` with value `1`.
5. Restart the Space after the new application version is deployed.
6. Confirm successful execution/settings in this conversation for the remaining
   real hosted publishing, second-visitor visibility and withdrawal verification.

Optional clipboard commands, run locally without posting their contents in chat:

```powershell
Get-Content -Raw '.\runtime\gallery-setup\gallery-setup.sql' | Set-Clipboard
# Paste in Supabase SQL Editor, review and Run.
Get-Content -Raw '.\runtime\gallery-setup\gallery-key.txt' | Set-Clipboard
# Paste in the HF Secret value field, then save.
```

Until configured, the gallery shows a setup notice and publishing is disabled.
The cloud build never silently substitutes temporary SQLite for durable storage.
Setting the variable back to `0` disables gallery access without deleting data.

## Permissions and security

Three new tables store public snapshots, pseudonymous publisher/source hashes,
and a SHA-256 hash of the gallery key. All have RLS enabled; `PUBLIC`, `anon` and
`authenticated` have **no direct table privileges**.

| Function | Caller and effect |
| --- | --- |
| `defectrag_gallery_configure` | Project owner in SQL Editor only. Stores the secret hash. Revoked from public/anon/authenticated. |
| `defectrag_gallery_read` | Anonymous or authenticated API clients. Returns visible public snapshots only; pages omit image blobs. Never reads staff tables. |
| `defectrag_gallery_write` | Requires the dedicated server-only gallery key for every status/write/removal. Uses HMAC publisher/source hashes computed by the backend. Cannot access staff tables through its fixed SQL. |

Functions require `SECURITY DEFINER` to access the otherwise inaccessible gallery
tables. Each fixes `search_path` to empty and schema-qualifies application tables.
The backend validates browser/staff context, resolves an existing saved inspection,
checks original staff ownership, extracts an explicit measurement allowlist and
re-encodes the server-saved image/heatmap. It accepts **no client scores/images**
on the publication endpoint. Publishing does not run inference or spend GPU quota.

Supabase publishable API keys are sent only on `apikey`; they are not user JWTs.
References: [Supabase API keys](https://supabase.com/docs/guides/getting-started/api-keys),
[database function permissions](https://supabase.com/docs/guides/database/functions).

The dedicated capability can manage **only gallery data through these functions**.
It is never included in React, public config, logs or committed setup files. If
exposed, rotate it using SQL Editor and HF Settings; existing HMAC publisher links
will no longer match, so maintainers must moderate old items. Preserve the key for
normal restarts and upgrades. Database admins retain full project access.

## Withdrawal, moderation and limits

- The uploader can withdraw using the original guest browser workspace, or the
  same approved staff account. A private inspection is never deleted by withdrawal.
- Approved staff can hide inappropriate gallery publications. Access is validated
  by the existing staff allowlist; the public gallery does not create new staff.
- Withdrawal/moderation hides the snapshot; retained database rows are private.
  No restore/republication control is provided. Downloaded/cached public copies
  cannot be recalled. Maintainer contact uses the public snapshot ID.
- Guest clearing browser storage loses withdrawal authority. Staff can moderate.
- Atomic SQL locking enforces **100 lifetime publications total, 5 per publisher**,
  including withdrawn records. At most two 120 KB JPEGs each; base64 storage uses
  approximately **32 MB maximum image text** at capacity, plus row overhead.
  Images are stored in gallery database rows, not private staff storage buckets.
- These bounds are for a small demo. There is no CAPTCHA, IP-level rate limiter,
  malware/NSFW scanning or proactive moderation. Attackers can create new browser
  workspaces, so the per-browser limit is not a strong anti-abuse identity check.
  The global bound limits stored data but a distributed attacker can fill it.
  Database/API bandwidth and free-plan availability remain hosting limitations.
- Model outputs are screening measurements, not verified diagnoses. Public samples
  are not an unbiased evaluation dataset. Existing model/RAG behavior is unchanged.

## Local use

The existing local server can optionally enable a local-disk gallery:

```powershell
$env:DEFECTRAG_GALLERY_ENABLED='1'
.\Start-DefectRAG.cmd -Port 8767 -PythonPath '.\.venv\Scripts\python.exe'
```

This creates only `runtime/gallery.sqlite3` and `runtime/gallery.key`. It is shared
only by visitors reaching that local server, and does not synchronize to the
public Space. Do not publish the SQLite file or key to GitHub.

## Verification status

See the latest `DEVELOPMENT_PROGRESS.md` checkpoint for actual test/build/deploy
results. The live Supabase migration and secret configuration are manual steps;
local software checks do not prove the new SQL has executed in the hosted project.
