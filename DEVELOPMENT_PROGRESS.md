# Public application QA checkpoint — 19 October 2026

Exploratory review completed against hosted3b68268a582dce6ad731e5a362988eb6d1d9b99e
(RUNNING), source baseline0554152. Findings and reproduction steps are saved in
docs/PUBLIC_QA_REVIEW_20261019.md. No working app code, UI design, models, datasets,
SQL policies, old records or deployment were changed during the review.

Fresh results: genuine PCB1 anomaly score0.313006 vs threshold0.141435, heatmap and
viewer passed; relevant live Qwen heatmap answer cited sources; direct score/verdict
answers and unsupported-repair abstention passed. Guest-to-staff share, saved
conversation append, staff note, alert acknowledgement, report/images, navigation
and benchmark switching passed. Two-image capsule batch: normal completed (Good,
~0.132 vs0.144); anomalous file blocked by actual ZeroGPU quota. Do not resubmit
the completed file. Supabase login is separate from Hugging Face GPU allowance.

30/31 public boundary expectations passed (unknown route405 rather than404).
Both anonymous RPC calls correctly denied401/42501. Python suite78/79 initially;
one Windows long-temp-path SQLite failure passed in the targeted shorter-path
security rerun (9/9). All79 distinct cases successfully covered across those runs.
6 frontend tests and existing batch harness passed. No new training/downloads.

Open priorities: source-handler harness reproduced late-answer context mix-up;
main views stay stale after sharing until reload; opening PCB1 can retain Candle
in input; export ignores active filters; report table exposes signed URLs/internal
fields; misleading filtered-empty and raw image-validation errors. Detailed report
separates live findings, isolated software reproductions and source-only risks.

Two labeled QA records remain in Supabase (batches QA-20261019 and
QA-20261019-BATCH), including one QA review note and four saved conversation turns.
Existing three archived records were viewed but not restored or changed. No archive,
delete, schema change or paid service. Private receipts/screen captures are ignored
under development-support/public-qa-20261019. Do not publish private capabilities.

Remaining verification: mobile override ignored (actual1280px, reset), no actual
non-staff/second staff account test, no fresh live archive/restore round trip or
sustained load/cold restart/PDF output. Quota stops further GPU tests. No local
training/server job was started; test commands completed or were stopped.

Resume: read the QA review first. Fix request-context guards and refresh consistency
before adding features; keep existing UI. Then form/export/report corrections,
followed by separately reviewed durable batch/review schema enhancements. Do not
retrain or repeat completed benchmark experiments. No fixes deployed by this review.

---

# Targeted Macaroni update completed and hosted — 18 October 2026

COMPLETED: public revision3b68268a582dce6ad731e5a362988eb6d1d9b99e serves
macaroni-recall-v1. Public model/evaluation endpoints exactly match the new
manifest for all12 products; the other10 cards match previous q95 without changes.
Browser verified Macaroni1 recall0.850/precision0.780 and Macaroni2 recall0.800/
precision0.741. Visible policy warns of normal false alarms24%/28%. Proof saved
at docs/assets/macaroni-recall.png. UI design/CSS/navigation preserved.
Desktop code/local frontend synchronized throughb74bc3b; selected policy checked
with existing Desktop .env. Personal Supabase config and personal guide hashes
preserved. Restart an existing local backend to apply the new policy.
66 backend tests +6 frontend tests and both builds passed. No new inference,
training, GPU experiment, model download, paid service or database mutation.
All original assets/results/history/static showcase preserved. This is threshold
calibration with higher review load, not better AUROC or independent validation.
No local training/test/development-server job remains running from this task.
Final documentation/proof checkpoint synchronized. Existing GitHub source export
refreshed IN PLACE fromfe912bd:290 files,11.93MB, blank public config, credential
scan passed. No duplicate model archive. Private receipts record these checks.
Future model research remains optional, not automatically started. Do not repeat
completed inference or refit banks. Rollback DEFECTRAG_CALIBRATION=normal-q95-v1
(previous policy) or normal-max-v1 (original), then restart backend/Space.

---

# Macaroni-only recall improvement — 18 October 2026

User authorized targeted Macaroni1/2 recall improvement with minimal compute.
COMPLETED locally: separate macaroni-recall-v1 normal-q80 decision overlay,
Macaroni1 recall57% ->85%, precision77.98%, normal FPR24%; Macaroni2 recall48%
->80%, precision74.07%, normal FPR28%. Other10 category cards byte-for-value
identical to earlier q95 manifest. Overall macro recall88.83%, precision90.47%,
F1 89.57%, normal FPR11.10%. These are retrospective development-score results,
not independent validation or improved AUROC. UI and README disclose false alarms.
Encoder, banks, scores, heatmaps, official split/results, history and static
showcase unchanged. Saved-map audit: all95 q95 Macaroni false negatives had full
GT-mask nonzero support at224x224, so no evidence for wholesale foreground loss.
No new inference, GPU job, rotation bank, downloads, training or database write.
66 focused backend tests passed in13.37s;6 frontend tests and both builds passed.
New model IDs for the two categories end -q80-v1; historical records unchanged.
Default installed policy macaroni-recall-v1. Roll back to normal-q95-v1 or
normal-max-v1 via DEFECTRAG_CALIBRATION and backend restart. Do not refit assets.
Next: publish incremental policy/UI, verify hosted all12 cards and visible table,
sync Desktop with configuration hashes preserved, refresh existing small GitHub
source export in place. Do not create another model archive or repeat inference.
Details: docs/MACARONI_RECALL_UPDATE.md. Folder name remains DefectRAG-v2.

---

# Macaroni follow-up diagnostic — 18 October 2026

Read-only CPU check of saved real inference scores: Macaroni1/2 current q95 recall
57%/48%, normal FPR1%/7%. Fixed normal q90 diagnostic gives recall76%/66%,
precision86.36%/80.49%, normal FPR12%/16%. This diagnostic was NOT activated;
public revision3e1bf17 and normal-q95-v1 policy remain unchanged. No GPU request,
new model, training, downloads or database mutation. Review and bounded next
research design saved in docs/MACARONI_RECALL_REVIEW.md. Authors' preprocessing
code confirms rotations supported/enabled in agnostic VisA, disabled in informed;
our adaptation omits rotations. Benefit here is unproven. Next: false-negative
mask/heatmap audit, then one preregistered isolated preprocessing candidate if
approved. Do not repeat completed baseline experiments or claim independent
validation from the existing development-exposed official test set.

---

# Recall calibration deployed and verified — 18 October 2026

COMPLETED: Hugging Face revision3e1bf17dcff9622b61b6f662af810348c8ab109e
RUNNING. Public /api/models and /api/evaluation exactly match the new manifest
for all12 products. Browser verified new sensitivity text and full metrics table,
including PCB2 recall0.840, capsules0.820, candle0.870. Screenshot saved at
 docs/assets/recall-policy.png. No fresh GPU job was requested: this update reuses
saved real inference scores and changes only decision calibration. No database
write, retraining, dataset change or model download. 56 backend tests,6 frontend
tests and both builds passed. Static showcase and original evaluation preserved.
Desktop synchronized through9c44466 with local build and personal Supabase config/
guide hashes unchanged. Restart an existing local backend to use new calibration.
Normal-q95-v1 policy is active by default when its manifest is installed. Original
policy rollback: DEFECTRAG_CALIBRATION=normal-max-v1 and backend/Space restart.
Future work: independent validation before claiming guaranteed recall/FPR;
approved feature/model research for weak Macaroni1/2; prior staff-role/load-test
gaps remain as documented. Do not rerun completed experiments. No local training,
server or test process was left running by this task. Folder rename NOT performed;
Desktop remains DefectRAG-v2; follow docs/FOLDER_RENAME.md for coordinated changes.
GitHub export refreshed IN PLACE from9c44466:284 source/public files,11.86MB,
blank public config and credential-pattern scan passed. Receipt saved privately at
development-support/space/github-export-refreshed.json. No duplicate model archive
was created. Final documentation-only checkpoint should be synchronized; all
implementation and hosted verification work for this calibration is complete.

---

# Recall-oriented calibration milestone — 18 October 2026

