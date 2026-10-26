# Team review and Corrective Actions navigation repair

Date: 26 October 2026. Baseline: b1dc641, feature/auth-mfa-inactive.

## Confirmed causes

- Staff workspace's Review handler fetched details but rendered them beneath the
  account/security controls and history without scrolling or moving focus. It
  appeared unresponsive, especially with a Developer's longer account page.
- CorrectiveActions.jsx was mounted only at the bottom of Staff workspace behind
  `correctiveActionsEnabled === true`. Both existing public configurations omitted
  that flag. There was no sidebar entry or hash route. This was a UI integration
  omission, not evidence that the backend was missing or that Staff lacked SQL access.
- The main dashboard supplied its shared-inspection/assistant callback only for
  cloud_session_workspace, omitting the already supported local sync client.

## Small UI changes

- Existing Staff Review opens the selected shared inspection, announces loading,
  focuses its accessible details region and scrolls it into view. Reduced-motion
  preferences are respected. Reopening an already selected record works too.
- Team-scoped Inspection history now has an explicit Review action that carries
  the selected ID into Staff workspace. Personal-history behavior is unchanged.
- Corrective Actions is a sidebar/hash route (`/#cases`) outside static showcase
  mode, and a button in authorized Staff workspace. The existing component and
  RPCs are reused. Existing configurations enable its interface when the optional
  flag is absent; explicit `correctiveActionsEnabled: false` still disables it.
  This only controls UI availability: it grants no account/database permissions.
- The case route preserves the selected Team inspection, puts case creation/list
  before its evidence, and omits unrelated account controls after access passes.
  Unauthorized visitors still receive existing sign-in/security controls.
- Case data/forms wait for the native `defectrag_ca_staff` check. Failed access,
  account changes and failed refreshes clear case selection, directory and private
  details. Late history results cannot replace a newer account/refresh generation.
- Shared assistant navigation now also supports local_sync_enabled. Original
  authenticated image downloads, structured reviews and private evidence remain.
- No stylesheet, backend, SQL, model, RAG, runtime flag, secret or notification
  configuration was changed. Case updates still use persisted owner/supervisor/
  Developer checks in the existing RPCs and optimistic version arguments.

## Where to click

1. Hard reload http://127.0.0.1:8765/ with Ctrl+Shift+R. Sign in and complete
   existing MFA in **Staff workspace**, if necessary.
2. Open **Inspection history**, choose **Team Workspace**, then **Review** beside
   a shared record. Alternatively use **Staff workspace → Review**.
3. The shared details show saved image/heatmap, measurements, conversation and
   **Human review**. Choose a review status/decision and **Save review**.
4. For a genuinely human-confirmed defect, use **Reviewed → Reject**, save, then
   **Create / view corrective actions**. Fill description, owner, supervisor,
   priority and due date; tick the separate human-confirmation box; create.
   An AI anomaly alone, an Accept/Hold decision or an archived inspection is
   insufficient. Existing server rules remain authoritative.
5. Open **Corrective Actions** in the sidebar to see accessible cases, status,
   owner and deadlines. **Details** shows status history, linked private evidence
   and delivery metadata. The owner, supervisor or Developer can save permitted
   state/assignment/deadline updates with an audit note; other Staff are read-only.
6. **Choose a Team inspection** returns to shared history when starting a case.
   **Review linked inspection and private evidence** opens/focuses its evidence.

## Verification and limits

- Full frontend suite: **205 passed, zero failed**, including 11 focused new
  navigation/component tests. Results: results/team-navigation-20261026/.
- Focused tests execute actual mounted JSX handlers with an in-memory SDK fixture:
  shared-image/detail loading, structured review submission, selection transfer,
  explicit confirmation, create/update RPC arguments, history, owner/supervisor/
  Developer versus unassigned controls, pending/MFA/revoked/guest denial, config
  opt-out and clearing after revocation. No actual Supabase writes are performed.
- Browser verification uses actual React components/styles with synthetic data
  and no Supabase connection: Review focus/scroll, structured review, selected
  case-creation navigation, confirmation gate, and removal of protected controls
  after incomplete MFA. The browser automation could not complete the native
  date field, so case creation/update are covered by mounted-handler tests, not
  claimed as browser end-to-end creation. No real case or review was created.
- Work Vite production build and local source/artifact receipt passed. CSS remains
  index-Bn4HF2vD.css. Non-blocking existing classic config.js / mixed-import Vite
  warnings remain. Local/guest served-bundle verification and Desktop build are
  recorded separately in the completion entry in DEVELOPMENT_PROGRESS.md.
- Existing live SQL security evidence is preserved; this frontend-only task does
  not claim fresh authenticated production RLS or lifecycle testing. An approved
  account with MFA can exercise the click path above against existing records.
- No migration, production deployment, GitHub push, account approval, record reset,
  real email or n8n activation. Existing backend/SQL authorization is unchanged.
