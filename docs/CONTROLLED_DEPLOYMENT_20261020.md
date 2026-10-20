# Step 5 controlled Hugging Face deployment

Completed 20 October 2026. **Space RUNNING; stop before Step 6 activation.**

Application: https://wizzas-defectrag.hf.space/
Space: https://huggingface.co/spaces/Wizzas/DefectRAG

| Revision | Value |
| --- | --- |
| Deployed source branch | `feature/auth-mfa-inactive` |
| Deployed application source | `1dfb01e8f15e26839964b58f9a7e1d1307701891` |
| Hugging Face release commit | `b9b5fd90e38f421007912f56663db26e9208bd6d` |
| Previous running HF revision / rollback target | `13af0e1cb002386ade5849739f4bd28c5736f341` |
| Main React bundle | `assets/index-C51GOc1V.js` |
| Account workspace bundle | `assets/TeamWorkspace-DVtFB4ub.js` |
| Security adapter bundle | `assets/authSecurity-C13nsxqA.js` |
| Existing stylesheet, unchanged | `assets/index-Bn4HF2vD.css` |

The final local documentation checkpoint succeeds the deployed application source;
it records results and does not represent another HF application deployment.

## Configuration and migration evidence

| Setting | Current state | Evidence |
| --- | --- | --- |
| Public `authWorkflowEnabled` | `true` | Served config verified against tested manifest |
| Public `registrationEnabled` | `false` | Served config; anonymous sign-in page has no registration form |
| HF `DEFECTRAG_AUTH_WORKFLOW` | `1` | HF variable readback and live health |
| DB `registration_enabled` | `false` | User-confirmed post-migration verification; no catalog SQL executed by agent |
| DB `mfa_required` | `false` | User-confirmed postcheck; approved non-AAL2 developer retained protected access |
| HF `DEFECTRAG_NOTIFICATIONS_ENABLED` | `0` | HF variable readback |
| Personal workspace / Gallery | Existing `1` values preserved | Unrelated HF variables compared before/after; live health and access |

The user confirmed successful manual execution of the exact reviewed migration
and successful postchecks before authorizing this deployment. Migration LF SHA256:
`cea1e451073fad9f47aca26292cb83a5d337854eef437d97f8c80b79c121e983`.
No SQL, permission update, membership decision, database-switch change, SMTP call,
invitation, factor enrollment or production-secret modification was performed.
The protected new own-status RPC exists and rejects anonymous access with HTTP401,
SQLSTATE42501; the signed-in UI successfully obtains the approved developer status.
This corroborates compatibility, but is not an independent full live catalog audit.

The notification worker and n8n workflow were **not deployed or invoked**. The HF
variable is not a substitute for disabling an independently deployed Edge worker:
that service has its own environment. No external Edge/n8n environment was changed
or independently inspected in this stage. Notification activation remains separate.

## Build and release verification

- Source and Desktop began at the same `1dfb01e` feature-branch checkpoint. Desktop
  local `frontend/public/config.js` and run guide edits were preserved.
- Built into `runtime/step5-build/cloud`, using the installed release public config
  with only the two approved flags changed; URL/publishable key preserved. No
  privileged key was introduced. Local/static working builds were not replaced.
- 62 frontend/security/worker/build-guard tests passed. The resulting 87-file
  manifest was verified, staged and accepted by the offline publisher guard.
  Already successful Python suites were not repeated because application code did
  not change in this stage.
- Source/test fingerprint:
  `d5686550fdef9e3ad4015741429eb1da012b4624c432e84c5376dfd514f4fb73`.
- Controlled publisher made 12 additive file updates; no repository deletions.
  All 149 allowlisted committed files were independently checked against Git blob
  IDs or LFS SHA256, rather than trusting the local upload-deduplication cache.
- Live root HTML, public config, main JS, workspace/security chunks and CSS matched
  the tested manifest exactly. Main JS SHA256:
  `156b30cb704873f239df1291a0cad17d94f2656f7aaff35a1c324aeab0d7b57f`.
  CSS SHA256:
  `087e3c48084e6752afdd5667f4ad43b22bd240038b904dc746f51b90b0732661`.
- HF image build completed and startup logs show the server listening on7860.
  During startup the previous container briefly served old assets; checks were
  repeated only after RUNNING. Temporary 404s from the pre-switch container and an
  incorrect verifier `/index.html` route were resolved; the application serves `/`.
- Nonfatal Vite warnings concern the intentional runtime config script and the
  existing Gradio client's Node-only branches. Real browser/API checks passed.
- Desktop's isolated cloud release and receipts were synchronized and passed its
  own manifest check. Exact hashes of its local public config, run guide and
  working local/static index files remained unchanged. Old release config backed
  up privately; no datasets/models/secrets/inspection records copied.

## Fresh live results

