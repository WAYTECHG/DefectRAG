# Staff registration interface activation — 20 October 2026

Live app: https://wizzas-defectrag.hf.space/#team

This is the smallest configuration-only rollout. No application source, models,
stylesheets, SQL, staff permissions, SMTP secrets or n8n configuration changed.

| Item | Verified state |
| --- | --- |
| HF release | `8df12b1010e8b3184544628bd0b64988910c7e39`, RUNNING |
| Parent / compatible application rollback | `b9b5fd90e38f421007912f56663db26e9208bd6d` |
| Source branch / checkpoint | `feature/auth-mfa-inactive` / `689554cc32880be925d14cda15e4d4972ffdaff9` |
| Only changed remote file | `frontend/dist/config.js` |
| Public flags | `authWorkflowEnabled=true`, `registrationEnabled=true` |
| HF backend | `DEFECTRAG_AUTH_WORKFLOW=1`, unchanged |
| HF notifications | `DEFECTRAG_NOTIFICATIONS_ENABLED=0`, unchanged |
| Database flags | `registration_enabled=true`, `mfa_required=true` |

## Database gate and authority

Before changing the frontend flag, the user ran the requested **read-only** query:

```sql
SELECT registration_enabled, mfa_required
FROM public.defectrag_auth_settings
WHERE singleton;
```

The user returned `true / true`. This user-provided live query output is the gate
evidence; it is not represented as an independently authenticated SQL query by the
agent. The user also reported successful Developer MFA verification, mandatory
MFA activation, working Gmail SMTP/reset mail and a corrected production recovery
redirect. No database setting, SQL migration or production secret was changed by
the agent. Do not rerun migrations to activate registration.

## Fresh deployment verification

- The build and release guard passed62 tests and verified87 frontend files. The
  publisher committed exactly one changed file. Comparing all149 allowlisted HF
  paths before/after confirms every other application/model/public file unchanged.
- Main bundle remains `assets/index-C51GOc1V.js`; workspace chunk remains
  `assets/TeamWorkspace-DVtFB4ub.js`; stylesheet remains
  `assets/index-Bn4HF2vD.css`, with identical bytes to the working release.
- Served HTML/config/main JS/CSS matched the verified manifest. Config SHA256:
  `dc3301072b627ccf2d1175de3622e0671f635a4e5a84805504a813a1216e80c4`.
- Public health/models/evaluation/samples/Gallery: HTTP200,12 categories and3
  pre-existing public Gallery IDs preserved. Unsigned private history: HTTP401.
- Supabase public Auth settings confirm `disable_signup=false` and
  `mailer_autoconfirm=false`: signup is permitted and email confirmation required.
