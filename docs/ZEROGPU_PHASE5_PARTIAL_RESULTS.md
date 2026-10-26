# Phase 5 partial acceptance — 18 October 2026

This is an interim checkpoint, not a completed release. Existing cloud commit
a31f52b64c91b7d6dab34113bc17a5bfac37ff72 remains hosted. Phase4 readiness changes
are saved locally for the next gated deployment. No retraining, repeated benchmark,
large release archive or database modification was performed.

| Check | Observed result |
|---|---|
| React design | Existing CSS byte-identical; layout, navigation, charts, inspection and staff workspace components retained |
| Navigation | Nine additional destinations opened locally and in cloud, expected headings and zero error alerts |
| Genuine browser inspection | Cashew4551ace05dba4237a22a1630f7b18d34, Anomalous, score0.2414531409740448, threshold0.13224798440933228, model inference743.44ms |
| Browser assistant | Heatmap question returned LIVE LLM · CITED answer, correct inspection context, screening-4 sources |
| History/recovery | Own anonymous test record archived then restored; image, heatmap and saved conversation retained |
| Report | Original image/localization, evidence conversation and retrieved documentation populated; print control present |
| CSV | Signed export downloaded; header plus the expected Cashew record |
| Private-file boundary | Generic Gradio file endpoint denied private SQLite and image requests403 |
| Two-image browser batch | One Capsules inspection succeeded, second rejected by guest ZeroGPU quota; partial results and error displayed correctly. Full batch completion unverified |
| Software checks |44 existing Phase3 regressions previously passed; latest9 security checks passed0.63s |
| Latest isolated UI build | Passed; expected config.js external-script and Gradio-client Node-module externalization warnings; original builds not overwritten |
| Staff persistence/RPC/RLS | Pending user's manual SQL execution and real staff/nonstaff account tests |

These are bounded integration observations, not availability, latency or model
accuracy guarantees. Existing all12 AUROC/evaluation files remain unchanged.
Quota depends on the caller's Hugging Face identity and free allowance. Supabase
login is a different identity and does not itself increase Hugging Face quota.
No paid usage, token-in-browser injection or repeated rejected GPU call was used.

Screenshots: zerogpu_phase5/cloud-live-rag.png and cloud-batch.png. Sanitized
navigation/security evidence and test XML are alongside them. Private reports,
workspace secrets, signed URLs and diagnostic logs stay Git-ignored under
development-support/space; do not upload that directory wholesale.

Remaining acceptance: enabled staff persistence, both RPC role matrices, durable
multi-user history/conversation/acknowledgement, archive/developer recovery under
RLS, successful authenticated batch after quota becomes available, quota/reconnect
and restart behavior. Do not restart completed all12 smoke tests or experiments.