User selected prioritizing anomaly recall with more false alarms. Audit reproduced
all 12 existing confusion matrices/precision/recall/F1 from saved genuine scores;
checked normal holdout content grouping, train/test nonoverlap and label polarity.
No inference, retraining, asset download or database mutation was needed.
New separate normal-q95-v1 manifest and guarded local/ZeroGPU adapter are ready.
Original cards, banks, encoder, evaluation, history and static showcase preserved.
Retrospective macro recall60.17% ->83.83%, precision97.59% ->93.26%, F1 68.63% ->
87.56%, normal false-positive rate2.42% ->7.43%. AUROC and image scores unchanged.
Policy chosen after viewing development diagnostics; NOT independent validation.
Macaroni1/2 remain limited (recall57%/48%). No guaranteed future recall/FPR.
56 focused calibration/highres/answer/API tests passed in9.66s,6 frontend tests
passed,local and separate cloud UI builds passed. Personal Supabase public config
copied into isolated cloud build and checked by hash (contents not logged).
Initial sandbox API tests stalled and were terminated; rerun outside sandbox
passed. No training/development server remains running from these checks.
Deployment and Desktop synchronization are pending this checkpoint; complete
those, verify public /api/models and /api/evaluation agree for all12 categories,
verify the visible performance page and record the published revision. Do not
repeat model experiments. New model IDs end -q95-v1; old records retain original
thresholds. Rollback: DEFECTRAG_CALIBRATION=normal-max-v1 and restart backend.
Details: docs/SENSITIVITY_CALIBRATION.md; audit results/recall_threshold_audit.json.
Folder rename was discussed but NOT performed. The Desktop path is still
C:\Users\User\Desktop\DefectRAG-v2. Source .venv/experiments junctions target that
path and sync_code.ps1 hardcodes it. A coordinated rename must update those and
verify the virtual environment. See docs/FOLDER_RENAME.md. Public Space unaffected.
The existing prepared GitHub export predates this calibration; do not claim it is
current until refreshed from the completed code checkpoint.

---

# Answer focus, brand and GitHub publication preparation — 18 October 2026

COMPLETED: code checkpoint59b61d11a008c70cc9df9d68f557ee8c6f8b6739, synced to
Desktop with rebuilt LOCAL frontend and both personal config/guide hashes intact.
Cloud b715fbf7b7d6237e9677550bda8dce02ce54ccb4 RUNNING; visible About/logo/RAG/
objective metrics heading verified. Source-only GitHub export is prepared at
C:\Users\User\Desktop\DefectRAG-v2\development-support\github-ready\DefectRAG.
Manifest275 source/public files plus export receipt,11.76MB, blank public config,
no Git history/models/datasets/private runtime/environments/build outputs. Known
credential-pattern scan passed. No GitHub repository was created or pushed.
README includes SVG hero/version badges/Mermaid diagram/actual dashboard preview.
All original model/evaluation files and static showcase backup remain preserved.
38 answer/API tests +6 frontend tests and both builds passed. No active local
development/training process was initiated. Existing local server needs restart
to load changed Python code; do not stop unrelated user processes automatically.
Further work is optional validation-based recall calibration (no test tuning),
previous role/load acceptance gaps, and a fresh live answer check when a staff
session is available. Do not repeat completed model experiments or asset downloads.

### Completion details and earlier preparation notes

LATEST: b715fbf7b7d6237e9677550bda8dce02ce54ccb4 RUNNING. Public About/new
logo, explicit RAG copy and objective evaluation heading verified in browser.
38 answer/API regressions and6 frontend tests passed; both builds passed, CSS
unchanged. Details docs/UI_AND_ANSWER_POLISH.md. No active staff session in the
new test browser; no fresh live Qwen response is claimed for this copy/assembly
update. Previous genuine RAG and Supabase acceptance remains preserved. No new
vision request, training, threshold study, model download or database change.
README and GitHub preparation scripts ready; commit then sync -SyncFrontend and
create Desktop source export. The export manifest will identify the source commit.
Existing Desktop public config and custom guide must retain their original hashes.

User requested question-focused RAG answers, objective interface text, clearer
recall/RAG/SOP explanation, new product-inspection logo and polished GitHub README.
Working from746a5bc; no models/thresholds/evaluations/database records changed.
Found unconditional measurement-prefix assembly in backend/rag.py. Heatmap and
documentation answers now omit unrelated verdict/score prefixes; score meaning
answers are direct; explicit result summaries retain trusted facts once. Existing
conversations preserved. Question-focused prompt added; source/citation guards stay.
38 focused answer/API tests passed13.48s (initial sandbox run stalled and stopped;
outside-sandbox run passed). Six frontend checks passed. Both cloud/local builds
passed; original CSS SHA remains087e3c48084e6752afdd5667f4ad43b22bd240038b904dc746f51b90b0732661.

Cloud update published b715fbf7b7d6237e9677550bda8dce02ce54ccb4 (8 files).
Pending this checkpoint: verify updated live About/logo and one existing-record
heatmap answer, then commit/sync updated local build with personal config preserved.
No new inspection/retraining needed. Existing static showcase build is preserved.
README redesigned with original SVG banner, real version badges, Mermaid architecture,
honest benchmark/recall distinction, reproducible source setup and explicit limits.
GitHub export script allowlists tracked source, resets public config, excludes Git
history/private state/models and scans credential-like values. Optional pinned
asset downloader added; only --list executed, NO model download. Source clone path
now accepts DINOv2-only encoder assets in launcher. No GitHub repo/push authorized.
After final code commit, sync Desktop with -SyncFrontend, then run export from
Desktop to development-support/github-ready/DefectRAG. Review manifest/size/links;
do not upload entire working folder or private migration/runtime evidence.

## Previous deployment checkpoint (completed evidence retained)

CORE PHASES2–5 MIGRATION DEPLOYED AND VERIFIED for the available developer account.
Public: https://huggingface.co/spaces/Wizzas/DefectRAG
Cloud commit3717008401fcf9c85612ce6d4c0c77b629c39f53, RUNNING, ZeroGPU,
staff_persistence_enabled=true. Core code checkpoint53c48ce; this final documentation
checkpoint is identified by Git HEAD and the Desktop sync receipt. Do not redeploy
or repeat finished tests simply to resume. Source working tree should be clean
after checkpoint commit; Desktop retains the user's two config/guide modifications.

Verified final outcomes:
- Same original React CSS SHA256 preserved, navigation/appearance/static/local
  backups intact. Existing all12 benchmark metrics/models/calibrations unchanged.
- Existing all12 local/cloud DINOv2 parity and genuine cited Qwen tests preserved;
  no retraining or benchmark rerun. Latest13 CPU boundary checks passed.
- User manually executed reviewed SQL and signed into existing developer account.
  No agent SQL, schema/policy/account changes or service credentials used.
- Both RPCs: approved developer success and anonymous401/42501 verified. Invalid
  JWT403; missing workspace401. No existing nonstaff account available.
- Actual PCB1 a6351615259d42868b766a004f5dd303 saved to Supabase, six conversation
  turns including real contextual Qwen answer, exact note and acknowledged alert.
- Same record, conversation, note, images, acknowledgment survived browser reload,
  archive/developer restore and an actual Space deployment restart. Signed report,
  CSV and both private Supabase images200 after restart.
- Guest batch quota failure safely stopped pending submissions; old successes
  retained. User then signed into HF Wizzas (regular FREE verified) and staff in
  the embedded Space. Both unfinished Capsule images processed in successive
  one-image runs under PHASE5-STAFF-BATCH; latest run1 completed/0 failed. Separate
  staff browser session's signed export verified both durable IDs:
  88b2489b5759419a9caad724ade0ae53 (Uncertain0.20549749),
  ee823f7db3ae4a8fb687bb7b4d50896c (Good0.13208820). No duplicate model retries.
- Captured final logs: queue/session/response-started/CUDA-init/OOM counts0;
  bounded observation only. No local development or training jobs started.

Remaining limits/next work (do not mislabel these as passed):
1. Authenticated nonstaff RPC denial, ordinary-staff ownership/restore denial and
   distinct second-user collaboration need real existing accounts. User reports
   no nonstaff account. Do not create accounts or change allowlists without scope.
2. Single-click successful combined two-file batch remains unverified; both files
   actually succeeded as separate one-image submissions. Multi-file rejection and
   quota-stop behavior plus scheduler software checks passed. Do not re-infer the
   saved images just to repeat a completed individual case.
