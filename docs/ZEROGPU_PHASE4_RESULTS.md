# Phase 4 live integration results — 18 October 2026

Runtime verified on cloud commit ebbcf47cdd1f87dcd7f94219fecaf7d5bac35db4.
User confirmed manually executing the previously reviewed additive SQL. The agent
executed no SQL, changed no schema/policy/account and used no service credential.
The existing approved developer signed in themselves through the unchanged staff
workspace. Existing public configuration, staff JWTs, RLS and private bucket reused.

| Boundary | Actual evidence |
|---|---|
| Anonymous RPC denial | Both reviewed RPCs returned401, PostgreSQL42501; missing function is not a pass |
| Invalid staff credential | Protected history/stats returned403; absent workspace returned401 |
| Real inspection → durable row | PCB1 a6351615259d42868b766a004f5dd303 saved directly to Supabase and appeared in Staff workspace and main history |
| Measured model result | CUDA DINOv2, score0.31300604343414307, threshold0.16181933879852295, Anomalous, inference666.43ms |
| Conversation RPC | Saved-measurement answer and genuine Qwen heatmap answer with screening-4 citations; all four turns returned in shared history |
| Review notes | Exact bounded acceptance-test note inserted through existing staff_notes policies, visible after full reload and recovery |
| Acknowledgement RPC | Alert became Acknowledged/0 pending; report payload confirmed alert_acknowledged=True after reload |
| Private images | Both image and heatmap loaded in browser and returned200 from signed Supabase storage URLs |
| Archive/developer recovery | The single owned public-fixture record archived, disappeared from active history, then restored; measurements, conversations, note and images retained |
| Reports/CSV | Signed report and export200; report storage=supabase, generated answer and retrieved source text present; CSV includes exact test ID/batch |
| Browser reload | Existing sign-in, saved inspection, conversation, note and acknowledgment persisted |

The tests used one clearly labelled public VisA preview fixture, batch
PHASE4-STAFF-ACCEPTANCE. Existing staff history was empty before this test. No
existing production records were archived or modified. The owned fixture was
restored to active history. No accuracy experiment, fitting or model change.

## Acceptance gaps and retained limitations

The user confirms no existing nonstaff account is available. Authenticated
nonstaff RPC denial is therefore **not live-verified**. Invalid JWT and anonymous
denial are different tests. No account was created or allowlist changed. Only the
existing developer account was available; distinct ordinary-staff ownership and
second-user collaboration are software/schema-reviewed, not live role-matrix proof.

Staff-submitted answers lack verified model provenance; acknowledgement stores no
actor/timestamp. Statistics cover latest1000 active records; archive processes up
to500 matches, team table shows latest200, main history latest500, CSV up to10000.
Failed multi-object upload can leave private orphan objects for operator cleanup;
failure is reported rather than a durable-success claim. No destructive cleanup.

Private resumable artifacts stay Git-ignored in development-support/space.
Sanitized evidence and screenshots are under docs/zerogpu_phase4. Never publish
JWTs, workspace secrets, signed capability links, raw HTML reports or full logs.
Final restart preservation and batch/stability acceptance are recorded separately.
