# Corrective Actions: disabled Edge deployment verified

25 October 2026, Asia/Kuala_Lumpur. Source checkpoint `422ead2` on
`feature/auth-mfa-inactive`. Owner approved ONLY this dedicated disabled deployment
and one refusal test. No activation, SQL, real notification, hosting or HF deploy.

## Actual live results

- Confirmed project `zrzqpbcomlorfzszolrs` initially contained only `hyper-worker`.
  A `DEFECTRAG_CA_` secret-name filter returned no matches; no value was revealed
  or changed. Absent CA enable flag defaults OFF in the reviewed handler.
- Work/Desktop source canonical hashes matched the reviewed manifest in
  `CA_LIVE_BRIDGE_NEXT_GATE.md`. Deployed exactly `index.ts` and `worker.mjs` via
  the native Supabase editor as new function **corrective-actions**.
- Supabase reported successful deployment; native dashboard marker recorded
  **12:36:56 MYT**. Saved the new function's reviewed `verify_jwt=false` setting.
  This is purpose-secret authentication code, not a Supabase user JWT endpoint.
  Custom bearer checks remain present; no existing function setting changed.
- Reopened deployed Code and copied only its public source through native editor
  selection. Entry matches reviewed source exactly after CRLF normalization.
  Dashboard displayed two worker module listings; both match the same reviewed
  worker source. No unreviewed source was deployed or corrective redeploy needed.
- ONE direct anonymous `POST {}` returned **HTTP 503** and exactly
  `{"error":"automation_disabled"}`. No keys supplied. Request ID
  `01a17159-cc09-7532-a1b8-a2c7dbbf7c40`, execution ID
  `3c35fd05-4996-4f33-afe4-892d15090670`.
- Native dashboard independently shows one invocation / one503 and runtime
  `booted (time: 18ms)`. The5xx metric is expected for this intentional guard,
  not evidence of a failed deployment. Do not enable automation or resend tests
  merely to remove its red error metric.
- Final inventory contains corrective-actions and unchanged hyper-worker (last
  updated label3days ago before and after). Developer worker/secrets/Cron/n8n/
  Staff/MFA/synchronization/Gallery/HF were not edited.

The guard returns before any Supabase RPC, n8n call or mail side effect. No SQL
was issued and no database permission/setting or record was changed by this step.
Database contents/settings were not independently re-audited here; retain the
earlier live security results within their recorded scope.

## What remains

This establishes a functioning **disabled** cloud bridge only. It does NOT verify
positive live callback authentication, event leases, delivery or hosting.

The current dispatcher claims events globally and expects an HTTPS n8n endpoint.
It cannot safely select one QA event or reach a Windows localhost webhook. Keep
database automation false, CA enable flag unset/0, CA schedulers inactive and
workflows unpublished. A separately reviewed event-scoped local/manual bridge or
approved hosting design is required before a real sink-first Supabase test.
Never fabricate a live lease, toggle global gates as a shortcut, expose the n8n
editor, provide a service-role key to n8n or consume unrelated queued events.

Evidence: `results/corrective-actions-disabled-deploy-20261025/` contains the safe
HTTP response/IDs, source/config review, native overview and final inventory.
No production secrets or private notification payloads are included.