3. Free quotas/cold starts/shared capacity remain; long-duration concurrent load
   and broad reconnect campaigns were not run. No paid operation is authorized.
4. Staff-submitted answers lack verified model provenance. Acknowledgment lacks
   actor/timestamp. Existing stats/list/archive/export bounds remain documented.
5. Anonymous history is temporary. Staff records are durable. HF GPU identity and
   Supabase staff login are separate; embedded/direct app sessions can differ.

Read docs/PUBLIC_APPLICATION_GUIDE.md, ZEROGPU_PHASE4_RESULTS.md and
ZEROGPU_PHASE5_RESULTS.md. Sanitized evidence: docs/zerogpu_phase4 and
docs/zerogpu_phase5_final. Private reports/logs/capabilities/confirmation stay in
Git-ignored development-support/space; never publish that directory wholesale.
No new large ZIP/model/environment/dataset copy was created. The hosted app stays
running; no new model tasks should be initiated after this checkpoint.

---

## Superseded continuation notes (final checkpoint above takes precedence)

# Active Phase 4/5 continuation — 18 October 2026

LATEST: final public Space3717008401fcf9c85612ce6d4c0c77b629c39f53 RUNNING.
Core Phase4/5 developer flow VERIFIED, including actual restart preservation and
new Qwen contextual generation. Final CPU boundaries13/13 passed, staff enabled,
CSS unchanged. Post-restart signed report/CSV/images200, six saved turns and
acknowledgment persisted. See docs/ZEROGPU_PHASE4_RESULTS.md,
docs/ZEROGPU_PHASE5_RESULTS.md and docs/PUBLIC_APPLICATION_GUIDE.md.

Remaining active check: direct-browser batch0 successes hit guest quota; scheduler
submitted only first image and marked second not submitted, preserving old data.
User has now signed into both HF (Wizzas regular FREE verified) and Supabase staff
inside the hosted iframe. Browser file-chooser automation failed twice across that
iframe; no GPU work was submitted by those failed upload attempts. User is manually
uploading ONLY capsules_good.jpg/capsules_anomalous.jpg to PHASE5-STAFF-BATCH.
Await their submission confirmation, read the actual outcome, and record it.
Do not re-run passed inspection/Qwen cases. No nonstaff account exists; real
authenticated nonstaff/ordinary-staff/second-user role acceptance remains limited.

After batch outcome: capture bounded final runtime/error summary, copy sanitized
evidence, update this header, commit and sync Desktop via sync_code.ps1. Preserve
existing config/guide hashes. No additional release ZIP, model copies or retraining.
No local development/training jobs were started; hosted app remains running.

## Continuation milestone details

User explicitly confirmed successful manual SQL execution in the existing project.
Private migration-confirmed.json records that confirmation and reviewed SQL hash.
Agent did not execute SQL. Phase4 incremental deployment published as
ebbcf47cdd1f87dcd7f94219fecaf7d5bac35db4 (13 changed files); startup/live staff
acceptance still requires verification. Resume only unfinished staff/RPC/persistence
and final stability checks. Do not rerun all12 model smoke tests or benchmarks.
Source baseline5dea41f. Preserve user config/guide and existing database records.

Phase4 first live checks PASSED: both RPCs deny anonymous caller401/42501 (not
missing functions); public CPU/API/assets checks13/13 passed, unchanged CSS,
12 categories, ZeroGPU=true, missing workspace401 and invalid staff JWT403.
Cloud startup RUNNING, captured missing-session errors0. No staff login yet;
await user's sign-in at the existing #team page. Do not claim staff persistence,
RPC success or nonstaff authenticated denial before actual account tests.
Investigated official HF quota docs: guest2min/day, free account5min/day, resets
24h after first GPU use. Supabase login and HF GPU identity are separate. Prepared
small batch transport fix stops pending submissions after quota error and retains
successful results; it does not increase quota or auto-retry. Tests use fixtures,
not GPU. Keep these changes for the next consolidated deployment after staff tests.

Phase4 staff milestone: approved existing developer signed in themselves. Genuine
PCB1 inspection a6351615259d42868b766a004f5dd303, score0.3130/threshold0.1618,
Anomalous, displayed666ms, saved directly to Supabase (visible in Staff workspace).
Measurement answer and real LIVE LLM CITED heatmap answer succeeded, exercising
the conversation append RPC. Continue notes, acknowledgement, reload/report,
archive/recovery and post-deployment restart preservation on this same record.
User confirms no existing nonstaff account: authenticated nonstaff denial remains
unverified; no account is created. Avoid repeated GPU work on this passed case.
Staff milestone2 PASSED: exact note saved through existing staff_notes RLS,
acknowledgement RPC changed queue to0 pending/Acknowledged, full browser reload
retained the shared inspection, both answers (four turns), images and exact note.
Testing reversible archive/developer recovery only on the single owned fixture;
no pre-existing staff records were present or modified.
Staff milestone3 PASSED: owned fixture archived then restored through developer
recovery; exact note, four conversation turns and both private images retained.
Main dashboard history reopened the shared record. Signed CSV/report returned200,
report storage=supabase and alert acknowledged=True; both signed Supabase images200.
Exact measured score0.31300604343414307, threshold0.16181933879852295, inference
666.43ms on CUDA. Private phase4-staff-artifacts.json/report/export saved. No tokens
are copied into public evidence. Next: final consolidated phase5 deployment,
verify this same durable record after restart, one bounded real two-image staff
batch and final logs. Do not repeat the passed inspection/Qwen conversation.
Phase5 published3717008401fcf9c85612ce6d4c0c77b629c39f53, runtime RUNNING. The
same inspection, prior four conversation turns and exact note survived the real
Space deployment restart; no re-inference/recreation was needed. Checking a new
contextual question against persisted history, then one bounded batch. Existing
anonymous session history remains intentionally ephemeral; only staff data durable.

## Prior verified checkpoint (SQL gate below superseded by confirmation above)

Phases 2 and 3 VERIFIED. Phase 4 prepared but disabled; Phase 5 partially verified.
Latest user answer: **SQL not executed yet**. Do not execute SQL or perform staff
database-writing/RPC tests. User will manually execute the exact reviewed
deployment/supabase_additive_conversations.sql. No additional phase approval is
needed; successful manual SQL execution and account-based acceptance are the gate.

Current verified cloud: a31f52b64c91b7d6dab34113bc17a5bfac37ff72,
https://wizzas-defectrag.hf.space. Real DINOv2 all12 inference and real Qwen3-4B
cited RAG passed. Existing React/CSS retained, no model training or new benchmark.
Phase3 source checkpoint: 2c4c31561c6451c25487a56e818fa71faa14f8b3.
The next Git commit adds readiness/error handling, bounded staff export pagination,
cloud-specific archive wording, nine security software checks and acceptance docs.
Those readiness changes are NOT yet deployed to the cloud; do not confuse source
readiness with live staff acceptance. Avoid another rebuild before SQL is ready.

Completed evidence (do not repeat):
- Phase2: 24 real images locally +24 in cloud, all12 categories. Verdict parity
  24/24; maximum score difference0.00052985549. Original benchmark results intact.
- Phase3: real Qwen heatmap/context answers passed citation/quote checks; measurement
  answers and scope refusal passed; ten saved turns. CPU BGE subprocess fixes the
  diagnosed ZeroGPU fork interaction. No Qwen weights downloaded to this laptop.
- Browser QA: nine navigation destinations locally and in cloud; genuine Cashew
  inspection4551ace05dba4237a22a1630f7b18d34 (score0.24145314, threshold0.13224798,
  Anomalous), live cited follow-up, history archive/restore, populated image/report
  evidence and signed CSV export passed. Generic Gradio private-file routes403.
- Browser batch: one real Capsules image completed (Good, displayed score0.132,
  threshold0.197); second image rejected by anonymous ZeroGPU run quota. UI showed
  1 completed/1 failed and retained success. Not a fully passed two-image batch;
  no retry or paid quota purchase. Screenshot and limitation saved.
- Existing44 focused regressions passed at Phase3. Latest9 security software
  tests passed0.63s; these are local fixtures, not proof of live Supabase RLS.
  Latest isolated frontend production build passed; original CSS unchanged.

