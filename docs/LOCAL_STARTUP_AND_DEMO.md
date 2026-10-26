# Current local operating edition — 26 October 2026

See [LOCAL_OPERATION_20261026.md](LOCAL_OPERATION_20261026.md) for the consolidated current startup and verified n8n scope. The source/output receipt audit found both local builds stale only for the current Corrective Action permission UI. They were backed up and rebuilt, preserving configuration and the existing CSS. A small local Gallery explanation/link was then added, with a focused rendering/privacy regression. Final frontend suite194PASS; the dated startup/browser verification is in results/local-completion-20261026/.

The earlier23October result below is historical. In particular, it does not mean that a separate HF deployment happened for the newer local bundle. Hosting/publication and Multimodal RAG remain deferred. Full-page reload resets an unsubmitted single-image form; saved history and batch recovery have their own persistence paths.

## Historical startup and demo correction
# Local startup, Staff interface parity and public demo

## Start locally

```powershell
Set-Location 'C:/Users/User/Desktop/DefectRAG-v2'
& '.\deployment\run_local.ps1'
```

Use `http://127.0.0.1:8765`. Stop an existing local backend with Ctrl+C first.
If a healthy synchronization server is already running, the launcher prints its
URL and returns without starting another process. If another service occupies
the port, it reports the process ID and stops startup; it never kills a process.
One terminal now serves both the React build and backend. The launcher checks
production-mode source/output receipts, backs up an older build, rebuilds only
when needed and enables the local sync flag for its process. It preserves models,
history, private account caches, public configuration, gallery and the showcase.
The older two-terminal Vite setup at5173 is still available for development.

The reported401 loop came from an old `index-CCMYEeeT.js` build sending private
requests without the required browser namespace. Retry cannot repair an old
client. An unverified/stale/showcase build now shows a rebuild instruction rather
than that broken dashboard. Current entry HTML/config use no-store headers.
After updating an already open old tab, perform Ctrl+Shift+R once to load the new
entry. Do not disable native authorization or MFA to resolve this issue.

## Staff Workspace parity

Both runtimes use the same React Staff and Account Security components. Desktop
public config lacked `registrationEnabled=true`, explaining the missing signup
form. Its existing Supabase URL/key were preserved; the local public flag was
backed up then aligned with the existing Space configuration. Required auth UI is
also enabled in the served current public config. Database flags/permissions did
not change. Both sign-in/registration and approval/TOTP rules remain native.

Sessions at8765,5173 and the HF origin are separate. Each needs its own sign-in/MFA.
Actual approved-account UI equality after sign-in still needs private credentials;
this update verifies the shared source and unsigned registration interface.

## Public recruiter/tester demo

The existing live Space already supports anonymous image inspection in an
isolated browser workspace. No Supabase Staff registration/password/TOTP is needed
for this guest flow. Enter via Image inspection or `/#inspect`, choose a supported
sample/category or upload, and run inspection. HF GPU availability/quota still
applies; an HF login may be needed for additional free quota, independently from
DefectRAG Staff access. No unlimited-availability claim is made.

A new **Try public demo** notice/button is prepared using the existing dashboard
styles on Overview/inspection/batch/Staff pages. It is visible only for a verified
guest posture, explicitly selects Personal/guest inspection routing, and does not
sign users out or convert pending/MFA/revoked sessions into anonymous access.
Unsigned local history remains device-local; cloud demo history is browser-isolated
and may reset after a Space restart. Neither is automatically published or copied
to Team. Signed-in private accounts retain their own Personal/Team workflow.

The new visible demo entry requires a separately approved HF frontend deployment.
No HF deployment was performed for this correction. Its existing anonymous
inspection and privacy path was tested live without a Staff token:

- Guest workspace/history200, authenticated=false, initially0 records.
- Attempting an existing private Personal inspection404; guest Team history403.
- One valid public Capsules request produced real ZeroGPU DINOv2 score
  0.13208819925785065, verdict Good, storage browser_session; both artifacts200.
- A different guest namespace could not retrieve that demo inspection (404).

Final Desktop browser verification passed for the new demo button, unsigned
registration/sign-in forms, sample selection and enabled inspection action.
Refreshing preserved the selected image without a red refresh warning. The local
bundle is index-D7D9gsmP.js; unchanged styles are index-Bn4HF2vD.css. A separate
review-only cloud bundle index-jMvSDx8O.js passed the standard181-test release
verification using the existing live public config; it has not been published.

Diagnostic transparency: the first report could not be written due to a missing
local output folder; it is not counted as passing. The saved follow-up rejected a
UUID-with-hyphens request ID before GPU inference and misleadingly reported an
image error. The final test used the same32-hex request ID format as React and
passed. These diagnostic failures did not alter Supabase data. A separate future
backend improvement could distinguish invalid request IDs from invalid images;
no speculative inference/backend deployment was made here.

Verification:181 frontend tests,21 focused Python tests and production builds
passed. A long test temporary directory produced a261-character Windows path;
the artifact existed via its extended path and API serving passed. Re-running the
same tests with a shorter temporary root passed; no data-path workaround or
application authorization change was needed.

No migration, staff approval/revocation, notification delivery, n8n change,
existing-history import or GitHub push was performed.
