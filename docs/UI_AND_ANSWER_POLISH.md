# Question-focused answers, branding and public source preparation

18 October 2026. Updated public Space revision:
b715fbf7b7d6237e9677550bda8dce02ce54ccb4, runtime RUNNING.

- Removed unconditional verdict/score prefix from heatmap/documentation answers.
  Explicit result summaries retain measured facts; score-meaning answers directly
  explain distance versus accuracy. The existing measurements panel/metadata remain.
- Added question-focused generation instructions while retaining scope, exact-quote,
  source-ID and invented-number checks. Existing stored conversations are unchanged.
- Replaced QC initials with an accessible quality-control scan icon; new SVG mark
  represents product inspection and a magnified defect. Existing layout/CSS/colors
  remain; CSS SHA256 unchanged.
- About explicitly names retrieval-augmented generation and its actual flow;
  runtime includes RAG, wording removes portfolio and clarifies SOP scope. Overall
  evaluation heading uses objective language. Recall interpretation added without
  changing any model, threshold, data split or saved evaluation result.
- README now contains an original SVG hero, actual version badges, Mermaid
  architecture, dashboard preview, honest ranking/operating metrics and source setup.
  The supplied RADAR URL could not be fetched; no claim of copying its contents.
- Source-only GitHub exporter excludes model/data/private state/environments/Git
  history and replaces personal public config with a blank template. Known HF,
  service-key and JWT-like patterns are checked. Manual publication remains required.
- Optional immutable public-asset downloader added for fresh source clones. Only
  --list executed; no large asset or dataset download. Launcher accepts DINOv2-only
  installations. Fresh dependency/model acquisition was not repeated or certified.

Validation:38 answer/API tests passed13.48s;6 frontend tests passed. Local and
isolated cloud production builds passed. Public About/new logo/RAG text and
objective benchmark heading verified in browser. Startup logs reported RUNNING
and0 captured response-already-started errors. Initial sandbox pytest stalled;
owned run stopped and focused checks passed outside sandbox. No new vision
inspection, fitting, benchmark or Supabase record modification was required.

No staff session was available in the new verification browser, so this update did
not claim a fresh live Qwen answer test. The question-specific assembly is covered
by regressions and the same deployed backend code; prior genuine Qwen/inspection
and staff persistence acceptance remain documented separately. No account bypass
or database changes were performed to manufacture verification.

See RECALL_AND_RESPONSE_QUALITY.md for exact confusion-matrix interpretation and
GITHUB_PUBLISHING.md for the source export/upload procedure.
