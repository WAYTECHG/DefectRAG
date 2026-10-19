# Live multi-user verification — 19 October 2026

Final running deployment: `13af0e1cb002386ade5849739f4bd28c5736f341`, source
checkpoint `e28f8c6`, Hugging Face `Wizzas/DefectRAG`, free `zero-a10g`.
Initial compatible deployment was `49463314b49e9a7407b80e4a18cbe3b5a85062d1`.
The owner manually executed the reviewed personal migration. No SQL was executed
by the agent. No retraining, new model assets, UI redesign or dependency changes.

## Compatibility before activation

- Live health confirmed all 12 model profiles, ZeroGPU and staff persistence.
- The approved staff browser loaded all three pre-existing team inspections.
  An existing record's images, saved evidence and human review still loaded.
- Both existing community snapshots remained available with redacted measurements,
  valid JPEG previews of at most 512 pixels and no EXIF metadata.
- The served stylesheet matched the existing build byte-for-byte.
- All 18 public/anonymous compatibility checks passed. The three new personal
  tables and five tested RPCs denied anonymous requests with permission error
  `42501`. Missing functions/tables were not counted as a passing denial.

## Activation

After the user reported adding the variable, the live process still reported
personal mode disabled and the exact public variable was absent. The agent set
the requested public variable `DEFECTRAG_PERSONAL_WORKSPACE=1` using the existing
deployment connection, verified the value and requested one restart. Health then
confirmed personal mode enabled. No secret or policy was changed.

All 19 activated public/anonymous checks passed, including guest Team denial,
empty guest private history/alerts/recovery, invalid-token denial and preservation
of both gallery entries. Raw receipts are private under `development-support/space`.

## Owner workflow

The approved owner started with empty Personal history. One new, genuine PCB1
sample inspection with batch label `QA-PERSONAL-20261019` completed on DINOv2:
anomaly score 0.3130, threshold 0.1414, approximately 747 ms model inference.
The UI showed private Supabase storage and both original and heatmap. A second
tab automatically displayed the new personal record and review alert. This is
same-account cross-tab synchronization, not a second-user authorization test.

Verified live on the new QA record:

| Check | Observed result |
| --- | --- |
| Personal versus existing Team history | Personal started empty; Team retained the original three rows. The new record appeared only in Personal until explicitly shared. |
| Real DINOv2 + heatmap | Private save, original and heatmap loaded; no model retraining or benchmark rerun. |
| Qwen evidence conversation | A live cited heatmap answer was relevant to the question and saved privately. It reloaded in the second owner tab. |
| Personal review | An In review / Pending event with a QA note persisted, separately from the measured verdict. |
| Personal alert | Acknowledge reduced the pending count from one to zero. The authorized report showed the acknowledgement persisted. |
| Owner report and images | Report retained conversation, source citation, review and measurements. Both signed private images loaded as valid JPEGs. |
| Known-record guest denial | A fresh guest could not read the known record, messages, reviews, image, heatmap or report. Guest saving/sharing was denied; its CSV excluded the private record. All 16 artifact/denial checks passed. |
| Explicit team share | Team count increased 3 → 4 only after sharing. With conversation opt-in off, private conversation and review were absent from the copy. |
| Duplicate share | Repeating Share returned Already shared; Team remained four records. |
| Shared collaboration | A separate QA staff note and team review loaded in a second tab. The owner-only review remained separate. |
| Personal archive/restore | A filter selecting only the QA batch archived one private record. Recovery showed one archived record; restore returned it with conversation/review intact. The team copy stayed active. |
| Team alert | The QA team alert was independent of the already acknowledged personal alert. The migrated staff acknowledgement RPC changed only that QA team alert from pending to acknowledged. |
| Separate totals | Personal overview showed one anomalous inspection. Team showed four inspections: one Good and three Anomalous. Neither included public-gallery counts. |
| Personal-source gallery lifecycle | Publish required an unchecked consent control to be enabled. An independent guest read the new snapshot with matching real measurements and redacted JPEG previews. UI withdrawal hid only that QA publication; its public detail returned 404 and the original two gallery entries remained visible. |
| Team archive/restore | The QA batch filter selected one team copy. Archive removed only that copy; developer recovery restored it. The personal original remained active, and the three older archived records were left archived and untouched. |
| Final deployment restart | Both owner tabs reloaded the final frontend. Private measurements, conversation, review, acknowledgement and images survived. The final report/known-guest checks passed 16/16 again, and activated public checks passed 19/19. |
| UI corrections | The final served entry was `index-DCyhJBD5.js`; the stylesheet remained `index-Bn4HF2vD.css`. Ordinary history clicks worked after reload. Staff context correctly identified Team, hid the unrelated selector, and the Team archive modal named the correct scope and recovery permissions. |
| Final UI receipt | Eight final UI checks passed: personal archive/recovery wording, correct Staff scope, restored team count, retained team note/review, excluded private review and excluded default conversation. The personal dialog was cancelled without another archive. |