Private resumable evidence: development-support/space (Git-ignored). Full reports
contain workspace secrets/signed capabilities: never publish them. Sanitized
summaries and screenshots: docs/zerogpu_phase2, docs/zerogpu_phase3,
docs/zerogpu_phase5; see docs/ZEROGPU_PHASE4_READINESS.md and
docs/ZEROGPU_PHASE5_PARTIAL_RESULTS.md.

Exact resume sequence:
1. Read this checkpoint, Git status and Phase4 readiness doc. Preserve Desktop's
   existing frontend/public/config.js and deployment/RUN_AND_DEPLOY.md user edits.
2. Await explicit user confirmation that the reviewed SQL executed successfully.
   Do not apply SQL, create accounts or create migration-confirmed.json before it.
3. After confirmation, record it privately, build isolated UI with existing public
   Supabase config and publish phase4. Existing RLS/tables/storage remain intact.
4. User signs in themselves. Test both RPCs with approved staff, anonymous and a
   real existing nonstaff account; no fabricated claims from software mocks.
5. Verify durable inspections/images/conversations/acknowledgements, collaboration,
   reports, archive ownership and developer recovery. Finish remaining quota,
   refresh/restart and multi-user acceptance; only then claim Phases4/5 complete.

Future hardening: staff-submitted conversation answers lack verified model
provenance; alert acknowledgements record no actor/timestamp. Staff dashboard
statistics cover latest1000 active records; archive operates on up to500 matches.
Anonymous history is temporary and quota-limited. No fitting/training jobs running.
Owned local compatibility server on8784 was stopped; no listener remains there.
original local app/Ollama/user processes are left alone. HF hosted app stays live.
Desktop code sync uses deployment/space/sync_code.ps1 with ff-only Git and checksums
for existing config/guide. Its private receipt records the exact synced commit.
Reviewed SQL SHA256: 025ef75f224fbefda7d24b9a291b4532ec43b014d8f7659209cd8de4578beb47.

---

## Superseded chronological notes (latest checkpoint above takes precedence)

# Phases 2–5 authorized — 18 October 2026 — IN PROGRESS

LATEST MILESTONE: PHASE3 LIVE CLOUD RAG PASSED at a31f52b64c91b7d6dab34113bc17a5bfac37ff72.
See docs/ZEROGPU_PHASE3_RESULTS.md and sanitized docs/zerogpu_phase3/rag-summary.json.
Existing BGE CPU execution now isolated in one CPU-only child to avoid corrupting
the ZeroGPU parent/fork runtime. Real Qwen3-4B generation passed (85 tokens2.465s,
peak8601.55MB); contextual follow-up passed (90 tokens2.696s,peak8649.42MB). Same
Blackwell48GB, same weights/revision; no laptop Qwen download. Ten conversation
turns saved for real inspection527791824aea4124b9f60ec9d173b048. Measurement-only
answers and scope refusal verified. Do not repeat these successful GPU checks.
Phase3 private report development-support/space/phase3-cloud.json; verifier resumes
passed cases and creates only ONE new integration inspection after an ephemeral
rebuild if the old record is genuinely gone.

Phase4 remains pending the user's MANUAL SQL success confirmation. No database
modification/RPC call has been performed. Publisher phase>=4 refuses to enable
staff persistence without development-support/space/migration-confirmed.json,
which must only be created after explicit user confirmation. Preserve exact reviewed
SQL. Continue UI/error/transport checks and other independent development now.

LATEST CHECKPOINT: Phase2 code 60a9e49, security/sharing checkpoint b1f28af.
Desktop fast-forwarded to60a9e49 with existing public config/guide hashes preserved.
44 focused regressions and6 new security software tests passed. Evidence XML in
development-support/space. Source changes after b1f28af are active Phase3 fixes.

Phase3 cloud candidate startup loaded/packed8.65GB successfully (Qwen4B plusDINO).
Initial cloud commit d09a296 failed CUDA worker initialization before any inference,
twice. Targeted CPU embedding warmup deferral/eager attention commit cd9f54c restored
vision: real new PCB1 request47ec26ea212841c7b83c47584e6aa10c and measurement answer
passed. After first BGE retrieval, generation worker again reported No CUDA GPUs
are available. This points to CPU embedding runtime contaminating parent GPU/fork
state; exact internal probe is unconfirmed. New fix isolates BGE loading/inference
in a bounded CPU-only subprocess; same model/CLS/L2 pooling, same Qwen and vision.
That Phase3 fix is being uploaded; inspect latest publish-phase3 receipt/runtime
and resume verify_rag without repeating completed all12 cases. Full cloud RAG is
NOT yet verified. No Qwen weights were downloaded to the laptop.

User explicitly says: approved migration is for MANUAL execution only; agent must
not directly modify Supabase. Await their success confirmation before RPC tests.
Do not run migrations or create test accounts. Staff login is available when ready.
Documented hardening limits: no model provenance attestation for staff-submitted
answers; acknowledgement boolean lacks user/timestamp. Exact reviewed SQL includes
NULL checks and remains unchanged since their approval.

LATEST MILESTONE: Phase 2 local/cloud PASSED; docs/ZEROGPU_PHASE2_RESULTS.md.
Cloud commit 3784513453133497d4249a00f7daa32571a3bfef. All 24 per-environment
real integration cases saved; all verdicts match, max score difference0.00052986.
No missing-session/response-started errors in the captured post-test cloud log.
Hub1.31.0 cloud verified. Guest quota stopped after7 cases; resumed only unfinished
cases with the verified regular free HF account. No paid operations. Anonymous
history, artifacts and reports are session-isolated. Do not rerun passed cases.

Migration review update: user approved the exact reviewed SQL for manual execution
only, NOT direct database modification by the agent. Await confirmation of their
successful execution before testing RPCs with staff/anonymous/nonstaff accounts.
Record limitations: staff-submitted conversations lack model provenance attestation;
alert acknowledgements lack actor/timestamp. Do not enlarge the reviewed migration.
Phase4 repository scaffolding is not enabled in the cloud until its readiness gate.
Cloud live RAG is next. Local RAG already passed against existing records.

User explicitly approved continuous Phases 2–5 from 5fdff26. Earlier STOP/approval
notes below are historical. Preserve React appearance, local app/static showcase,
models/results/configuration. Do not train, pay, delete data or replace architecture.
Additive database migrations must be reviewed before execution. User can sign in
to an existing staff account when the test page is ready; do not request passwords.

Phase 2 implementation is isolated under deployment/space. All 12 existing banks
load eagerly with checksums; original highres encoder, PCA/scoring/thresholds and
heatmaps are reused. Browser session namespaces isolate anonymous history; image
and report links use expiring signed capabilities. Sequential batch transport
preserves existing result/error contracts. Fresh per-job Gradio clients close
deterministically; cloud stream lifecycle still requires verification.

Local 24-request smoke PASSED (one normal/anomalous resized public sample per
category), including real CUDA output, all heatmaps/reports, same-bank checks,
cross-session isolation, unsigned-image rejection and invalid image rejection.
Saved private report: development-support/space/phase2-local.json. Do not repeat
these successful GPU requests; verifier resumes saved cases. This is integration
evidence, not a rerun or revision of the model benchmark/AUROC.

Phase 2 cloud update is in progress. First upload failed before committing because
Windows default decoding corrupted the README emoji; explicit UTF-8 fixed it.
Hub 1.31.0 is verified published and satisfies Transformers>=1.31 and the platform
datasets<2 dependency, replacing the Phase1 Hub 2.2 cloud warning. Production local
dependencies unchanged. Check publish-phase2 receipt and Space runtime before any
next upload. Existing phase1 Space remains until a commit succeeds.

Read-only Supabase probe: public auth settings HTTP200; staff_members,
shared_inspections and staff_notes reject anonymous reads (401/42501). This is
not yet authenticated RLS verification. Existing public config URL/key reused,
no credentials printed, no database changes. User can sign in when ready.

Phase 3 provider scaffolding: inject a generator into the existing EvidenceWorkflow,
keep existing BGE CLS/L2 pooling on CPU and existing citation/measurement checks.
Qwen3-4B-Instruct-2507 candidate pinned cdbee75f17c01a7cc42f958dc650907174af0554,
8,044,982,000 weight bytes. Cloud-only loading planned; no laptop Qwen download.
Must verify actual cloud RAM/GPU/time/quality before claiming live generation.

