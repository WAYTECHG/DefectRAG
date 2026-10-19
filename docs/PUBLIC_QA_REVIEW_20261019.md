# Public DefectRAG exploratory QA — 19 October 2026

## Assessment

The application performs genuine visual inspection, source-grounded generation and
durable staff storage. It is usable for supervised demonstration and benchmark
screening. This review found workflow correctness issues and a real availability
limit that should be addressed before relying on it for continuous staff operation.
This is bounded exploratory testing, not exhaustive certification or a penetration
test. No application fixes or deployment were performed during this review.

Target: https://huggingface.co/spaces/Wizzas/DefectRAG and its direct application.
Hosted commit: `3b68268a582dce6ad731e5a362988eb6d1d9b99e` (RUNNING).
Source baseline: `0554152`. Selected hardware reports `zero-a10g`; the genuine
inspection report identifies an NVIDIA RTX PRO 6000 Blackwell MIG 2g.48gb allocation.
These describe different platform/runtime layers, not two model experiments.

## Coverage and results

| Area | Fresh result | Evidence / limits |
|---|---|---|
| Public page, assets, APIs, validation and access boundaries | 30/31 expected responses | Only unknown API path differed: 405 rather than expected 404. All tested auth boundaries passed. |
| Supported models and samples | 12 categories, 24 samples available | CPU metadata, not 24 new inference runs. |
| Single real image inspection | PCB1 anomalous sample produced Anomalous | Score 0.313006; threshold 0.141435; model inference 1125.84 ms. Genuine CUDA inference and heatmap. |
| Image viewer | Passed | Original/overlay, comparison divider at 75%, zoom 125%, expansion and Escape dismissal. |
| Assistant — score explanation | Passed | Directly explained distance versus accuracy, without an unrelated verdict preamble. Saved-measurement answer, no LLM required. |
| Assistant — heatmap question | Passed | LIVE LLM cited answer explains nearest-normal patch distance; two retrieved passages. No repetitive anomalous-verdict preamble. |
| Assistant — unsupported defect / repair request | Passed | Abstained; did not invent a named defect or repair temperature. |
| Assistant — staff conversation append | Passed | A fourth measurement question survived in the generated report after reopening. |
| Two-image real batch | Partial success; quota blocked second file | Capsules normal sample: Good, approximately 0.132 vs 0.144, 787 ms. Anomalous sample received quota rejection; no result invented. Completed record survived. |
| Malformed image and missing batch label | Correctly rejected | Malformed JPEG reaches server validation before GPU; missing label rejected in dashboard. Error wording needs improvement. |
| Staff authentication | Approved developer account worked | User entered credentials. No password or JWT exported. |
| Guest-to-staff sharing | Passed | Original image, heatmap and three existing conversation turns appeared in Staff workspace. |
| Staff review note | Passed | Clearly labeled QA note saved with author and date; reopened for persistence verification. |
| Alert acknowledgement | Passed | New QA alert acknowledged; acknowledgement true in report; alert count cleared. Does not establish a human acceptance decision. |
| Report | Passed with presentation issues | Original and heatmap both loaded at 640×488; measurements, four conversation turns and source passages present. Print dialog/PDF output not exercised. |
| CSV | Downloaded successfully; filter mismatch | Candle filter showed zero rows while exported CSV contained the PCB1 QA record. |
| Navigation | All ten sidebar pages opened | Overview, inspection, batch, history, alerts, performance, official benchmark, staff, recovery, about. Browser back/forward routing worked. |
| Evaluation | Consistent with active policy | All 12 rows present; Macaroni1 recall .850 / precision .780, Macaroni2 .800 / .741. False-alarm cost and retrospective nature disclosed. DINOv2/DINOv3 benchmark switch works. |
| Recovery | Read-only page and cancel path passed | Existing three archived records were visible and left unchanged. No new live archive/restore round trip. |
| Anonymous RPC authorization | 2/2 denials passed | Both functions returned HTTP401, SQLSTATE42501, using random nonexistent ID and public key without user JWT. |
| Browser console | No captured errors/warnings at final check | Bounded browser log sample, not proof that no error can ever occur. |
| Existing Python regression suite | 78/79 initially; remaining case passed with shorter temp path | Long Windows workspace path prevented one SQLite file opening. Targeted security rerun: 9/9 passed. All 79 distinct suite cases were covered successfully across these runs; this was not a single clean full-suite run. |
| Existing frontend / batch software checks | 6 frontend tests and batch harness passed | Batch quota stopping, retained successes and independent invalid inputs covered without model simulation being represented as live inference. |

Only two new images produced actual model predictions. One additional image was
blocked by quota. One fresh cited answer used live Qwen; direct measurement and
scope-gated answers did not require generation. No models were trained or downloaded.

