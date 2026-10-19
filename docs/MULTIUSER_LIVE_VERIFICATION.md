# Live multi-user verification — 19 October 2026

Deployment: `49463314b49e9a7407b80e4a18cbe3b5a85062d1`, source checkpoint
`7d636ac`, Hugging Face `Wizzas/DefectRAG`, free `zero-a10g`.
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

The gallery personal-source publication/withdrawal check and final deployment
regression are still being completed. Existing rows were not altered during
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
Their markup and behavior are preserved. Final build/deployment verification is
pending; these fixes do not change any backend model or database policy.

## Coverage limits

No second actual approved staff account or authenticated non-staff account has
been supplied. Anonymous and invalid-token denials are verified; they do not
prove authenticated cross-owner RLS. No project administrator impersonation,
staff membership changes or direct database-policy tests were performed.
Free ZeroGPU quotas and cold-start capacity remain platform constraints.

Signed preview/report URLs are bearer capabilities until their bounded expiry;
already downloaded copies cannot be recalled. Model provenance remains
unattested, and this is benchmark screening rather than factory acceptance.
