# Guided practice: action-based onboarding

The optional tutorial now navigates real dashboard routes and renders clearly
labelled, isolated practice panels there. It does not click through real Staff
operations. `GuidedPractice.jsx` uses the same design, inspection-action button and
image viewer. It deliberately does not mount the live Team/Corrective Actions,
sharing, gallery or archive components while practice runs.

## Action sequence

1. Image inspection: choose Candle.
2. Select the supplied public sample.
3. Run inspection: open its saved historical result; no new inference.
4. Compare images and move the divider.
5. Enter a question and Ask: a labelled teaching answer, not live Qwen.
6. Select the actual Inspection history sidebar button to find the temporary
   private copy. Real signed-in Personal inspections save automatically; the lesson
   explains online save status instead of teaching an unnecessary extra save.
7. Inspection history: open that practice row.
8. Image inspection: explicitly share the practice copy with Team.
9. Staff workspace: save Reviewed / Reject with a note.
10. Corrective Actions: describe, assign, choose a future due date and confirm.
11. Record In Progress with a note.
12. Record Resolved with a note.
13. Record Closed with a note.
14. Batch inspection: enter a name, add two samples, Inspect batch.
15. Review alerts: Mark as seen; no product approval implied.
16. Community gallery: acknowledge that a public copy is visible to anyone.
17. Overview: Finish tutorial, discard practice and return to normal work.

A matching user action advances the reducer and changes the hash route. There is
no timed advance or generic Next button. Wrong/incomplete actions do not advance.
Back restores a pre-action snapshot, including editable case status and notes,
without overwriting real data. Off-route navigation offers Return to current step;
it never reveals live records or permits real forms within practice. Skip/Escape
can exit. Escape first closes an expanded image when that dialog is open.

## Data and authorization boundaries

Practice state is held separately in React memory. It never enters a normal
result, files, batch, history, cloud client, authorization state or synchronization
queue. Only a versioned dismissal flag is stored. Real workspace polling is paused
while practice is active and resumes on exit; in-flight refresh application is
invalidated. Existing normal photo/category/batch drafts are not reset. Active
inspection/assistant/loading tasks block starting practice. Existing identity
change handling still clears real private state when required.

Practice requires no account and never fabricates an approved role. Native
Supabase membership, MFA, RLS, RPCs and ownership checks remain unchanged for all
real operations. No API client or network write is available in the lesson
components/reducer. Static public image requests are allowed. No model, email,
notification, n8n or production secret is involved.

The sample measurements and original/heatmap come from bundled public showcase
record 7dbb6f27253b450698a1a503cfa9a8c8, measured 16 October 2026 with
`dinov3-normal-bank-candle-v1`. They are explicitly historical teaching data, not
current thresholds or fresh predictions. Tests compare all measurements and
paths with the bundled original. Images are VisA / Zou et al., ECCV 2022, CC BY 4.0.
The second batch sample is public Candle record 14418c36d94648adbdbc2779a6a33b3c.

## Review and release

Focused tests exercise the reducer, actual control callbacks, invalid inputs,
progression/Back/replay, standard image-viewer compatibility, provenance and
absence of request services. Full frontend regressions and separate cloud-build
verification are required. Browser checks cover the complete lesson, wrong-page
return, draft image preservation, Skip/Finish and normal workspace restoration.
No real inspection/review/case/email is needed to test onboarding. A Hugging Face
release still needs separate owner approval through the existing guarded
frontend-only publisher. No migration or configuration activation is required.

The three teaching JPEGs are imported from src/practiceAssets so Vite emits
content-hashed assets under /assets, which both installed servers serve. Byte
comparisons tie these copies to their original public showcase images. The cloud
server does not mount /showcase; direct public-directory URLs must not be used by
the lesson. Release QA must check actual original/heatmap naturalWidth > 0 in the
live browser, as successful button clicks alone do not establish loaded imagery.
