# Final verified result - 26 October 2026

**Local n8n / real Supabase integration and disposable-case lifecycle PASS.**
Production unattended Corrective Action automation remains OFF.

Fresh event b857cc19-6e07-4772-8651-b91b52c9bb4b completed all9 nodes. Real ledger
shows sent/attempts1, done effect/receipt, finished grant and cleared lease. The
local no-relay sink accepted1 message, sent0 real emails and stored0 raw bodies.
No duplicate dispatch was made. The consumed grant and one-effect ledger are
verified; live concurrent replay and crash-after-SMTP guarantees are untested.

Same QA case fb462978-af2b-4b4f-a280-2c9803dc4bb1 completed Open3 -> Assigned4 ->
In Progress5 -> Resolved6 -> Closed7, with both timestamps and audited actors.
All8 original-data comparisons match: original case/history/events/effects,
Staff memberships, Personal11, Team10 and Gallery6. QA flag restored0, actual
endpoint503/qa_disabled; temporary sink stopped; n8n execution data cleared and
workflow unpublished. Independent Developer registration emails unchanged.

| Feature | What is verified | Remaining gate |
| --- | --- | --- |
| Supervisor notification | Real cloud event -> authenticated n8n -> one local SMTP acceptance -> durable cloud receipt/finalization | Approved hosted endpoint and actual supervisor mail delivery; queue latency measurement |
| Before-deadline follow-up | Existing SQL queues one reminder within24h per version; isolated real PG17 contracts pass | Hosted scheduler and end-to-end reminder delivery |
| Overdue escalation | Existing SQL queues one overdue supervisor alert per version; offline boundary/dedup contracts pass | Hosted delivery; higher-management ladder and repeated follow-ups are NOT implemented |
| Resolution and closure | Same disposable case completed live with CAS updates, history, actor and timestamps | Production operational rollout only after hosting/testing approval |

## n8n's function in DefectRAG

Human review creates a Corrective Action in Supabase. Its durable event is sent
through a secured bridge to n8n. The workflow validates the event, reserves its
notification effect in Supabase, delivers to the verified supervisor, then saves
the delivery receipt. Supabase owns identity, MFA, case permissions, state and
audit records. n8n coordinates the external notification workflow; it does not
run DINO/RAG, authenticate Staff or approve access. The separate Developer signup
notifications already run through cloud Cron/Edge/Resend and do not need n8n.

## Exact production gates still open

1. Approve an always-on host with TLS, a stable HTTPS webhook, restricted editor,
   persistent encrypted credentials/database, tested backups and restart monitoring.
   Local Windows Docker cannot receive unattended cloud traffic or run laptop-off.
2. Configure separate production worker/inbound/callback/SMTP credentials privately
   on that host; never publish QA credentials or provide a Supabase service key to n8n.
3. Review and quarantine the retained QA queue with a separately approved procedure.
   Closing a case stops deadline reminders but its latest updated notification may
   remain eligible for production dispatch. Do NOT simply enable the global flag.
4. Test actual supervisor delivery, before/after-deadline scheduling, provider failure,
   uncertain receipt handling, revoked supervisor, host restart and laptop-off flow.
   The tested sink is not proof of inbox delivery or hosted operational reliability.
5. Separately approve global automation and scheduler activation only after those
   gates pass. Do not change the working Developer notification schedule.

