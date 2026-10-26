# Inspection storage, gallery and batch workflow

## Guest and Personal storage

| Use | Where the result is kept | Durability and access |
| --- | --- | --- |
| Unsigned local app | Default `runtime/inspection.sqlite3` and `runtime/artifacts/` on this device | Survives normal restarts; not automatically cloud-saved. A local single-user device history is not a multi-user private cloud account. |
| Unsigned Hugging Face app | Server-side guest workspace selected by this browser's random namespace | Isolated from other guest namespaces; temporary and may be lost after restart. Images are not stored solely inside browser localStorage. |
| Approved account with MFA, local app | Owner-specific mirror under `runtime/local-sync/accounts/<account-id>/` | Queued changes become durable cloud data only after successful synchronization. |
| Approved account with MFA, cloud app | Supabase Personal tables and private image storage | Owner-only access across authenticated clients. Team sharing is a separate explicit action. |
| Community Gallery publication | Separate gallery store for the running backend | Public, sanitized snapshot only after consent. Does not move the private original or share its conversation/notes. |

Runtime paths above assume the default data directory. Existing local guest history
requires an explicit import after account approval/MFA; signing in does not
silently assign that history to an account. The cloud guest Save to Personal action
requires approved authenticated access; signup alone grants no staff rights.
Guests can print/save a report locally without signing in.

## Why publishing was unavailable locally

The screenshot's disabled publication panel corresponds to a backend with no
gallery adapter configured. It is not a ban on guest publishing. The hosted
Space and local backend have separate configuration and stores. Enabling a local
`DEFECTRAG_GALLERY_ENABLED=1` alone creates a local SQLite gallery; it does not
connect to the hosted Community Gallery. No gallery secrets or activation settings
were copied or changed during this improvement. Shared public gallery publishing
from the local app needs a separately reviewed server-side integration; do not put
the gallery key into React/public config.

The updated panel explains which server is unavailable instead of implying that
guest identity or all application storage is broken.

## Single inspection versus batch monitoring

- Image inspection processes one selected image and opens its detailed report,
  heatmap and Evidence Assistant.
- Batch inspection processes up to 20 selected images sequentially and saves
  each result under the same batch name. It does not require prior single-image
  inspection. Completed items are kept and not resubmitted during batch retry.
- Batch history monitors saved batch results. This is not continuous camera or
  production-line monitoring.

Fresh uploads display **awaiting this inspection run**, and selecting new files
clears the previous batch result displayed beside the upload form. The app cannot
truthfully say an image has never been inspected by looking at its filename. No
cross-history visual/content-hash duplicate search was added.

New batch names are checked case-insensitively with normalized whitespace and
Unicode. Cached active/archive names provide immediate feedback; before creating
a batch the UI performs a fresh read-only `/api/batch-name` check across paginated
active and archived records in the current account/workspace. Other accounts'
names are not disclosed or reserved. Retrying the same unfinished job is allowed.
Existing records and optional single-image grouping labels remain unchanged.

**Concurrency limit:** this is a submission preflight, not an atomic distributed
name reservation. Two simultaneous new clients, or direct API clients bypassing
the form, can still reuse a label. A strict cross-client guarantee would need a
reviewed owner-scoped database batch entity/unique constraint and transactional
reservation. No Supabase migration or production permission change was performed.

## Report and verification

The report uses the existing navy/purple visual identity with summary cards,
original/heatmap figures, measurements, human reviews, saved conversation and
retrieved passages. It has responsive CSS, print rules, escaped untrusted text,
safe image URL schemes, no-referrer and private/no-store headers. It does not
generate another prediction or turn a score into confidence/accuracy.

The browser layout preview is an explicitly labelled software UI fixture, not
new model-performance evidence; both preview images are the same sample original.
Desktop layout was visually reviewed. Actual print-to-PDF and mobile viewport
rendering were not manually exercised. Relevant API/privacy/software regression
tests and production frontend build are recorded in DEVELOPMENT_PROGRESS.md.

These changes require a backend restart and a new local frontend build. Hugging
Face still requires a separately approved compatible backend/frontend release;
the current live Space has not been changed by this work.
