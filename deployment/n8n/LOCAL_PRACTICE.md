# Local callback and SMTP practice

Latest lesson (25 October): two additional deliberate native GUI runs proved
receipt-loss quarantine. SMTP accepted one synthetic message; the receipt endpoint
returned injected503. After that endpoint recovered, replay skipped SMTP and
Require durable completion threw the expected manual-reconciliation error. See
practice-ambiguity-review.json. The last open editor now shows this expected
error rather than the earlier successful duplicate output described below.
Do not rerun SMTP or enable automatic retries to remove it. Simulator is stopped.

This is a **simulation**, separate from the authenticated webhook draft and the
live Supabase implementation. It uses no project key, password, real mailbox,
live lease or real inspection. Keep it unpublished. Developer cloud email delivery
is a different workflow and is unchanged.

## Verified lesson: follow the decision

Open the existing local workflow **DefectRAG CA - SIMULATED CALLBACK + MAIL SINK**:
`http://localhost:5678/workflow/DRCALocalPractice20261025`.

1. Open **Reserve notification effect** and select its OUTPUT **JSON** tab.
2. The last run shows `execute: false` and `done: true`.
3. Close that panel, then open **Effect requires execution**. Its condition is
   `$json.execute` is true. A false value takes the lower branch directly to
   **Require durable completion**, skipping SMTP.

On the first run the callback returned `execute: true`. One message was accepted
by the local SMTP sink; the workflow checked SMTP acceptance and recorded a
receipt. The second run used the same fake event and skipped sending. Recorded
counters: begin calls 2, finish calls 1, sink messages 1, effect done, real emails 0.
The original **DefectRAG CA - LOCAL QA ONLY** workflow retains its native Header
Auth and pinned sample. It was not replaced or reconfigured by this lesson.

## Files and boundaries

- `local-practice-fixture.mjs`: loopback HTTP callback on port 18081 and SMTP sink
  on 12525 **inside the existing n8n container**. No published container ports are
  added. No external HTTP client, DNS lookup, SMTP relay or Supabase SDK exists in
  this helper. Only fixed synthetic envelope addresses and IDs are accepted.
- `fixtures/local-practice-workflow.json`: separate inactive ten-node manual
  workflow derived from the existing template. The first node keeps the template
  name **Authenticated case event**, but is intentionally a manual trigger here;
  it does not test webhook authentication. **SYNTHETIC input only** supplies fake
  data. The final webhook response is replaced with No Operation.
- `fixtures/local-practice-smtp-public-config.json`: loopback host/port, TLS off
  and blank username/password. It contains **no credentials for any real service**.
  This cleartext SMTP setting is for the container-loopback sink only.
- `test-local-practice.mjs`: six focused checks, including HTTP guards/limits,
  duplicate suppression and failure quarantine. These test the simulation, not
  Supabase's production ledger or RLS.

The callback's `X-DefectRAG-Local-QA` marker is public fixture text, **not an
authentication secret**. Never copy this configuration to a real cloud bridge.
The real workflow still requires purpose-specific server authentication.

The sink discards raw mail content. Its status lists fixed synthetic envelope /
template metadata; it does not establish inbox delivery or validate the received
message body. n8n's SMTP acceptance and completion outputs plus the fixture
counters establish the local send/receipt result.

The ledger is in memory, not a durable database. Restarting it resets the practice
state. This test therefore does **not** establish crash/restart deduplication,
live Supabase leases, cloud callbacks, production retries, or laptop-off hosting.
Earlier isolated n8n failure tests remain separate evidence and were not repeated.

## Lifecycle

The helper requires `DEFECTRAG_LOCAL_PRACTICE=1`, stops after 30 minutes, and was
explicitly stopped after this lesson. The n8n service remains running. Saved
node output can still be inspected; executing now will get connection refused
until the fixture is deliberately restarted. No listener or key prompt is needed
for this practice workflow.

For a future approved practice session, copy the helper to the existing container
and start it (its ledger will be empty):

```powershell
cd 'C:\Users\User\Desktop\DefectRAG-v2'
docker cp '.\deployment\n8n\local-practice-fixture.mjs' n8n:/tmp/local-practice-fixture.mjs
docker exec -d -e DEFECTRAG_LOCAL_PRACTICE=1 n8n node /tmp/local-practice-fixture.mjs
```

Do not reimport over edited workflows or change the original authenticated draft.
To read only this synthetic fixture's status:

```powershell
docker exec n8n node --input-type=module -e "console.log(JSON.stringify(await (await fetch('http://127.0.0.1:18081/qa/status')).json()))"
```

Evidence for 25 October 2026 is under `results/n8n-hands-on-20261025/`: native
replay output/screenshot, mailbox counters and practice-review report. Production
Corrective Action automation remains OFF; no production settings were changed.