Final deployment regression passed for these recorded flows. Existing rows were not altered during
these tests. Only the newly labelled QA record and its explicit team copy were
used for mutation checks.

## UI issues found during live testing

The archive dialog used generic shared-storage wording while operating on a
personal record. The Staff page also displayed the global Personal selector
above a team-only table. Context labels and archive copy now distinguish Personal,
Team and temporary Guest scope, with the irrelevant selector hidden on the Staff
page. Layout, styling, colors and navigation remain unchanged.

Background polling also remounted Gallery, Filters and Table because they were
declared as component functions inside App. This can discard a click/focus during
refresh; the history row needed a keyboard action during testing. These three
small components now have stable module-level identities with explicit props.
Their markup and behavior are preserved. All 20 frontend tests and all three
builds passed with unchanged CSS. The UI follow-up was published as Space commit
`13af0e1cb002386ade5849739f4bd28c5736f341` from source checkpoint `e28f8c6`.
It changed only three frontend files (346,848 bytes), retained the enabled flag
and did not upload models or delete files. The final Space is RUNNING on the
recorded revision, and live health confirms personal mode enabled.

## Coverage limits

Only the existing approved developer-role account was available. No second actual
approved staff account or authenticated non-staff account has been supplied.
Anonymous and invalid-token denials are verified; they do not
prove authenticated cross-owner RLS. No project administrator impersonation,
staff membership changes or direct database-policy tests were performed.
Free ZeroGPU quotas and cold-start capacity remain platform constraints.
Direct inspection of audit-table actor/time values, authenticated cross-owner
storage reads, the conversation-inclusion opt-in branch and a fresh guest-to-personal
import were not performed live in this run. They have source/software coverage
where documented; no live pass is claimed. Owner CSV download was not exercised
through the browser; the fresh guest CSV exclusion check passed.
One vision job and one live Qwen answer succeeded in this run; quota exhaustion
and peak concurrency were not deliberately provoked. Browser offline transitions
and interrupted transfers have local software coverage, not a newly induced live
network failure. Pending batch-file recovery remains browser/device-local.
Some automated pointer actions in the narrow browser viewport did not dispatch
and required keyboard fallback. Stable component identities address unnecessary
polling remounts, but these observations do not prove every pointer issue was
caused by remounting or fully resolved. Keyboard actions worked; an additional
manual touch/pointer regression pass across viewports remains useful.

The new QA inspection and its team copy are retained for traceability. The QA
gallery snapshot is withdrawn rather than deleted; it still counts toward the
configured lifetime gallery/publisher caps. Existing published entries were not
withdrawn or moderated. No hard-delete or database-policy change was performed.

Signed preview/report URLs are bearer capabilities until their bounded expiry;
already downloaded copies cannot be recalled. Model provenance remains
unattested, and this is benchmark screening rather than factory acceptance.

## Operational result and resuming

The application is deployed and active for the verified owner/guest demo flows.
Remaining multi-account and failure-mode checks prevent claiming a complete
production security certification. Keep the current SQL and setting; do not run
the versioned migration again. No pending inference/training job remains.

Resume optional acceptance work with a separately authorized regular staff and
authenticated non-staff test account when available. Do not create memberships,
weaken RLS or obtain credentials from browser storage to fill that coverage gap.
Use only new labelled QA fixtures. No completed benchmark needs repeating.

Private receipts: `personal-compatibility-published.json`,
`personal-compatibility-public.json`, `personal-enabled-public.json`,
`personal-owner-artifacts.json`, `personal-gallery-lifecycle.json`,
`personal-ui-followup-published.json`, `personal-final-ui.json`, `personal-live-inspection.png` under
`development-support/space`. Authorized report links remain in ignored private
files and must never be committed or published.