Active local development server: isolated port 8784, exec session 28223 (PID17032).
No training/benchmark jobs. Next: cloud all12/parity and stream checks; phase2 Git
checkpoint; bounded live RAG local/cloud tests; additive persistence migration
review then authenticated staff tests. Do not stop simply because a phase finishes.

---

# Historical ZeroGPU Phase 1 — 18 October 2026 — core passed, issues recorded, STOPPED

User approved React + Gradio Server architecture and Phase 1 compatibility ONLY.
Phase 1 passed locally and on the existing empty Wizzas/DefectRAG ZeroGPU Space.
STOP here. No Phase 2, full RAG migration, Qwen download, training, Supabase
schema change or full production deployment is authorized.

Read docs/ZEROGPU_PHASE1_RESULTS.md for detailed evidence and limitations;
deployment/zerogpu_phase1/README.md for exact local resume commands. All new
implementation is isolated under deployment/zerogpu_phase1. Existing React/backend
source, CSS, dist/static showcase, models, thresholds, data and evaluations remain
unchanged. Desktop's preexisting config.js and RUN_AND_DEPLOY.md edits are preserved.

Completed: original React served by gradio.Server, nine navigation pages checked,
file upload, real @gradio/client -> scheduled DINOv2 -> saved score/heatmap -> React,
comparison/zoom, HTTP report/history/evaluation/CSV and identical production CSS.
Exactly one real local and one cloud inspection were run; no benchmark repeated.
Local score 0.3130886257; cloud 0.3130060434; both Anomalous, threshold 0.1618193388.
Cloud GPU: RTX PRO 6000 Blackwell Server Edition MIG 2g.48gb; ZeroGPU=true.
Cloud Python 3.12.12 / Torch 2.8.0 / Gradio 6.30.0 / spaces 0.51.3 /
Transformers 5.20.1 / Hub 2.2.0. Local original production environment unchanged.
Gradio/old Transformers Hub conflict resolved only in isolated test environment.
One HF CONFIG_ERROR fixed by removing +cu128 from requirements' Torch version.
Unused preinstalled datasets/Hub dependency warning remains documented.
After successful result delivery, cloud logs show Gradio SSE missing-session 404
errors and a response-already-started exception. Immediate server condition traced
to missing pending_messages_per_session entry; reconnect/cleanup trigger remains
unconfirmed. This needs bounded lifecycle diagnosis before a production migration.

Public test: https://huggingface.co/spaces/Wizzas/DefectRAG
Cloud commit 84df9af3f59b2fe43fdb6ad14a1820c930329abc. Only public PCB1 fixture
and its bank are accepted; no private history/config, RAG, batch or cloud staff
migration published. The separate Wizzas/defectrag-inference Space is untouched.
Read-only metadata and local/cloud verification saved under
development-support/zerogpu-phase1 and docs/zerogpu_phase1. Genuine local artifacts
and isolated SQLite remain in runtime/zerogpu-phase1. No new large release ZIP.

Owned local adapter on port 8783 stopped after testing. No owned training or
inference job remains. HF minimal test remains hosted/idle and can sleep; temporary
history is not durable. All other existing user processes are left alone.

Next only after approval: diagnose SSE session cleanup; review HF iframe identity/quota and restart
tests, clean the unused cloud dependency warning, then migrate bounded vision
requests for remaining existing banks with approved parity checks. RAG and durable
Supabase persistence remain later gates. Do not repeat completed work or rerun
publish_minimal (it intentionally refuses to overwrite the existing test).

---

# Historical ZeroGPU assessment — 17 October 2026

User requested feasibility/architecture review ONLY before major implementation.
Assessment complete in docs/ZEROGPU_MIGRATION_ASSESSMENT.md. STOP here for approval.
No UI, application code, dependencies, models, data or cloud services changed.
No GPU runs, installations, model experiments, rewrites, new ZIPs or deployment.

Recommendation: preserve the exact React/Vite UI in one Gradio SDK Space using
documented gradio.Server mode; @gradio/client transports scheduled GPU requests,
existing CPU/FastAPI services retain reports/evaluation/history contracts. Use a
separate ZeroGPU runtime adapter for DINOv2 (DINOv3 optional), CPU BGE retrieval,
an injected in-Space Transformers generation provider, and the existing Supabase
project for durable authenticated history/artifacts/collaboration. Proposed cloud
LLM candidate is Qwen3-4B-Instruct-2507 (not downloaded or tested for this app).
Existing local Qwen2.5-3B/Ollama remains unchanged. No model retraining proposed.

Current Desktop Git HEAD 67b2378. Preserve existing user edits to
deployment/RUN_AND_DEPLOY.md and frontend/public/config.js. Unlike older notes,
Desktop public and built configs now contain a non-placeholder Supabase URL and
publishable key. Do not overwrite them with the blank source-mirror config.
No live database/schema/RLS/login was checked; account/Space entitlement unknown.

Key risks: Gradio route ordering and HF iframe quota headers; lazy CUDA loading,
worker isolation/locks and CPU-only startup computations; unauthenticated global
SQLite/history must not be exposed publicly; ephemeral disk; separate Supabase/HF
identities; missing durable backend message/alert/artifact repository; generation
JSON differences, quota/cold starts and exact dependency compatibility. No claim
of cloud performance, numerical parity, or always-free uninterrupted availability.

Next after approval: only an isolated Phase 1 test retaining the React build,
one queued existing-model job, actual account hardware/quota context and dual-auth
transport. Then scoped vision parity, one generation provider, additive Supabase
migration and full UI/persistence acceptance. Details, options, files and gates
are in the assessment. Do not rerun old experiments or start implementation now.

---

# Local folder consolidation — 16 October 2026

Follow-up editor fix: backend/highres.py explicitly types the optional encoder
and checks it before .device/.encode access, addressing possible-None diagnostics.
Six focused detector tests passed; report development-support/device-typing-tests.xml.
No model assets, thresholds or saved benchmark results changed. Actual VS Code
hover diagnostics were not supplied; if an underline persists, inspect its exact
message and confirm the local .venv interpreter. No experiment rerun is needed.

The subsequently supplied reportOptionalMemberAccess screenshot was for the
legacy backend/vision.py. The same explicit optional type and checked local
encoder fix is now applied there. One real CUDA DINOv3 PCB1 inspection passed
(score 0.0961143672, Anomalous); development-support/legacy-device-smoke.json.
No training, thresholds, model assets or existing results were changed.

COMPLETED AND PAUSED near 4% usage at the user's request. Both receipt files
confirm status=passed. All 228 experimental receipt files are hash-verified;
both 12-category experiments, banks/results/caches, legacy projects, interpreter
and dependencies are now inside Desktop\DefectRAG-v2. Real CUDA API inspection,
inspection-grounded assistant, pip/uvicorn launchers and private-row preservation
passed. Existing CUDA PyTorch 2.8.0+cu126 retained, no packages reinstalled.
No training/benchmark or owned preview server remains. Global Ollama is unchanged.
No more development tasks should begin until the next user instruction.
On resume, read these receipts and Git status; use the simple command below.
Do not repeat migration, feature extraction, fitting or successful benchmarks.

User requested one Desktop application folder, without duplicating large assets.
This section supersedes old interpreter paths below. Consolidation status is
authoritative in development-support/consolidation-moves.json and
consolidation-verification.json. Only status=passed confirms all final checks.

Target: C:\Users\User\Desktop\DefectRAG-v2. Existing environment moves from
Desktop\.venv-defectrag into .venv (user had already moved it out of Verified).
Activation and executable entry points are repaired offline; no package download
or CUDA replacement. Local .python-deps replaces the Codex PYTHONPATH dependency.
Both complete experiments move here into experiments; the source mirror gets
a junction to avoid duplicate storage and accidental reruns. Original VisA stays
unchanged in Downloads. Legacy Unified project (including datasets/secrets) and
remaining Verified Git history are preserved privately under
development-support/legacy-projects, excluded from Git and release packaging.

Run after successful verification:
cd C:\Users\User\Desktop\DefectRAG-v2
.\Start-DefectRAG.cmd -Port 8767
VS Code interpreter: .venv\Scripts\python.exe. No external overlay variables.
The existing base Anaconda Python and global Ollama remain system requirements.