## Ranked findings

### QA-01 — High: free GPU availability interrupts normal batch use (live)

Reproduction: submit `capsules_good.jpg` and `capsules_anomalous.jpg` together as
`QA-20261019-BATCH`, signed in to Supabase, using the direct Space application.
The first image completed; the second returned “exceeded your ZeroGPU runs limit.”
Supabase sign-in does not provide Hugging Face GPU quota. This is a real platform
availability limit, not an anomaly-model failure. Completed data was preserved.

The UI has no failed-only retry control or durable job resume. The error correctly
advises retrying unfinished images, but pressing Inspect batch again with the same
selection resubmits both files. Failed/pending filenames live in client batch state;
the staff repository records successes, while failures are server logs, not durable
batch items. A browser reload can therefore lose the retry list.

Recommended: persist job/item states and identifiers, expose “Retry failed/pending
only,” retain completed results, and explain the separate HF/staff sessions before
submission. Show a service/quota-blocked state without inventing an exact remaining
quota if the platform does not expose it. Avoid automatic repeated GPU retries.

### QA-02 — High: late assistant answers can attach to the wrong visible inspection (software reproduction)

The actual `ask()` handler in `frontend/src/main.jsx` appends an awaited answer to
whatever message list exists when it finishes. There is no active inspection/request
identity check. Navigation and opening another record can occur while a request is
pending. The `openRecord()` messages fetch has a similar stale-response exposure.

A deferred-response harness executing the actual source `ask()` handler reproduced:
start question for inspection A → switch visible state to B and clear messages →
resolve A → A's answer is appended under B. No network or GPU was used in this
reproduction. It was not forced in the hosted browser. The backend request still
targets A; incorrect server-side attribution was not demonstrated.

Recommended: key conversations by inspection ID; use an active request/identity
generation guard for inspection, message loading and chat; invalidate it on result,
auth or workspace change. Preserve completed server results under their original
record rather than displaying them in a different context.

### QA-03 — Medium: sharing does not refresh the main workspace views (live)

After sharing the new anomalous inspection, Staff workspace showed one shared
record, while the main Review alerts page still showed zero awaiting acknowledgement.
Reloading showed the expected alert. The share-success path sets a notice without
calling the main `refresh()`; normal sidebar navigation does not refresh it either.
Other staff changes can also leave the main views stale while the separate staff
table refreshes every 15 seconds.

Recommended: invalidate/refetch workspace queries after sharing and on relevant
page entry or shared changes; distinguish stale, loading, error and genuinely empty
states. Use one consistent refresh policy across overview, history, alerts and staff.

### QA-04 — Medium: saved record and input form disagree (live)

Select Candle in the inspection form → open history → open the saved PCB1 record.
The result and assistant correctly show PCB1, but the product dropdown remains Candle;
the saved QA batch is also not restored in the input form. A subsequent upload may
therefore inherit an unintended product. The existing model does not verify category.

Recommended: synchronize category/batch to the opened record, or explicitly separate
read-only saved evidence from a clearly labeled new-inspection form. Keep user
selection explicit; do not claim automatic product identification.

### QA-05 — Medium: export scope differs from active filters (live)

With Candle selected, zero history rows were visible; Export CSV contained the PCB1
QA record. The link is always `/api/export.csv`; current filters are not included.
The caption explains an export limit, but does not label the action “Export all.”

Recommended: offer “Export filtered” and “Export all,” applying the same server-side
filters and making row count/scope explicit. Keep spreadsheet formula escaping.

### QA-06 — Medium: reports expose implementation fields (live + source)

The report renders every scalar record field, including owner UUID, raw signed
image/heatmap URLs and the report capability URL. Long tokens dominate the report and
are copied into saved/printed text. No unauthorized disclosure was demonstrated;
these are already authorized report contents, but temporary bearer URLs are
unnecessary report metadata. The actual report images loaded successfully.

Recommended: allowlist useful human-readable measurements and audit metadata;
omit signed URLs and internal owner IDs from the measurement table. Include staff
review notes and a clear review disposition section when implemented. Keep a
separate optional technical export for development. Do not publish private reports.

### QA-07 — Low: filtered empty state says no inspections exist (live)

Filtering the existing history to Candle displays “No inspections yet. Add an image
to start your inspection log.” This falsely describes a filter miss as an empty
workspace. Use “No inspections match these filters” plus a clear-filters action.

### QA-08 — Low: invalid image message exposes Python internals (live)

