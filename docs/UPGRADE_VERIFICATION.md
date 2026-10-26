# Upgrade verification — 16 October 2026

Story: select a product, inspect an image, save the measured result, discuss that
inspection, compare heatmaps, review history and recover archived records.
Separately, publish saved examples and optionally share records through Supabase.

| Boundary | Evidence | Result |
|---|---|---|
| Python API and persistence | results/software-tests-upgrade.xml | 40 tests passed; covers uploads, failures, filters, citations, factual answers, archive/restore and protocol math |
| Real local Qwen | results/assistant_quality_verification.json | Five developer acceptance cases passed; two real generated explanations with checked source quotes |
| Original assets | results/upgrade_preservation.json | 66 model/evaluation files hash-identical to all12 checkpoint |
| User history | Private SQLite backup under development-support/saved-runtime | Integrity OK; excluded from release |
| Frontend | npm test | Five contract/config tests passed |
| Production/static builds | Vite 6.4.4 | Both built successfully; runtime config.js deliberately remains an external script |
| Static artifact closure | results/static_verification.json | 25 measured examples; hashes, report images, privacy and score provenance passed |
| Browser | Local preview 8780 and static 8771 | Archive two Pipe fryum records and restore both; 12-category benchmark; comparison slider 50→51; zoom 100→125%; expanded dialog; factual and generated answers rendered |
| Branding | Browser | DefectRAG name, own SVG logo/favicon, larger fonts, colored navigation, transitions; reduced-motion CSS |
| Supabase absent configuration | Browser and Node test | Setup screen; no requests without public configuration |
| Editor dependencies | scripts.check_environment in verified interpreter + overlay | All eight queried modules visible; VS Code Problems panel not inspected |

The assistant acceptance cases are not a general RAG accuracy benchmark. The
review database includes historical diagnostic answers as well as corrected
answers; only the passed capture is included in the refreshed featured showcase.
No public visitor uploads or private user records are exported.

Official-split experiment: 12 products, all official training normals and test
images, three fixed bank seeds, threshold-free metrics, reference sampled pixel
integration at 224×224. Completed receipts and bank hashes were verified without
repeating model runs. All four banks/category are preserved separately. Existing
application banks use the earlier compact modified split and are unchanged.

Cloud project/account creation, hosted sign-in, RLS permissions, signed storage
URLs and cross-browser staff sharing are NOT verified because no Supabase project
exists. Supplied SQL is setup-ready and must pass the documented anonymous,
non-staff, staff and developer checks before use. Static hosting is not inference.

Docker execution, clean new-venv installation and 390px mobile visual QA remain
unverified. A previous viewport override was ignored; the current browser check
was at 714px width. No paid services, cloud resources or public deployment were
created. The user's existing port8767 server was left alone.

Visual inspiration: https://averroes.ai/ . Layout, logo and implementation are
project-created; no commercial performance claims are reused.