No new large ZIP is created. Existing local-accuracy and highres-benchmark-assets
ZIPs become optional backups after both experiments and real CUDA/API checks pass.
Deleting them removes independent backups, not the consolidated on-disk assets.
Do not delete runtime, models, experiments, .venv, .python-deps or legacy datasets.
No training reruns are authorized or necessary. Old owned previews on 8766/8771
may be stopped for consolidation; do not stop unrelated Python/Ollama processes.
Resume any incomplete move by inspecting the receipt before touching directories.

---

# Completed accuracy upgrade — 16 October 2026

This is the latest checkpoint; older sections below are historical. Preserve
every earlier model, experiment, dataset, history and release. Previous upgrade
is still recoverable at commit 39590a6. Final Git identity and packaging/sync
status are recorded in the sibling accuracy ZIP receipts and
development-support/release_sync_receipt.json; inspect these before repeating.

Completed: AnomalyDINO-inspired frozen DINOv2 Small/14, 448px short edge with
aspect retained, unsupervised PCA foreground, image-balanced normal memory up to
32,768 vectors. Three fixed benchmark seeds 42/43/44, all 8,659 official train
normals and identical 2,162 official test images across all 12 products. This is
a custom adaptation, not exact paper reproduction or weight fine-tuning.
Prior test exposure is disclosed; no fresh untouched-test claim. Masks and test
anomaly labels never fit the bank, foreground heuristic or operating threshold.

Measured overall means (original -> candidate): image AUROC 85.38% -> 95.13%,
image AU-PR 86.47% -> 95.74%, pixel AUROC 92.96% -> 98.60%, pixel AU-PR
33.29% -> 43.04%. Macaroni 2 image AUROC 48.27% -> 83.20%. Cashew image
AUROC regresses slightly; Cashew and Pipe fryum pixel AP regress. All rows and
seeds are saved, including regressions. Official VisA reports mean AUROC and
AU-PR; supplementary mean AP is separate from YOLO bounding-box mAP@IoU.

Operational model is a separate fixed-seed normal-holdout bank installed beside
the original models in models/highres. PROFILE.json enables auto selection;
DEFECTRAG_PROFILE=legacy restores the original DINOv3 detector. Its conservative
threshold yields macro precision 97.59%, recall 60.17%, F1 68.63%. Some anomalous
images are classified Good. High AUROC is not classification accuracy. No
threshold adjustment after test exposure was performed.

Saved assets: models/encoder_dinov2 (revision/hash/license receipt),
models/highres (all 12 operational banks/cards), experiments/dinov2_highres_v1
(all completion receipts, four banks per product, split/calibration/predictions,
metrics and intermediate caches/maps). Original DINOv3 assets are unchanged.
The benchmark finished successfully; do NOT repeat completed experiments or
restart scripts.train / benchmark_official / benchmark_highres.

Verification: 46 Python tests, six frontend checks, both builds, 24 real API
inspections across all 12 products, five assistant cases including real Qwen,
CPU/CUDA checks, browser benchmark profile switch and static provenance/privacy
checks passed. Actual receipts: results/software-tests-highres.xml,
highres_application_verification.json, highres_preservation.json and
static_verification.json. See docs/ACCURACY_VERIFICATION.md for exact limits.
The 25 static examples retain their original DINOv3 measurements; the static
benchmark includes both reports and does not pretend to run live inference.

Recoverable release artifacts (unique names; never replace earlier archives):
- DefectRAG-local-accuracy.zip: application, both detector profiles, builds/docs.
- DefectRAG-static-accuracy.zip: saved-example dashboard for free static hosting.
- DefectRAG-highres-benchmark-assets.zip: all experimental banks/manifests/
  predictions/metrics. Intermediate feature caches/maps stay on this workstation.
- development-support/git/DefectRAG-accuracy.bundle: code-only Git recovery.
Private database backup: development-support/saved-runtime/
desktop-before-highres.sqlite3 (integrity OK; 9 inspections / 10 messages).
Excluded from all releases. Original 66 model/evaluation files hash-identical.

Exact next steps on resume:
1. Inspect Git status and accuracy receipts; preserve any newer user edits.
2. In the user's existing PowerShell server window, Ctrl+C and use README.md's
   exact existing-computer command on port 8767. The already-running old process
   keeps its imported code until restarted. No fitting/build/install is needed.
3. Read docs/ACCURACY_AND_METRICS.md and ACCURACY_RESULTS.md before reporting
   performance. New experiments must have new versioned outputs and frozen
   settings, with a genuinely held-out evaluation if making generalization claims.
4. Supabase remains unprovisioned. User must create their own free project;
   deployment/SUPABASE_SETUP.md contains setup and hosted validation steps.
   No public deployment exists. Static hosting serves saved examples; live AI
   needs the local/running backend. Preserve optional cloud config and secrets.

Running state: benchmark session 55802 and acceptance session 91404 completed.
Owned port 8782 preview was stopped after browser checks. User's port 8767 /
PID 10108 and shared Ollama were left alone. Earlier preview ports 8766 / 8771
may remain; these are servers, not training jobs. No fitting job remains.
Docker execution, a fresh dependency installation, 390px mobile visuals and
hosted Supabase auth/RLS/storage remain unverified. Final archive/sync results
are authoritative in receipts, not inferred from the historical text below.

---

# DefectRAG development checkpoint — upgrade, 16 October 2026

This section supersedes the historical checkpoints below. Preserve original
assets and earlier archives. Visible branding is DefectRAG; directory stays
DefectRAG-v2 for compatibility. No Supabase project/account was provisioned.

Completed in this upgrade:
- Official VisA split experiment across all 12 categories, seeds 42/43/44,
  all 8,659 train normals and 2,162 test images; all masks evaluation-only.
  results/official_evaluation.json contains means/SD, per-seed and pixel metrics.
  Retrospective test exposure is disclosed. Macro image AUROC 0.854 / AU-PR 0.865;
  macaroni2 remains weak (~0.483). This is frozen DINOv3 patch memory, not fine-tuning.
- Every category has a verified completion receipt, three benchmark banks and
  a separate normal-only calibration bank in experiments/official_visa_v1.
  Completed experiments are skipped; do not repeat them. Current app banks and
  original evaluations are unchanged (66 files hash-checked).
- Saved-inspection measurement answers now state verdict/score/threshold directly.
  Five real HTTP assistant cases passed, including two real Qwen explanations
  and one follow-up. Root causes abstain; negative questions avoid ambiguous yes.
- New logo/favicon, larger fonts, stronger colors, transitions/reduced-motion,
  image comparison, zoom, expanded viewer, training/benchmark pages.
- Local Clear history archives; Recovery restores records/images/conversation.
  Browser verified archive/restore of two isolated Pipe fryum test records.
- Optional Supabase allowlisted staff login/sharing/notes/private images/archive/
  developer restore prepared. No hosted sign-in, RLS or storage test is possible
  until the user creates a Supabase project. Setup screen clearly shows this.
- Import configuration, environment checker and editor/training/evidence/cloud
  guides added. Current verified environment sees all eight required imports.
- Both builds and five frontend checks passed; static snapshot has 25 measured
  examples across 12 categories and refreshed recorded assistant answers.
- Vite 6.4.4 installed; dependency installation audit reported zero vulnerabilities.

Release artifacts (unique names; earlier ZIPs preserved):
- DefectRAG-local-upgrade.zip: source + current application models/builds/guides.
- DefectRAG-static-upgrade.zip: static public dashboard, no live AI.
- DefectRAG-official-benchmark-assets.zip: all experimental banks/manifests/
  calibration/predictions/metrics, hash/CRC verified. Extract into project root
  only when absent; never overwrite newer experiments. No source dataset images.
- development-support/git/DefectRAG-upgrade.bundle: code-only Git recovery.
Packaging/sync completion is recorded in sibling *.receipt.json and
  development-support/release_sync_receipt.json. Inspect those before repeating.

Preservation:
Original VisA dataset and DefectRAG-Verified are read-only and unchanged.
Desktop runtime is preserved, never replaced with preview data. Private backup:
  development-support/saved-runtime/desktop-before-upgrade.sqlite3
(integrity OK; 9 inspections / 10 messages at backup; excluded from release).
Preview runtime/ux-review is isolated. Models/experiments remain outside Git;
ZIPs preserve them. Git history is fast-forwarded, never reset or rewritten.

Resume/use exact next steps:
1. Inspect Git status, this file and release receipts; preserve newer edits.
2. Restart the user's existing server in its own terminal with Ctrl+C, then use
   the exact README command for port 8767 and the verified interpreter/overlay.
   No fitting, dependency installation or frontend rebuild is needed.