- The browser displays the registration form and existing password sign-in
  together. Demo access is still anonymous. Existing password-reset code was not
  altered. Both signup and reset use the live page's `location.origin +
  location.pathname`; the actual email landing URL still needs the manual test.
- A runtime log contained `sqlite3.OperationalError: database is locked` during
  guest-history startup. Subsequent fresh-session history/stats/alerts returned200.
  This is an observed intermittent temporary guest-initialization risk in unchanged
  code, not claimed fixed or exhaustively load-tested. No persistent startup failure
  was observed. It does not grant staff access or modify Supabase permissions.
- Desktop's isolated cloud release and receipts passed the local manifest check.
  Its original local public config, run guide, working local/static index files,
  datasets/models/records/secrets were preserved. No benchmark or GPU experiment
  was repeated for this one-flag rollout.

## Authorization boundaries retained

`frontend/src/authSecurity.mjs::registerAccount` calls native Supabase signup with
an email redirect, no role metadata/invitation or membership insert. A confirmed
session may submit only its own bounded request; otherwise the applicant signs in
after confirmation and submits the request from Account Security.

`deployment/supabase_auth_mfa.sql::defectrag_request_access` requires verified email
and the DB registration switch, uses `auth.uid()`, and creates a pending request,
audit event and durable notification-outbox rows. Repeated requests are idempotent.
It does **not** insert `staff_members`. Pending, rejected and revoked identities
remain outside protected workspaces even if they enroll TOTP.

`defectrag_decide_access` and `defectrag_access_directory` require
`defectrag_can_manage_access`: an active Developer plus native AAL2 and a currently
verified TOTP factor. Requests cannot choose a role or self-approve. Explicit
approval grants only Staff; approvals/rejections/revocations were not performed
in this rollout. The server, private RLS/RPC helpers and private Storage guards
retain mandatory MFA enforcement for approved Staff/Developer operations.

These are source review and existing automated test conclusions. Real pending,
ordinary Staff, AAL1/AAL2 and revocation scenarios are claimed live only when the
manual identity tests below are completed and recorded.

## Abuse protections and email

The user explicitly chose **retain native Supabase rate limits for this rollout**
and confirmed CAPTCHA is not configured. No CAPTCHA secret/provider/site key was
created or changed. Native email/auth throttling remains authoritative; the UI
disables duplicate submissions while busy and surfaces SDK errors. The project
rate-limit values were not changed or independently inspected through an admin
API; no production rate-limit exhaustion test was run.

CAPTCHA is a documented pending hardening step, not an implemented live control.
Supabase supports Turnstile/hCaptcha, but activation needs a native provider secret
in Supabase and the corresponding public widget/token integration in signup,
sign-in and recovery. Do not simply enable it server-side with the current client:
that could break those flows. See [CAPTCHA](https://supabase.com/docs/guides/auth/auth-captcha)
and [native rate limits](https://supabase.com/docs/guides/auth/rate-limits).

SMTP delivery and reset/redirect success are initially **user-reported**. No real
mail was sent by the agent. A test signup/confirmation is performed only by the
user with a separate account they control. Avoid repeated confirmation/reset
requests while testing, especially with a Gmail sender's quotas.

n8n and its Edge worker were not deployed or invoked. Access-request events can
queue durably without sending notifications. The HF flag is0; an independently
deployed Edge worker has its own environment, which was not changed/inspected.

## Manual test participation and current limit

The user authorized a separate self-controlled test email and agreed to perform
password/email steps. The live form is open in this conversation's browser.

1. Register the test identity with display name such as `QA Registration` and a
   privately entered password. Confirm the mail; record only success/failure and
   whether the landing hostname is `wizzas-defectrag.hf.space`. Never paste the
   confirmation token/link, password or authenticator details into chat.
2. Return to Staff workspace, sign in if needed, submit **Request staff access**.
   Confirm **Access: pending**, no protected history and no management directory.
3. A Developer can later sign in and complete native TOTP to view the pending
   request. Do **not** approve/reject/revoke it without the user's separate explicit
   permission. No approved-Staff post-approval MFA test is claimed in this stage.
4. Optional manual recovery regression: use the controlled test email, request a
   single reset and verify its live application landing; any password entry/change
   is performed only by the user. Keep production Developer credentials untouched.

**Follow-up verification:** the user completed signup, received and confirmed the
Supabase email, landed on the production HF application, signed in and submitted
the request. No approval was performed. This email/landing evidence is user-observed.

The agent independently observed the test account in this conversation's browser:
**Access: pending**, session not AAL2, no staff rows, no management controls and no
Developer recovery. Neither Personal nor Team history disclosed protected records.
Returning to Staff workspace loaded the same pending request, demonstrating its
persistence. A single public Capsules sample was submitted through the normal
inspection UI; the queued server rejected it with **Approved staff and required
authenticator verification are needed. Open Staff workspace.** No result/report
was produced. Source preflight places that membership check before GPU compute.
The test account was then signed out for the Developer assurance-level check.

Expected pending-account denial is also presented as generic synchronization-failed
and CHECKING MEMBERSHIP messages. This is a clarity issue, not evidence of a data
leak; a focused pending/MFA-specific status improvement is recommended separately.
No UI change or redeployment was performed during this verification stage.

The user then signed in with the existing Developer password without entering a
TOTP code. The agent observed **Access: approved**, **session not verified**, no
protected Team history, no Developer recovery and no access-management controls.
A second single public-sample inspection attempt was rejected by the queued server
with the same staff/authenticator-required message, with no result/report. This
checks the server guard for an approved AAL1 identity as well as a pending identity;
it is not merely a hidden-page test. Existing native TOTP challenge remains usable.

After the user privately entered a native TOTP code, the agent observed
**Authenticator: verified session**, Developer access management and recovery.
The controlled test request was present in the native directory as **pending /
applicant** with approve/reject actions. No action was clicked. Five existing Team
records were accessible; saved original/heatmap images downloaded as authenticated
Storage Blobs. Existing protected backend image paths then loaded successfully,
and Personal history showed the two existing owner records. This verifies the
AAL1-to-AAL2 access transition without granting any account new permissions.

The Developer-only delivery-status read showed the request event **queued** with
**zero attempts**. No delivery, retry, approval, rejection or revocation was
triggered. The account remains pending, and notification delivery remains off.

Fresh password-recovery regression remains unperformed (earlier success is
user-reported). Direct negative native REST/RPC/
Storage policy calls under pending/AAL1 credentials were not exercised; UI and
backend denial are not a substitute for every policy test. No test-account approval,
rejection/revocation or approved-Staff post-approval test is authorized or claimed.
Existing local tests were not repeated; application code is unchanged.

## Recovery and resume

For a registration-interface regression, disable only the public registration
flag through a verified build/publisher, or restore the compatible parent HF
application/config revision above. **Keep backend workflow1 and DB MFAtrue.**
Never roll back to a pre-MFA application, disable mandatory MFA or undo SQL just
to hide signup. Existing Auth identities, requests, outbox/audit rows, history and
Gallery entries must remain. No application rollback was needed for this rollout.

Private baseline/config backup/receipts: ignored
`development-support/space/registration-20261020`. Do not upload that folder.
Sanitized results: `results/registration-activation-20261020.json`.
Resume from `DEVELOPMENT_PROGRESS.md`, keeping notifications off and approval
decisions gated on separate permission. Do not restart model experiments.
