# Next production gate: disabled Corrective Action bridge

UPDATE25October: owner approved and this disabled deployment/refusal gate now
PASS. Dedicated corrective-actions deployed, native source copies match reviewed
hashes, verify_jwt=false saved, CA flag absent/OFF, one POST{} returned exact503/
automation_disabled. No SQL/secrets/activation/real delivery. See
CA_DISABLED_DEPLOYMENT_20261025.md. The approval-request wording below is the
completed gate's historical plan; do not deploy/test again automatically. The
positive live single-event/connectivity limitations below remain outstanding.

Prepared 25 October 2026. This is a plan, not a deployment or activation receipt.

## Completed before this gate

- Owner manually installed the revised case migration. Native live Supabase case,
  MFA, assignment and Personal/Team authorization tests passed within their saved
  scope on 24 October. The migration must not be repeated.
- Local native webhook authentication and malformed rejection passed separately.
- Local valid-envelope projection, simulated callback/SMTP success and replay
  passed. In the new failure lesson, real local n8n/SMTP accepted one synthetic
  message; the simulated receipt endpoint returned 503. After endpoint recovery,
  a replay skipped SMTP and stopped for manual reconciliation. Counters stayed
  begin2/finish1/accepted1. No real email or Supabase call occurred.
- The local ledger is a simulation in memory. These results do not establish
  actual cloud callbacks, live delivery, crash durability or always-on hosting.

## Exact next approval scope

Request owner approval for **only** deploying the existing `corrective-actions`
Edge Function to project `zrzqpbcomlorfzszolrs`, initially disabled, followed by
one POST `{}` verifying HTTP 503 with `automation_disabled`.

Deploy source:

- `deployment/supabase/functions/corrective-actions/index.ts`
  - canonical UTF-8/LF SHA256:
    `9d53b4905382588fa27361b4bdbbc52e9c67ce5d621ed3ba515665c1454b8fc1`
- `deployment/supabase/functions/corrective-actions/worker.mjs`
  - canonical UTF-8/LF SHA256:
    `f48ff5635b23cc9f33515c67a66412a543d0f0af4b26126c100bce3669b90bd1`
- `deployment/supabase/config.toml`: the existing corrective-actions entry uses
  `verify_jwt=false` because the handler checks its purpose-specific bearers when
  enabled. Do not remove those handler checks. The disabled gate runs first.

`DEFECTRAG_CA_AUTOMATION_ENABLED` must be unset or `0`; the source fails closed
unless it equals `1`. No new bearer or service key is needed for this disabled
test. Do not read/change production secrets to discover masked values. If a
current function/configuration conflicts with the last verified baseline, stop
and review it before overwriting. Its absence was last observed on 24 October;
no fresh production inventory was obtained during the 25 October local lesson.

The POST check must return before any RPC, claim, email, n8n request or scheduler
work. A 503 alone is insufficient: inspect the response's `automation_disabled`
code. Save only safe status/body, source identity and configuration metadata.

Keep database `corrective_action_settings.automation_enabled=false`, all CA
schedulers inactive, CA UI off and n8n workflows unpublished. Do not alter
`hyper-worker`, Developer notification gates/Cron/Vault/Resend, Staff/Auth/MFA,
Personal synchronization, existing records or schema. No SQL, real notification,
Hugging Face deploy, GitHub push or new hosting is included in this approval.

## Why positive live delivery cannot follow automatically

The current worker does not support a safe one-event local dispatch:

1. The Edge handler gates both worker and callback operations on the same
   `DEFECTRAG_CA_AUTOMATION_ENABLED` flag.
2. SQL claim and effect RPCs also require database automation ON. With it OFF,
   claim returns null and effect rejects. Do not fabricate a lease or temporarily
   turn this global gate on to work around the test boundary.
3. `defectrag_ca_claim()` selects the earliest due eligible event globally; it
   takes no QA event argument. Calling the current scheduler can also generate
   reminder events. A single QA target is not currently guaranteed.
4. The Edge dispatcher accepts a fixed HTTPS webhook and calls it from Supabase.
   `localhost:5678` is local to Windows/Docker and cannot serve as that cloud
   destination. No public tunnel or editor exposure is authorized.

Before a positive live QA test, prepare a separately reviewed event-scoped
claim/dispatch design and an authenticated outbound local/manual bridge (or
approved stable HTTPS hosting). It must name a disposable QA event, leave other
queued events untouched, avoid giving n8n a privileged Supabase key, and route
mail to a test sink first. Any required code/SQL/configuration/permission changes
and real supervisor email need their own approval. Do not use the fixture's
public marker or fake identifiers as actual authorization.

Reliable always-on hosting, persistence/backup/restart tests and laptop-off
Corrective Action delivery remain a separate later gate. Local Docker does not
satisfy that requirement. No paid hosting, Oracle signup or Trello is activated.

## Rollback of the disabled deployment

If the new function fails to start or produces an unexpected result, stop the
test and preserve safe logs. Keep all gates OFF. Restore only a previously
verified version of this dedicated function if one exists; do not touch the
unrelated Developer worker, drop data or revert the installed migration. Removing
a cloud resource or changing gates beyond this plan needs separate authorization.