| Check | Result |
| --- | --- |
| Health, models, evaluation, samples | HTTP200;12 categories; personal/team/Gallery enabled |
| Public Community Gallery | HTTP200 anonymously; all3 baseline public entry IDs preserved; no publication/moderation performed |
| Unsigned private history | HTTP401 |
| Anonymous account-security RPC | HTTP401 /42501 |
| Existing developer password login | Passed; user entered credentials; no credentials handled by agent |
| Existing approved access without AAL2 | Passed;5 active Team records and2 Personal records accessible |
| Private Team storage | Existing original and heatmap loaded as authenticated Blob URLs |
| Backend Team/Personal image paths | Existing originals and heatmaps loaded under protected API access |
| Existing Team review and notes | Read successfully, unchanged |
| Personal alerts | Existing pending and acknowledged states displayed; no acknowledgment written |
| Recovery |3 existing Team archives visible to developer; Personal archive list empty; no restore/archive performed |
| Account Security | Approved developer shown; `Set up authenticator` available; no factor enrolled |
| Real guest DINOv2 | Capsules fixture: score0.2054974884, threshold0.1439922601, Anomalous; CUDA801.65ms |
| Guest image/heatmap/report | HTTP200 for all3; foreign guest history empty and foreign inspection404 |
| Real Evidence Assistant | Qwen3-4B generated a cited heatmap explanation on ZeroGPU;2532.49ms; claim quotes checked against retrieved text |
| Guest conversation | Both turns persisted in its isolated temporary session |

Runtime reported Python3.12, Gradio6.30.0, spaces0.51.3, torch2.8.0,
transformers5.20.1, huggingface-hub1.31.0. The actual GPU lease was a Blackwell MIG
device; requested Space hardware remains `zero-a10g`. Device assignment is managed
by HF. One successful lease is not a quota/concurrency/availability guarantee.

The new smoke inspection used a supplied public fixture in **temporary guest
history only**. No durable Personal/Team record or Gallery entry was created.
No retraining, new model download to the laptop, benchmark rerun or full batch
experiment occurred. All12 profiles remain configured; only one image was newly
inferred. Legacy local DINOv3 assets remain preserved; this cloud smoke uses DINOv2.
RAG remains vision-assisted text RAG with LangChain/LangGraph and Qwen; no multimodal
retrieval or vision-language upgrade was implemented.

## Outstanding tests and limits

Not claimed as live passes: a separate ordinary Staff account, non-staff/pending
identity, cross-owner account isolation, successful/failed TOTP, second-session
AAL2, developer approval/rejection/revocation, native lost-factor recovery, external
SMTP, notification retries against real Edge/n8n, and a fresh multi-image batch.
Existing automated coverage is recorded in the earlier milestone reports and is
not a substitute for these identity/integration tests. Read-only recovery visibility
is verified; new archive/restore mutations were intentionally not repeated.

Private record reads demonstrate continued access, not an exhaustive row-by-row
database backup comparison. No deployment SQL or membership mutation was issued.
Previously issued signed image URLs can remain usable until their expiry; already
downloaded images cannot be recalled. Native Supabase external-user email/redirect
and SMTP configuration remains an activation gate. Protected access management
requires AAL2 even while ordinary approved workspace access is allowed at AAL1.

## Next manual Developer TOTP test; no enforcement

1. Keep registration, DB mandatory MFA and notification delivery off. Retain an
   independently authorized Supabase Dashboard administrator recovery path.
2. In `/#team`, sign in to the existing Developer account. Confirm **Access:
   approved**, the developer role and access to existing records.
3. When ready for the next separately controlled test, select **Set up
   authenticator**. Scan the private QR in an authenticator; do not paste its seed,
   QR or codes into chat, logs, Git or screenshots. Preserve the authenticator's
   supported secure backup. DefectRAG does not issue custom recovery codes.
4. Enter the current six-digit code and select **Verify authenticator**. Confirm
   **Authenticator: verified session** and developer management visibility. Do not
   approve/reject/revoke accounts or retry notifications as part of enrollment.
5. In a second browser session, repeat password sign-in, confirm ordinary workspace
   access, then verify an authenticator code and confirm AAL2 management access.
   Use one incorrect code to verify rejection only in a controlled test; respect
   provider rate limits. Keep the original session available.
6. If enrollment fails or is interrupted, cancel only the unfinished setup and
   inspect provider error/TOTP settings. Never enable mandatory MFA to troubleshoot.
   Lost-factor recovery must use Supabase's authorized native administration path;
   password reset and n8n do not remove MFA.
7. Record the outcome and request a separate decision for Step6. No enforcement,
   registration, notification, permission or database-switch activation follows
   automatically from successful enrollment.

## Rollback plan (not used)

Previous verified application commit:
`13af0e1cb002386ade5849739f4bd28c5736f341`. The rollback baseline, old public config,
non-sensitive prior variables, release manifest and startup logs are saved privately
under `development-support/space/step5-20261020` (not for GitHub).

For a critical application regression, restore the parent revision's application
files and frontend through a new HF commit guarded against the current HEAD. Use
the parent files for each changed existing path; restore its root HTML/config so
old asset references are selected. Preserve model/data files and leave unused new
chunks unreferenced rather than deleting them. Restore/remove only the two HF
variables changed in this stage to their captured prior states, after confirming
the DB MFA switch is still false. Never revert SQL, drop tables, alter allowlists,
reset the database or bulk-replace secrets/variables. Verify RUNNING and parent
asset hashes, Gallery and password workspace access. Later mandatory-MFA activation
would require a new compatible rollback assessment; hiding setup is not recovery.

## Evidence and resume

Sanitized report: `results/controlled-deployment-20261020.json`.
Private detailed receipts, temporary guest artifacts/capabilities and public-config
backups stay in ignored development-support/runtime folders. Do not upload them.
The final Git checkpoint and guarded Desktop synchronization are recorded in
`DEVELOPMENT_PROGRESS.md` and the Git log. Resume with manual Developer enrollment
testing only after the user chooses the next milestone. No jobs remain active
locally; the HF web application continues running normally.