3. User must create a free Supabase project in their own account. Follow
   deployment/SUPABASE_SETUP.md and supabase.sql. Configure only public URL/key,
   invite staff, then verify anonymous/non-staff denial, staff share/read/notes,
   developer restore and expiring private images. Do not claim cloud connected.
4. For public saved-example hosting follow deployment/RUN_AND_DEPLOY.md.
   No public deployment exists; static hosting does not run Python/Ollama.
5. Optional future experiments require a new versioned output and frozen settings;
   do not replace production banks based on already-seen test metrics.

Verification details: docs/UPGRADE_VERIFICATION.md. Docker runtime, clean venv
installation and 390px mobile visuals remain unverified; VSCode Problems UI not
inspected. No training job remains. The owned port 8780 preview is stopped during
final teardown; existing user port 8767/PID10108 and shared Ollama are left alone.
Earlier port 8766 / static 8771 previews may remain; they are not model training.

All 40 Python tests passed (one third-party deprecation warning). Archive/Git/sync status is in the receipts and
results/software-tests-upgrade.xml. Do not call setup-ready Supabase fully tested.

---

# DefectRAG v2 — development checkpoint

## Active upgrade — official protocol, assistant quality, UI and staff sharing

User authorized the official VisA-split experiment, inspection-grounded conversational answers, DefectRAG branding/logo, larger type, richer colors/interactions, recoverable history and free Supabase staff sharing. No Supabase project has been created; user confirmed they do not have a known project. Setup/schema/client are being implemented, but hosted auth/RLS/storage checks remain blocked on project creation/public config. Do not claim cloud is active.

Official benchmark is isolated in experiments/official_visa_v1; exec session 27077. It uses all official training normals and all official test images, three fixed seeds, no test-based thresholds. A fourth normal-calibrated operational bank is saved separately and does not replace current app banks. Completed per-category receipts skip repeated work. Original baselines/models/history remain preserved.

Assistant now directly answers saved measurement questions with an explicit measurement-only mode; Qwen remains responsible for cited document explanations. Archive/restore preserves records, images/conversations and writes audit events. New regression suite: 36 tests passed, results/software-tests-upgrade.xml. Live cloud verification pending a project. UI build passed; isolated UX preview is being started on localhost:8780 (runtime/ux-review), leaving the user's Desktop server on 8767 alone. Vite patched to 6.4.4; npm install audit reports zero known vulnerabilities.

Current remaining work: finish and audit official results; finish UI/browser QA and response quality capture; inspect editor import visibility; document/install Supabase setup; refresh static snapshot and final unique release ZIPs; commit/checkpoint and synchronize Desktop without stopping the user's server. Resume this active work before the older checkpoint steps below. Save and pause if remaining usage approaches 3-5% as previously requested.


## Latest checkpoint: all 12 evaluated; paused near 5% usage

All nine missing categories completed fitting/calibration/final evaluation. All 12 cards, banks, split manifests and prediction files are saved. Original three-category models and predictions remain hash-identical (`results/all12_preservation.json`). No training or evaluation process remains active.

Completed integration: backend category allowlist and safe sample routing for all 12 (including pipe_fryum); dashboard labels and category count; weak-separation warning when image AUROC < 0.6; incremental --resume fitting safeguards. `results/all_categories_acceptance.json` records 18 real API inspections for the new nine categories, saved separately under runtime/verification12. Scores matched evaluation; heatmaps and reports passed. All 29 software tests passed in results/software-tests-all12.xml.

Both dashboard builds and 3 static contract tests passed. Static snapshot now contains 25 measured examples across 12 products. Snapshot hash/privacy/report-resource checks passed. Earlier three-category browser checks are preserved in results/static_verification_three_categories.json; browser QA for the expanded build has NOT been performed.

Important measured limitations: macaroni2 image AUROC is 0.46825 (weak; do not claim reliable detection). Macaroni1/2 localization is extremely weak; capsule/PCB2 localization is also weak. See docs/ALL12_EVALUATION.md for all 12 measured rows. No final-test tuning or extra experiments were performed. Existing clean serving profile covers only the original three categories.

The new artifact is DefectRAG-v2-all12-checkpoint.zip, a recoverable development checkpoint, NOT the final accepted all12 release. Earlier released ZIPs remain three-category versions and are preserved. Recovery bundle: development-support/git/DefectRAG-v2-all12-checkpoint.bundle. Archive and sync JSON receipts record hashes/commit and whether Desktop copy finished.

Exact resume steps:
1. Read this file, Git status and results/evaluation.json (must contain 12 categories). Do NOT refit or reevaluate completed categories.
2. Verify the expanded dashboard in the browser: 12 category options, 24 local samples, 25 static examples, pipe_fryum routing, all 12 performance rows, macaroni2 warning and static report/CSV links. Existing local preview on 8766 still has the OLD Python process/category allowlist; restart only that identified v2 preview before testing the new backend. Static preview on 8771 serves the rebuilt files; reload it.
3. Refresh README, deployment guide, static Space metadata and older three-category wording to the final scope. Keep old verification results clearly historical. Update final screenshot/browser receipt. Do not repeat model experiments.
4. Create unique final all12 static/full ZIP names; the old ZIP names must not be overwritten. Commit final documentation, create a new recovery bundle, then sync Desktop with scripts.sync_release --archive NEW_FULL.zip --bundle NEW.bundle --extra-archive NEW_STATIC.zip.
5. Preserve original dataset, runtime history and all models/results. The exporter uses runtime/verification12 (new nine examples) plus original runtime (earlier seven examples); both remain saved. No dependency installation is needed: use original verified Python + workspace sibling .test-deps overlay.

Processes at pause: training session 77130 and API/tests session 38315 completed successfully. Build/test session 1643 completed. No fitting/training/test job remains running. Static preview localhost:8771, v2 preview localhost:8766 and shared Ollama localhost:11434 may remain active; no training state depends on them. A new verification database is under runtime/verification12; never replace user history with it.

User requested saving around 3-5% remaining; account reported 5% at this checkpoint. Stop after checkpoint/archive synchronization and wait for a credit reset or further instruction.

## Earlier milestone — free static showcase (16 October 2026)

User requested a free static public version while preserving the full local app.
Implemented a separate read-only build using **seven allowlisted, real saved VisA
inspections**: the original six acceptance images plus the latest verified RAG
follow-up inspection. Model weights, datasets and evaluation experiments were
not changed or repeated. Obsolete LLM conversations with an old knowledge
fingerprint are excluded from the public snapshot. No private uploads are exported.

- Local production build passed after UI integration; live functionality remains
  in the ordinary build. Static build uses no backend or inference service.
- Three Node tests passed: static data loading/cache, rejected upload/chat/alert
  writes, real score/cited conversation/report URL preservation.
- `results/static_verification.json`: all seven scores match saved receipts,
  snapshot hashes pass, report images exist, no local paths/secrets/model files.
- Browser QA passed: seven records, image toggle, combined PCB1+Anomalous filter
  gives two records, final recorded Qwen explanation/follow-up, report images
  and source text, batch/alerts/performance/About pages. No captured console errors.
- Vercel static configuration, Render Static Site configuration and Hugging Face
  Static Space metadata are provided. No account/public deployment was created.
- Instructions: `deployment/RUN_AND_DEPLOY.md`. Dashboard proof:
  `docs/screenshots/static-showcase.jpg`.

New release names: **DefectRAG-v2-static.zip** (public files only) and
**DefectRAG-v2-with-static.zip** (full local app + static build/source).
Adjacent JSON receipts record archive size/hash and verification. Earlier
`DefectRAG-v2.zip` and its recovery bundle stay preserved.
The new code-only recovery bundle is
`development-support/git/DefectRAG-v2-static-release.bundle`.

Resume only if a new receipt is absent: inspect Git status; preserve newer edits;
run `python -m scripts.package_showcase` if its archive is missing, then
`python -m scripts.package_release --name DefectRAG-v2-with-static.zip` if missing.
After committing code and creating the new bundle, synchronize using:
`python -m scripts.sync_release --archive DefectRAG-v2-with-static.zip
--bundle DefectRAG-v2-static-release.bundle --extra-archive DefectRAG-v2-static.zip`.
Never overwrite an existing differing ZIP or restart completed model experiments.