Evidence is in results/corrective-actions-one-event-20261025/*20261026*.
The dated preparation notes below are historical and superseded by this result.
# Current state - 26 October 2026

The replacement authorization expired without a claim. Live metadata shows
queued0/no effect, not a failed send. It cannot be renewed by the installed RPC.
Owner separately approved ONE fresh versioned event on the SAME disposable case.
New event b857cc19-6e07-4772-8651-b91b52c9bb4b is updated/version3, queued0.
Both previous events and grants remain unchanged. New grant and actual delivery
are still pending. QA flag0/globalOFF/MFA ON; Developer email delivery unchanged.

The exact expired-event recovery helper uses native Developer MFA and existing
version-checked RPC only; no SQL, inspection, permission or production UI change.
14 focused lifecycle/recovery tests pass. Eight baseline preservation comparisons
pass live. Temporary sink PID561 accepted0; n8n draft remains unpublished.

Next: owner performs native timed approval and existing-key sender entry, then
agent checks grant lifetime before enabling ONLY QA and arming the protected
listener. No real mail. Disable QA after the result. If successful, advance SAME
case Open3 -> Assigned4 -> In Progress5 -> Resolved6 -> Closed7 and verify audit
and timestamps. Failed original event must never be retried; the expired event
must never be reset. Do not mistake queueing or SMTP acceptance for completion.

The older dated sections below are historical, superseded by this current state.
# Corrective Actions: completion audit and controlled QA

25 October 2026, Asia/Kuala_Lumpur. Existing permissions and production automation
remain unchanged. This document separates implementation from actual live proof.

CURRENT: one real exact-event attempt was claimed once, but n8n's callback was
rejected401 before an effect or SMTP action. Event is dead/attempts1; grant
finished; lease cleared; sinkaccepted0. QA is OFF. Owner corrected callback
Value; a fixed-wrong-event partial request returned403/wrong_qa_event, proving
authentication before deliberate rejection WITHOUT a database RPC or mail.
Normal workflow expression restored; transient execution data cleared. Original
ledger/membership fingerprints and inspection/gallery counts match baseline.
Successful end-to-end delivery and the new case lifecycle are still pending.

Prepared replacement operator control (inactive): ONE new versioned event on the
SAME synthetic case, using existing native update RPC. Never resets the failed
event/grant or changes permissions. Requires separately approved additional
attempt; zero-effect finished failure; same exact QA case; version/audit-intent
recovery on lost response. Ten relevant guard/recovery tests passed. Owner then
approved one replacement attempt: native version2 on the SAME case now has event
`5f58829c-e8ca-42ba-ad8d-0ec5cc0b09d8`, queued/attempts0. Failed original event is
preserved. Replacement grant/dispatch are not yet performed. QA gate stays0;
only its event pin was replaced. No new keys are required.

| Capability | Implemented behavior | Current verification |
| --- | --- | --- |
| Initial supervisor notification | Creation/update RPCs immediately queue a versioned event. Enabled dispatcher sends one event per invocation; the supplied schedule is every 15 minutes. Delivery is not instant or guaranteed within 15 minutes when a backlog exists. | Native claim/webhook/validation passed; callback401 blocked first attempt before SMTP. Callback subsequently verified corrected using a rejected wrong-event probe. Successful sink delivery still pending. |
| Before-deadline reminder | `defectrag_ca_schedule()` queues one `reminder` per current case version when due within 24 hours. | Focused isolated real PostgreSQL deadline contracts passed; production scheduler remains OFF. |
| Overdue escalation | Same scheduler queues one `overdue` event per version at/after the deadline for Open/Assigned/In Progress cases. Current notification goes to the assigned verified supervisor. | Boundary and duplicate checks passed offline. No higher-management ladder, automatic reassignment, priority change or recurring daily escalation is implemented. |
| Resolution/closure | Version-checked RPC enforces Open → Assigned → In Progress → Resolved → Closed, audited notes/timestamps. Resolved can reopen to In Progress; Closed/Cancelled are terminal. | Earlier native role/lifecycle tests passed on the original closed fixture. New sink-case lifecycle remains pending. |

Sources: `deployment/supabase_corrective_actions.sql` functions
`defectrag_create_corrective_action`, `defectrag_update_corrective_action`,
`defectrag_ca_schedule`, `defectrag_ca_claim`, `defectrag_ca_effect`,
`defectrag_ca_finish`; `deployment/supabase/functions/corrective-actions/worker.mjs`;
`deployment/n8n/corrective-actions-scheduler.json`.

## What the deadline audit established

New focused tests exercise the existing scheduler, not a replacement:
`deployment/tests/corrective_actions_deadlines_local.sql` and
`run_corrective_deadlines_sql.py`. Cached PostgreSQL17, network NONE, no published
ports/host mounts, fake Auth identities/factors only, exact container removed.
No completed old suite/model experiment was repeated. The fixture initially
omitted a required display name; after correcting that fixture, all assertions
passed. No deployed SQL, RLS, RPC or application feature was changed.

Verified: outside/at 24-hour boundary; at/past deadline; same-version dedup;
new-version eligibility; resolved/closed/cancelled/archived exclusion; disabled
and paused scheduler gates. Test-local clock positioning affects synthetic rows
only. These are NOT real hosted scheduler/SMTP/hosting tests.

Existing semantics are one reminder and one overdue alert PER VERSION, not a
configurable repeated follow-up sequence. An already queued reminder is not
automatically withdrawn just because its deadline later passes within the same
version. At one event per 15-minute call, sustained capacity is 96 events/day;
backlog/latency must be measured before claiming immediate delivery. Treat these
as explicit limits before activation, not secretly changed production policy.

## Controlled native QA state

- QA migration owner-applied; nine SELECT-only postflight checks passed.
- Separate `corrective-actions-qa` deployed disabled; exact sources verified.
- Owner saved two distinct QA keys; only native names/digest inequality checked.
- n8n draft `yx3NG0Ac1kIv8L37` remains unpublished; execution payload/progress
  retention disabled. Native import did not preserve those settings and selected
  local credentials automatically: actual assignments must be checked, not trusted.
- Both callback nodes now select `DefectRAG CA QA callback - Supabase only`;
  inbound keeps `X-DefectRAG-CA-Key`; SMTP uses separate container-loopback12526
  no-login/no-relay sink. Owner entered callback value privately.
- Native Developer AAL2 readiness passed. New synthetic case
  `fb462978-af2b-4b4f-a280-2c9803dc4bb1`, created event
  `8360adfa-a5c0-4af3-8525-08265380fc0e`, queued/attempts0. No original case reopened.
- Endpoint pin set to ONLY this event; QA enable explicitly0. Actual one-event
  grant/dispatch/receipt/finalization still pending. Do not reset or claim another.

Temporary loopback operator page now includes status and one-step lifecycle
controls for ONLY that plan's Developer-confirmed synthetic case. It requires
the exact created event sent and notification effect done before changing state;
uses existing native MFA and version-checked RPC; no direct writes, permission
parameters, real mail or automatic retry. Five focused JS guard tests passed.
This is operator tooling, not a React redesign or a new authorization boundary.

## Hands-on n8n lesson

1. Inbound Header Auth authenticates the LOCAL sender, not a Supabase user.
2. Validate strips input down to exact event/short-lived lease identifiers.
3. Reserve calls the separate HTTPS QA endpoint with the CALLBACK credential.
   Supabase independently checks the event grant, lease and durable effect ledger.
4. IF sends only when `execute=true`; a completed replay skips SMTP.
5. Mail goes only to fixed `supervisor@example.invalid` at the local sink.
6. Acceptance check validates recipient acceptance and message ID, then receipt
   callback records durable completion. Unknown effects stop for reconciliation.
7. Windows sender finalizes once; SQL verifies the actual effect ledger. Webhook
   HTTP success alone is insufficient. Disable ONLY QA afterward and compare
   baseline fingerprints of unrelated rows.

Do not pin real webhook headers/leases, publish the QA workflow, reuse the
Developer-email worker key, or provide a service-role key to n8n. The 15-minute
QA grant has one claim and cannot be reset. SMTP acceptance does not guarantee
inbox delivery; this sink never contacts an inbox. Lost receipts cannot guarantee
exactly-once external effects, so uncertain effects are quarantined.

## Still required before production-ready

Finish and reconcile the one-event native cloud→local→cloud sink test, then the
new case lifecycle and original-ledger comparison. Hosted reminder/overdue
delivery, real supervisor SMTP acceptance/inbox, real endpoint failure/recovery,
revocation during delivery, restart persistence and laptop-off execution remain
separate live gates. The QA endpoint handles created/updated events only: do not
toggle global production DB automation to test deadlines on unrelated cases.

Secure always-on n8n hosting is not provisioned. It needs persistent encrypted
credentials/database/backup, TLS, restricted editor/admin access, fixed HTTPS
webhook, restart monitoring and separately approved production secrets/scheduler.
Local Windows Docker stops with the laptop. No tunnel, hosting purchase or
Trello activation is included. Review all QA queues before eventual production
activation; retain audit records and prevent QA events being mailed later.

Existing Developer registration emails use independent cloud Cron/Edge/Resend
and remain unchanged. Multimodal RAG has not been started.