A non-image file named invalid.jpg is safely rejected, but the displayed error
contains `cannot identify image file <_io.BytesIO object at ...>`.
Use a stable user-facing explanation and keep internal diagnostics in server logs.
The cloud transport also maps caught validation errors to HTTP503, obscuring the
difference between a bad upload and a service outage for API clients.

### QA-09 — Low: cloud and local terminology is inconsistent (live)

The cloud footer says “Local AI inspection & evidence workspace”; alerts still
describe a “local review alert.” The sidebar says “Private browser session” even
when the approved staff identity is active. About identifies DINOv2 as an optional
profile although it is the cloud's active model, and its source library lacks the
primary DINOv2/Qwen references despite listing related Dinomaly documentation.

Recommended: render environment/identity/storage status from one shared source and
add the active model's primary sources. Preserve layout, colors and existing UI.

### QA-10 — Low: unknown API path returns 405 (live)

Authenticated workspace GET `/api/definitely-not-a-route` returned405 rather than404.
This is an API consistency issue; no route exposure or access bypass was observed.

## Additional source-confirmed gaps / logical enhancements

- **Independent error states:** `refresh()` uses eight settled requests but only
  surfaces a health failure. History, metrics or alerts can fail while defaults or
  stale data look valid. Show section-specific errors and targeted retry actions.
- **Staff review lifecycle:** acknowledgement means “seen,” not “reviewed/accepted.”
  Add an explicit human review status, disposition, reviewer and timestamp, separate
  from immutable model verdict. Assignment and optional follow-up notes would connect
  the review queue to useful operational work. Any schema change needs separate review.
- **Existing hardening limits remain:** conversation RPC accepts approved staff
  answers without verifying model provenance; acknowledgement stores no actor/time.
  Existing successful authorization checks do not remove these limitations.
- **Capacity and search:** history displays at most500, staff table200, and staff
  overview/alerts aggregate the latest1000. CSV is capped at10000. Add pagination,
  date/batch/ID search, explicit scope labels and database aggregates before calling
  these totals complete at larger scale. Thousands of synthetic staff records were
  not inserted to test scale.
- **Connect shared review to action:** Staff Review shows a snapshot and notes but
  lacks a direct “Open inspection / continue evidence conversation / report” action.
  Link to the existing inspection view rather than creating a second assistant.
- **Model operating costs:** current retrospective Macaroni1/2 recall85%/80% comes
  with normal false alarms24%/28%. Pixel AP is approximately .221/.158 in the deployed
  report. These are model/threshold limitations, not repaired by UI changes. Preserve
  disclosures and record human review outcomes before any separately approved model work.

## Unverified boundaries

- The requested390×844 viewport override was ignored: measured innerWidth stayed1280.
  Override was reset. Mobile/touch and cross-browser visual QA remain unverified.
  The file named `mobile-batch.png` is evidence of this failed emulation, not mobile proof.
- No existing non-staff account or second staff account was available. Live non-staff
  JWT denial, staff-vs-developer permissions and two-person concurrency remain open.
  Anonymous/invalid-JWT denials and isolated software permission tests passed.
- Existing archived records were read only. Archive dialog cancel and software
  archive/recovery checks passed; no live archive/restore mutation was performed.
- No sustained load, cold-start/restart, long-expired-session, email reset,
  token-refresh, full offline recovery or actual print-to-PDF test in this review.
- Quota stopped further GPU testing. No repeated retries, paid upgrades or model
  experiments were initiated. Earlier all-category verification is historical evidence,
  not a fresh claim from this test session.

## Preservation and next work

Two new clearly labeled QA records remain in Supabase; the PCB1 record has one QA
note, four conversation pairs and an acknowledged alert. The normal capsule record
is saved. The quota-rejected image has no successful inspection record. Existing
active/archived records, policies, models, datasets and evaluation artifacts were
not deleted, changed or retrained. No SQL migration or deployment was executed.

Private receipts/screenshots live in ignored `development-support/public-qa-20261019/`:
`public-boundaries.json`, `anonymous-rpc.json`, `tests.xml`,
`security-short-path.xml`, `context-race.json`, `filtered-empty.png`,
`history-category-mismatch.png`, `batch-quota.png`. No authentication tokens are
saved in those receipts. Downloaded CSVs contain only this session's QA records.

Recommended implementation order, in a separate incremental change:

1. Guard asynchronous request context; regression-test delayed answers and record opens.
2. Refresh shared data consistently; fix saved-record form synchronization.
3. Make export scope explicit; improve empty and validation states; clean report fields.
4. Add failed-only retry and a durable batch job ledger after schema review.
5. Add auditable human review disposition and direct links between staff/assistant/report.
6. Close mobile, non-staff/second-user and sustained availability verification gaps.

No application changes are active from this QA review. All findings remain open.