Latest remaining scope: public account deployment is user-run using the documented
commands. The static site deliberately has no live image upload or chat. Full
browser inference/RAG conversion remains a separate future project. Existing
Docker/mobile/fresh-environment verification caveats below still apply.

Processes: a static preview was started on localhost:8771 (plain Python file
server; safe to stop/restart, no training state). The original local preview may
remain on localhost:8766 and shared Ollama on localhost:11434. No training,
benchmark or dependency-installation job was started in this milestone.
Usage checks reported 26%, 21%, then 15% five-hour allowance remaining. If usage reaches
3–5%, stop new work after updating this file and a recoverable Git checkpoint.

---

Updated **16 October 2026**, Asia/Kuala_Lumpur. User-authorized continuation completed
the remaining implementation and local verification. No fitting, dataset download
or expensive experiment was repeated.

## Deliverables and authoritative completion records

- Source and assets: `C:\Users\User\Desktop\DefectRAG-v2`.
- Final release: `C:\Users\User\Desktop\DefectRAG-v2.zip`.
- ZIP verification/checksum: adjacent `DefectRAG-v2.receipt.json`.
- Desktop synchronization/recovery: `development-support/release_sync_receipt.json`.
- Current Git commit: `git log -1`; release manifest also records the commit.
- Primary working source remains
  `C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\DefectRAG-v2`.

The build/synchronization receipts are authoritative for final handoff. If a
disconnect occurs during the final archive/copy step and a receipt is missing,
resume that step below; do not repeat completed fitting or verification.

## Completed

- Actual DINOv3 ViT-S/16 nearest-normal inference for PCB1, capsules and cashew;
  calibrated score, Good/Anomalous/Uncertain result and coarse heatmap.
- FastAPI, React + Vite, SQLite history, batch inspection/filtering, local review
  alerts, printable reports and CSV export.
- LangChain source loading, chunking, local BGE retrieval and persistent index;
  LangGraph scope/retrieval/evidence/generation/validation/fallback workflow.
- Genuine local Qwen explanations and follow-ups. The model selects a source
  sentence by ID and writes its explanation; the application attaches the original
  quote and source ID, then validates citation/number consistency. No generated
  explanation is represented as a deterministic template.
- Fixed wrong-method evidence: current-detector questions exclude Dinomaly
  reconstruction passages. Follow-up retrieval uses the prior user topic, and
  stale assistant facts are excluded after knowledge changes.
- Completed README, architecture diagram, portfolio description, licenses/notices,
  frontend production build, verification report and desktop screenshots.
- ZIP packager verifies CRC, all file hashes, duplicate entries and required assets.
  Dataset, secrets, runtime history/uploads, dependency overlays, node_modules,
  caches and Git objects are excluded from the release.

## Verified results

**29 software tests passed**, no failures, one upstream AnyIO deprecation warning:
`results/software-tests.xml`.

**Extracted release candidate passed on Python 3.11.15**:
`results/release_extraction_verification.json`. Imports were confirmed to come
from a new extraction. It served the frontend, uploaded a real VisA image, loaded
the bundled model, produced a real score/heatmap, saved/retrieved the record, used
bundled knowledge/embeddings with a genuine Qwen answer, and served report/CSV.
The final archive has the same runtime/frontend/model assets, plus final reports
and release utilities.

Other authoritative results:
- `results/acceptance.json`: six original predictions, source retrieval, genuine
  generation, follow-up persistence, batch filtering, reports, alerts and failures.
- `results/evidence_scope_verification.json`: real current-method explanation and
  genuine follow-up after the final source-sentence contract.
- `results/browser_verification.json`: two real uploaded images completed,
  Good/Anomalous displays, combined history filters, alert acknowledgement, report
  images and cited answer rendered; no captured browser JavaScript errors.
- `results/startup_verification.json`: actual Windows launcher/model verification
  on Python 3.11.15 with torch 2.5.1+cu121 and transformers 4.57.6.
- `results/serving_profile.json`: one clean bounded GPU profile and CPU smoke.
- `results/preservation_verification.json`: 15 frozen model/evaluation artifacts
  match the pause-checkpoint hashes, including all weights, banks and final results.

## Frozen performance and scope

| Product | Final images | AUROC | AP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| PCB1 | 180 | 0.896625 | 0.866319 | 0.779070 | 0.837500 | 0.807229 |
| Capsules | 140 | 0.825000 | 0.888730 | 0.838235 | 0.712500 | 0.770270 |
| Cashew | 130 | 0.970500 | 0.983017 | 1.000000 | 0.700000 | 0.823529 |

64 normal fit images/category; 32 distinct normal + 20 reassigned official test
anomalies calibrate max-F1 thresholds; remaining official test identities are
held out. This is a modified VisA protocol, not the full official benchmark.
±5% review band is heuristic, not calibrated confidence. Capsule localization
remains weak (pixel AP ~0.045). No named defects, counts, root causes, factory
tolerances or product-safety/acceptance guarantees are inferred.

Clean RTX 4060 model medians: **54.59 / 53.875 / 65.615 ms**; total
file/decode/inference/overlay medians about **173 / 159 / 230 ms**. PyTorch allocated
GPU peaks about **66 / 78 / 90 MB**, excluding driver, other processes and LLM.
CPU inference passed. Earlier frozen evaluation/timing records remain preserved.
The shipped method is frozen DINOv3 patch memory, **not Dinomaly**.

## Explicit remaining verification limitations

- Docker compose configuration passed; container execution unverified because the
  Docker daemon was unavailable.
- Responsive CSS is implemented, but mobile visual QA is unverified: the browser
  ignored the requested 390 px override and stayed at 1280 px, including in a new
  tab. The override was reset after testing.
- Python 3.11 verification reused the existing Conda runtime plus an isolated
  compatibility overlay. A clean dependency installation in a new venv was not run.
- Anomalib decoder training, browser ONNX/WebGPU export, Supabase, n8n and public
  deployment remain optional/future work; none was executed or provisioned.
- Quote/ID validation establishes traceability, not guaranteed semantic entailment.

These limitations are documented in the README and verification report. Do not
restart successful experiments to remove a documentation caveat.

## Start / continue without rebuilding

For ordinary standalone use, read README and run `Start-DefectRAG.cmd -Setup`
once in a compatible Python environment, then `Start-DefectRAG.cmd`.
The dashboard build, weights and knowledge index are already bundled.
Qwen is optional and separately installed through Ollama; no automatic LLM download.

Existing verified development runtime (unchanged):
`C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe`,
with `PYTHONPATH` set to the workspace sibling `.test-deps`.
Python 3.11 runtime:
`C:\Users\User\anaconda3\envs\defectrag\python.exe`,
with `PYTHONPATH` set to sibling `.test-deps311` and `USE_TF=0`.
Do not reinstall those completed overlays or change the original environments.

A development preview may still run at `http://127.0.0.1:8766`.
Its last startup reported PID **32284**; verify identity before stopping it.
Shared Ollama is at localhost:11434, `qwen2.5:3b`.
No fitting/training/benchmark jobs remain active.

If final packaging was interrupted:
1. Inspect Git status and the existing ZIP/receipt. Preserve any newer edits.
2. If the final ZIP does not exist, run `python -m scripts.package_release`.
   It refuses to overwrite an existing archive.
3. With source committed and the release bundle present, run
   `python -m scripts.sync_release` with Desktop write permission.
   It requires a clean Desktop tree and fast-forwards Git without rewriting history.
4. Check the generated receipts. Do not repeat the completed model evaluation.

The code-only release recovery bundle is
`development-support/git/DefectRAG-v2-release.bundle`.
Prior Git commits, code bundles and timestamped checkpoint ZIPs remain preserved.
Historical progress is under `docs/PAUSE_CHECKPOINT_20261016.md` (excluded from the
clean release archive).

## Preservation

The original `DefectRAG-Verified` source, Git history and installed dependencies
were not changed. Existing VisA data at
`C:\Users\User\Downloads\VisA_20220922` was read only.
All original model banks, weights, checkpoints and evaluation records remain.
The new app's development history stays in workspace `runtime/`; earlier safe
SQLite backups remain under `development-support/saved-runtime/`.
Never replace a newer database with an older backup. No public deployment,
paid service, cloud resource or external notification was initiated.
