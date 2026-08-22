# Final Pre-Demo Audit

Audit date: 22 August 2026  
Scope: supplied BAIF/HSBC communications, complete VaaniSetu repository, executable workflows, release evidence and judge-demo readiness

## Source register and interpretation

| ID | Source | Date / authority | Use in this audit |
| --- | --- | --- | --- |
| S1 | Problem-statement clarification from Anshul Sharma | 26 May 2026 | Core problem, users, production/minimalist goal and must-have product features |
| S2 | Design-phase Q&A and drop-in summary | 26 June 2026 | Evaluation pillars, no-GPU/open-source constraints, office/field workflow, testing and DLP guidance |
| S3 | Technical & Delivery Clarifications | Supplied 16 July 2026 | Formal target hardware/software, mandatory media boundaries, reuse, sample confidentiality and post-selection handover |
| S4 | Implementation Phase Results + deliverables | 14 July 2026 communication | Production-ready web application, BAIF deployability and complete handover/training pack |
| S5 | Implementation-phase review email | 4 August 2026 | Operative judging weights and later timeline |
| S6 | Sample-video language-direction clarification | August 2026, supplied 22 August | Marathi samples must translate to Hindi/English; all six directions among English/Hindi/Marathi remain primary |

Interpretations that must remain explicit:

- S1 calls a fully offline model non-negotiable, while S2/S3 allow internet at the BAIF office for installation and translation. These are compatible when provisioning may use internet but normal processing remains capable of using locally cached models, and exported field outputs require neither the worker nor internet. Office internet is permission, not a required runtime dependency.
- S2 says smaller models can be feasible at approximately 8 GB with accuracy trade-offs. S3 is later and expressly defines 16 GB as the target minimum. Therefore 8 GB is an engineering/test possibility, not a production acceptance baseline.
- S1 permitted prioritising three or four document formats for an MVP, while S3 says its listed file specifications “must be supported.” VaaniSetu treats PDF, DOCX, PPTX, XLSX and CSV as mandatory; TSV is an additional supported format.
- S2's tentative 17 August final was superseded by S5's later tentative 25–27 August finals. No supplied source gives a newer implementation submission format beyond the design deck; this remains a human confirmation item.

## Requirements and compliance matrix

Status vocabulary is restricted to **PASS**, **PARTIAL**, **FAIL**, **NOT APPLICABLE**, and **NEEDS HUMAN CONFIRMATION**.

| Requirement | Source | Mandatory / Optional | Current implementation | Evidence | Status | Gap / risk | Required action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Improve BAIF eLearning accessibility for staff, farmers and other learners | S1 | Mandatory | Office-to-field multilingual content workflow | `README.md`; browser product copy; offline package | PASS | Impact still depends on adoption and reviewer quality | Demonstrate the complete office-to-field journey |
| English, Hindi and Marathi as initial languages | S1, S6 | Mandatory | Three configured languages | `config/languages.py`; `/languages` | PASS | None | Retain |
| Any supported source language to either other supported language (six directions) | S6 | Mandatory | Direction-aware local translation | `core/translator.py`; six-direction benchmark seed | PASS | Linguistic adequacy lacks BAIF reviewer sign-off | Complete bilingual review |
| Lightweight, minimalist, production-deployable web solution | S1, S4 | Mandatory | FastAPI worker with static browser UI and one model worker | `app.py`, `api.py`, `frontend/`, `core/job_manager.py` | PARTIAL | Formal production deployment remains unproven on target Windows machine | Complete Windows acceptance; describe current state as release candidate |
| Fully offline-capable model/runtime | S1 | Mandatory | Runtime downloads and hosted translation disabled by default; local model routes | `config/settings.py`; `core/translator.py`; startup scripts | PARTIAL | Intended MIT IndicTrans2 checkpoints are not yet accepted/cached; current engineering fallback is NLLB | Cache/inventory IndicTrans2; rerun offline test |
| Office internet may be used for installation/translation | S2, S3 | Permitted | Controlled setup downloads dependencies/models | `scripts/one_click_setup.py`, `scripts/setup_models.py`, `scripts/setup_ocr.py` | PASS | Setup time can be long and gated-model access is manual | Measure clean Windows setup and retain offline installer evidence if practical |
| Translation happens at BAIF Pune office, not live in the field | S2 | Mandatory deployment constraint | Managed local/on-prem worker; browser clients; field uses exports | `ARCHITECTURE.md`; `SETUP.md` | PASS | LAN security is BAIF IT responsibility | Demo local-only mode; require IT approval for LAN mode |
| Field outputs usable without internet/server | S2 | Mandatory | Server-free ZIP with `CONTENTS.html`, direct links and media playback | `core/export_utils.py`; `scripts/verify_package.py` | PASS | Package must be extracted and kept together | Show verified package with worker disconnected |
| CPU-only, no GPU, low-spec optimisation | S2, S3 | Mandatory | INT8 CTranslate2 routes, one worker, bounded queue, balanced ASR | `config/settings.py`; `core/job_manager.py`; BAIF benchmark in `TESTING.md` | PASS | Target Windows performance still external | Run measured Windows BAIF video test |
| Target CPU: i5 11th Gen+/equivalent or Ryzen 5, 6+ cores | S3 | Mandatory baseline | Preflight records CPU and recommends profile | `scripts/operations.py`; `COMPATIBILITY.md` | PARTIAL | Current evidence is an 8-core Mac, not target Windows CPU | Execute Windows preflight/UAT |
| Target RAM: minimum 16 GB | S3 | Mandatory baseline | Preflight blocks machines below 16 GB for production | `scripts/operations.py`; memory regression test | PASS | Must still be observed on target worker | Capture machine evidence |
| Target storage: 512 GB/1 TB; sufficient working free space | S3 | Mandatory baseline | 20 GB free-space preflight and per-job low-disk guard | `scripts/operations.py`; `core/file_utils.py` | PARTIAL | App checks free space, not physical drive capacity | Human records installed drive capacity during acceptance |
| Windows 11 | S3 | Mandatory baseline | PowerShell setup/start/acceptance scripts | `scripts/setup_baif_worker.ps1`; `scripts/windows_acceptance.ps1` | PARTIAL | Not executed on the target machine in this audit environment | Complete teammate Windows run |
| Microsoft Office 2020+ target environment | S3 | Mandatory environment fact | Reads Office Open XML without automating Office | `core/document_processor.py`; `COMPATIBILITY.md` | PASS | Exact Office visual layout is not preserved | State best-effort exports clearly |
| Audio up to 30 minutes | S3 | Mandatory | Probed duration enforced | `core/media_utils.py`; `core/pipeline.py`; boundary test | PASS | Unsupported/corrupt codecs depend on FFmpeg/PyAV diagnostics | Retain graceful error tests |
| Compressed audio MP3/OGG up to 50 MB | S3 | Mandatory | Type-specific 50 MB cap | `core/file_utils.py`; `/limits` | PASS | Additional formats are supported but not organiser-mandated | Retain |
| Uncompressed WAV up to 150 MB | S3 | Mandatory | Type-specific 150 MB cap | `core/file_utils.py`; `/limits` | PASS | None | Retain |
| Video MP4/MKV, 720p/1080p, up to 15 minutes and 200 MB | S3 | Mandatory | Extension, size, duration, stream and max-resolution validation | `core/file_utils.py`; `core/pipeline.py`; BAIF inventory | PASS | Lower-than-720p files are accepted as useful compatibility, not rejected | Explain that 720p/1080p is supported, not the minimum accepted resolution |
| Extract video audio and create subtitles and/or voiceover | S3 | Optional choice within video requirement | WAV extraction, ASR, translation, SRT/VTT, optional TTS/caption/dub | `core/pipeline.py`; `core/video_processor.py` | PASS | Voice quality/backends vary; optional media may warn and leave core outputs | Demo subtitles as core; treat voice/dub as optional |
| Store prior translations for reference and reuse | S3 | Mandatory | Durable library, manifests, review versions and exact approved memory | `api.py`; `core/review_store.py`; `outputs/` runtime storage | PASS | Retention/backup ownership must be assigned | Record BAIF owners and policy |
| Respect BAIF sample confidentiality and approvals | S3 | Mandatory | BAIF media/models/runtime outputs ignored; privacy-safe metadata only | `.gitignore`; `scripts/release_check.py`; `scripts/validate_baif_samples.py` | PASS | Private reviewer worksheets must remain outside public evidence | Re-run secret/content policy before submission |
| Transfer complete source code to BAIF IT | S3 | Post-selection mandatory | Source repository and submission builder | repository; `scripts/build_submission_bundle.py` | PASS | Final release tag and transfer channel not yet recorded | Tag accepted release and record transfer |
| Handover documentation and BAIF IT training/KT | S3, S4, S5 | Mandatory | Role-based setup, usage, operations, acceptance and onboarding runbook | `SETUP.md`, `OPERATIONS.md`, `HANDOVER.md`, `BAIF_ONBOARDING_RUNBOOK.html` | PASS | Live KT session is necessarily external | Schedule, conduct and record KT |
| Short-text translation with queue and graceful degradation | S1 | Mandatory | Async text queue, actionable local-model errors and approved-memory reuse | `/jobs/text`; `core/job_manager.py`; `core/user_messages.py` | PASS | No hosted fallback in production by design | Retain |
| PDF, DOCX, PPTX, XLSX and CSV translation | S1, S3 | Mandatory | Extraction and reviewable translated exports for every format | `core/document_processor.py`; document tests | PASS | Same-format output is content-oriented best effort, not exact layout recreation | Keep limitation visible in UI/docs |
| OCR for scanned PDFs or documented fallback | S1 | Mandatory | Local PDFium rendering plus Tesseract OCR | `core/document_processor.py`; OCR health/test | PASS | OCR quality varies with scan quality | Demo a controlled scan or state limitation |
| Auto source-language detection and selected target | S1 | Mandatory | Text/document auto-detect; explicit media language for ASR quality | `core/text_utils.py`; UI; API validation | PASS | Detection is script/heuristic based and cannot distinguish Hindi/Marathi Devanagari reliably without lexical cues | Keep explicit choice for audio/video; expose detected source |
| Async file processing with visible status and completion | S1 | Mandatory | Durable queue, persisted state, progress polling and result state | `core/job_manager.py`; `frontend/app.js` | PASS | Browser notifications are in-page, not OS push notifications | Demo visible progress/completion |
| Download same format or clearly stated best-effort format preservation | S1 | Mandatory | Reviewable exports plus original-purpose text/table outputs and ZIP | `core/document_processor.py`; `README.md` limitation | PASS | DOCX/PPTX visual fidelity is not preserved | Never claim exact formatting preservation |
| Admin-approved access and Admin/Authorised User roles | S1 | Mandatory | First-admin bootstrap, pending registration, approval/deactivation, CSRF sessions | `core/auth.py`; `api.py`; auth tests | PASS | HTTP without TLS is local-machine only; LAN needs reverse proxy/TLS | Keep demo bound to localhost |
| Open-source only; no licences/software purchases for BAIF | S2 | Mandatory / eligibility | Open-source software/model plan and manifest | `LICENSING.md`; `config/model_manifest.json` | PARTIAL | Active NLLB fallback is CC-BY-NC-4.0; model and dependency licences need final inventory/notice verification | Use MIT IndicTrans2 production route; generate SBOM/notices; human licence confirmation |
| Impact | S2 | Judging pillar | Reusable outputs, approval/reuse and privacy-safe impact metrics | `/impact`; UI impact panel | PASS | Metrics are local operational evidence, not measured field outcomes | Do not claim field impact before deployment |
| Scalability and production readiness | S2 | Judging pillar | Single-worker bounded deployment, queue, recovery, backup/restore, cleanup and diagnostics | operations and failure drills | PARTIAL | Horizontal scalability and target Windows proof are not demonstrated | Position as predictable vertical office worker; complete target acceptance |
| Usability and user experience | S2, S5 | Judging pillar, 30% | Guided three-step UI, onboarding, review, downloads, responsive styling | `frontend/`; browser evidence | PASS | Must be rechecked live after final changes | Run browser/mobile/keyboard smoke test |
| Tech safety, fairness and inclusivity | S2 | Judging pillar | Human approval, script/invariant/glossary checks, privacy controls, accessibility basics | `core/quality.py`; review flow; UI | PARTIAL | No formal WCAG audit; machine quality varies by dialect/noise/gender | Run accessibility checks and bilingual review; state limitations |
| Solution efficiency/coverage/accuracy | S5 | Judging criterion, 30% | Six directions, formats, media pipeline and measured CPU timings | `TESTING.md`; benchmark scripts | PARTIAL | NLLB scores are engineering-only; IndicTrans2 and human accuracy evidence missing | Cache intended model and obtain reviewer evidence |
| Clear time-boxed walkthrough with fallback | S5 | Judging criterion, 30% | 3.5-minute demo plus prepared package/walkthrough path | `DEMO.md`; onboarding runbook | PASS | Backup assets must exist on the actual demo laptop | Smoke-test every referenced asset before the room |
| Documented critical/edge test evidence | S5 | Judging criterion, 10% | Automated/adversarial suite, failure drill, BAIF inventory and reports | `tests/`; `TESTING.md` | PASS | Evidence counts and stale commit references must be kept current | Re-run and refresh final report |
| Repeatable deployment, prerequisites, rollback and logging | S5 | Judging criterion, 20% | One-click/PowerShell setup, preflight, logs, backup/restore and support bundle | `SETUP.md`; `OPERATIONS.md`; scripts | PARTIAL | Clean Windows execution, setup time and rollback rehearsal remain external | Run and record Windows acceptance |
| Complete handover/adoption plan enabling operation without team | S5 | Judging criterion, 10% | Role-based guides, ownership model, training journeys and acceptance record | `HANDOVER.md`; onboarding runbook | PASS | Owners/session evidence not yet filled | Assign owners and conduct recorded exercises |
| Design deliverable: concise 4–5 slides covering problem, architecture, stack and pillars | S2 | Mandatory design-phase deliverable | Five-slide PPTX | `submission/VaaniSetu_Final_Hackathon_Deck.pptx`; five-slide render; template-fidelity report | PASS | Final presentation delivery mechanism remains administrative | Keep the audited deck unchanged except for evidence updates |
| Work on personal laptops; avoid HSBC-to-personal content transfer | S2 | Mandatory DLP guidance | Repo excludes private data and uses BAIF-approved samples already supplied separately | release policy; privacy docs | PASS | Team handling outside repository cannot be proven automatically | Team confirms no HSBC-restricted content was transferred |
| Public agriculture/crop videos up to 15 minutes allowed for testing | S2 | Optional testing guidance | Licensed public agriculture fixture plus real BAIF samples | `TESTING.md`; demo evidence | PASS | YouTube content would require licence verification; current canonical fixture is Wikimedia CC BY | Retain attributed fixture |
| Implementation submission deadline and exact final submission contents | S5 | Mandatory administrative item | Repository has deck and submission builder | `submission/`; `scripts/build_submission_bundle.py` | NEEDS HUMAN CONFIRMATION | Supplied material says further submission details will follow; no final portal/checklist is present | Confirm portal, deadline timezone, file/link limits and required artefacts with organiser |
| Team eligibility, team-size rules and prizes/recognition | Supplied material | Administrative | No conclusive rule supplied | None | NEEDS HUMAN CONFIRMATION | Cannot infer eligibility or prize rules | Obtain official confirmation if still relevant |

## A. Executive summary

The core VaaniSetu demo path is working and materially hardened: authenticated local processing, six translation directions, OCR/document extraction, long-running media progress, durable jobs, human approval, exact approved-memory reuse and integrity-checked offline packages are implemented and exercised. The final browser journey is clean, the automated suite passes, the real-model smoke test passes without runtime downloads or hosted translation, and the five-slide deck is visually and structurally verified.

This audit does **not** convert external acceptance work into an internal pass. VaaniSetu is a verified release candidate and a strong controlled demo, but unrestricted production acceptance still depends on the intended MIT IndicTrans2 models, Hindi/Marathi human sign-off and a clean Windows 11/16 GB acceptance run. The exact organiser submission mechanism also remains absent from the supplied material.

## B. Compliance matrix

The canonical matrix is above. Every meaningful supplied requirement is represented, including later amendments and the explicit source conflicts. No silent interpretation was used.

## C. Final P0/P1/P2/P3 findings

### P0 — External demo/eligibility gates still open

| Finding | Evidence | Resolution status |
| --- | --- | --- |
| MIT IndicTrans2 checkpoints are not accepted/cached; NLLB is only a CC-BY-NC engineering fallback | `/health`; model inventory; `LICENSING.md` | **OPEN — human/model-account action** |
| Hindi and Marathi linguistic approval is absent; English→Hindi seed terminology remains weak | six-direction report and reviewer worksheet | **OPEN — human review** |
| Clean target Windows 11/16 GB installation and BAIF-media acceptance are not available in this macOS audit environment | `ACCEPTANCE.md`; no signed Windows evidence | **OPEN — external machine test** |
| Exact final portal, deadline timezone and submission contents were not supplied | S5 explicitly says further details will follow | **OPEN — organiser/team confirmation** |

### P1 — Internal must-fix findings

All reasonably addressable internal P1 items are resolved:

- Fixed the vulnerable `pypdf` 6.14.2 pin by moving to 6.15.0 and rerunning selectable/scanned/corrupt PDF tests.
- Changed the default judge path to English→Hindi with speech off; subtitles remain on. This removes unnecessary TTS latency without hiding the optional feature.
- Corrected Docker from the 32 GB quality profile to BAIF's 16 GB balanced profile.
- Changed direct/local shell startup from `0.0.0.0` to `127.0.0.1`; explicit LAN/Docker deployment still supports a deliberate host override.
- Removed the inapplicable Vercel serverless config, which conflicted with local models, durable storage and on-prem operation.
- Added a quick/full pre-demo smoke gate and made the release check validate local documentation links.
- Upgraded the local packaging toolchain within PyTorch's compatibility boundary and documented the remaining model-toolchain advisory exposure.
- Removed stale deck evidence, repaired obsolete speaker-note sources and fixed a visible slide-4 text overflow; theme fidelity and slide overflow checks pass.
- Corrected stale `SETUP.md` wording so the balanced large-v3-turbo path and visible ETA are described accurately.

### P2 — Strong polish completed

- Current requirements matrix, audit trail, runbook, smoke test, judge Q&A and scoring are consolidated here.
- Demo assets, package integrity, browser console, UI defaults and documentation links were rechecked.

### P3 — Post-hackathon

- Multi-worker/horizontal scale after capacity measurement.
- Same-layout DOCX/PPTX/PDF reconstruction instead of reviewable content exports.
- More languages, dialect-specific evaluation and a larger reviewer-approved BAIF corpus.
- Formal WCAG audit, threat model and long-duration soak testing on the production worker.

## D. Changes made

| Problem | Root cause | Fix | Verification |
| --- | --- | --- | --- |
| Crafted PDFs could consume excessive memory/time | Vulnerable pypdf pin | `pypdf==6.15.0` | 77 tests; PDF/OCR/adversarial tests pass; advisory no longer appears in audit |
| Fast demo unexpectedly generated speech | TTS checkbox was selected by default behind collapsed options | Default TTS off; English→Hindi selected | Live DOM/browser verification; full smoke package contains text/subtitles without TTS |
| Docker exceeded target baseline | Quality profile was hardcoded | Balanced profile and full requirements | Config review; dependency integrity |
| Local shell startup exposed port 8501 to the LAN | `0.0.0.0` hardcoded | Localhost default plus explicit `BAIF_HOST` override | Source check; localhost live server/browser test |
| Serverless config contradicted architecture | Residual Vercel file used ephemeral storage and no local models | Removed `vercel.json` | Release policy and repository review |
| Broken documentation links could recur | Release gate checked existence of guides, not their targets | Added local Markdown/HTML link validation | Release policy passes 90 repository paths |
| Setup toolchain was stale; unconstrained upgrade broke Torch | venv bootstrap packages were old and Torch requires setuptools `<82` | Upgrade pip/wheel and newest compatible setuptools line | `pip check` passes; audit records only acknowledged residuals |
| Deck cited deleted files and stale test count; one callout overflowed | Documentation renames and evidence drift | Current notes, durable test wording, shorter controls copy | All slides rendered; no canvas overflow; template fidelity passes; theme hash preserved |
| Long-video guidance named the obsolete ASR profile | Docs lagged the balanced-profile fix | Documented multilingual large-v3-turbo, elapsed time and ETA | Documentation-link/release checks pass |

Files changed are visible in the final Git diff; no BAIF media, transcripts, credentials, model weights or generated runtime evidence is added to Git.

## E. Tests performed

| Test | Result |
| --- | --- |
| Python compilation and frontend `node --check` | PASS |
| Full unit/adversarial suite | PASS — 77/77; 20 adversarial cases |
| `pip check` after dependency changes | PASS |
| Dependency vulnerability audit | pypdf fixed; constrained Torch/Transformers/setuptools residuals documented below |
| Release policy, secret/generated-data policy and documentation-link audit | PASS — 90 repository paths |
| Six failure drills | PASS |
| Quick pre-demo smoke test | PASS |
| Full real-model English→Hindi smoke and offline ZIP verification | PASS — NLLB CTranslate2 INT8, no runtime downloads/hosted API |
| Six-direction translation engineering gate | PASS — 12/12, all required directions, no critical preservation/script/backend failure |
| Browser login/workspace/result journey | PASS — no console or page errors; generated package verified |
| Final UI defaults | PASS — English→Hindi, TTS off, subtitles on |
| Offline ZIP integrity and server-free contents page | PASS |
| BAIF sample inventory | PASS — 8/8 technical limits/streams |
| Real BAIF shortest-video pipeline | PASS on engineering Mac; exact final timing recorded in `TESTING.md` |
| Submission deck render/overflow/theme/template fidelity | PASS — five slides, theme hash preserved |
| Submission evidence/bundle builder | PASS; rebuilt after final verification |

## F. Remaining risks

- The installed fallback translation model is non-commercially licensed and is not the final unrestricted production route.
- Machine translation scores are not human accuracy evidence. English→Hindi terminology in the small seed is the weakest direction.
- The actual target Windows worker may differ in CPU, codec support, antivirus overhead, path policy and installation permissions.
- Optional natural TTS and video dubbing add latency and backend-specific failure modes; text/subtitles are the dependable demo baseline.
- Transformers/PyTorch advisories concern untrusted model/checkpoint or training/JIT paths. VaaniSetu uses fixed, locally provisioned model directories and does not accept user-supplied models, but the versions should be upgraded after compatibility testing.
- Cancellation is cooperative at stage boundaries; a native inference call is not forcibly terminated mid-call.
- Document exports preserve usable content, not exact Office/PDF layout.

## G. Human checks required

1. Accept the official AI4Bharat terms using the team-owned model account; cache only the approved repositories; run `python scripts/operations.py model-inventory` and archive the evidence.
2. Have named Hindi and Marathi reviewers grade transcripts/translations using the generated worksheet. Record severity, correction and approval; do not edit model predictions to manufacture a score.
3. On the target Windows 11 machine, follow `SETUP.md` from zero, run `scripts\windows_acceptance.ps1`, process BAIF `401.1.mp4`, restart/retry, verify the offline ZIP, and record wall time/peak RAM/backend/job ID.
4. Confirm the final submission portal, deadline/timezone, repository visibility, file limits and required deck/video/source links with the organiser.
5. Confirm team eligibility/DLP handling and that no HSBC-restricted material entered personal storage.
6. Assign BAIF administrator, IT owner, retention owner and Hindi/Marathi reviewers; conduct and record the KT exercises in `HANDOVER.md`.

## H. Demo runbook

The canonical timed script is `DEMO.md`. Safest sequence:

1. Run `python scripts/demo_smoke_test.py --full`; stop if any check is false.
2. Start one worker on `127.0.0.1:8501`; open Chrome/Edge with only the deck and VaaniSetu tabs.
3. Sign in with a pre-approved disposable demo account. Confirm **System: Ready to translate** and that the backend is named honestly.
4. Paste `samples/demo_agriculture.txt`; keep English→Hindi, subtitles on and speech off. Point out validation, elapsed time, backend provenance and preserved numbers/units.
5. Correct one phrase if useful and select **Approve final**. Explain that humans remain authoritative.
6. Run the exact same source again and show exact approved-memory reuse.
7. Download the ZIP, run `python scripts/verify_package.py PACKAGE.zip`, disconnect from the worker if practical, extract it and open `CONTENTS.html`.
8. Close with slides 4–5 and name the three external gates without apology or overclaiming.

Backup path: use the prepared verified package and `outputs/VaaniSetu_Backup_Walkthrough.mp4`; never switch to a cloud translator. If the backend fails, restart the one worker, recheck `/health`, use **Run again**, and continue from the prepared package. Before a repeated demo, delete only the disposable demo job through the UI; do not manually clear auth/review storage.

## I. Pre-demo checklist

- [ ] Correct Git commit/tag recorded; working tree contains no private/runtime data.
- [ ] `python scripts/demo_smoke_test.py --full` is green.
- [ ] `/health` is reachable; local translation, FFmpeg, ffprobe and OCR are ready.
- [ ] Hosted translation and runtime model downloads are off.
- [ ] One worker only; at least 20 GB free disk; laptop on power; sleep disabled.
- [ ] Demo account approved and sign-in tested.
- [ ] English→Hindi, speech off, subtitles on.
- [ ] Sample text, audited deck, verified ZIP and backup walkthrough open locally.
- [ ] Browser console has no errors; downloads work; `CONTENTS.html` opens offline.
- [ ] Presenter knows the three external gates and does not claim perfect accuracy, exact formatting or instant long-video processing.

## J. Likely judge questions and defensible answers

1. **What problem does VaaniSetu solve?** It turns BAIF office learning content into reviewed Hindi/Marathi/English text, subtitles, speech/video options and reusable offline field packages.
2. **Why not use a public translator?** BAIF needs controlled content handling, reusable artefacts, human approval and offline field delivery; normal VaaniSetu jobs stay on the configured worker.
3. **Is it fully offline?** Provisioning can use internet. After models are cached, normal processing can run locally; exported field packages require neither VaaniSetu nor internet.
4. **Which directions work?** All six directions among English, Hindi and Marathi are implemented and pass the engineering gate; human linguistic approval is still required.
5. **Which model is used today?** The engineering machine uses local NLLB-200 CTranslate2 INT8. The intended unrestricted production path is official MIT-licensed IndicTrans2 after account approval, caching and review.
6. **Why mention that limitation?** Model provenance and licence are part of trustworthy deployment; hiding the fallback would be a compliance and credibility risk.
7. **Does it need a GPU?** No. The balanced path is CPU-only, INT8 where applicable, and intentionally limited to one heavy worker.
8. **What machine should BAIF use?** Windows 11, 16 GB RAM minimum, six or more recent CPU cores, 512 GB/1 TB storage and at least 20 GB free working space; the balanced profile is the default.
9. **Why can video take minutes?** ASR and translation run locally on CPU. The UI reports stage, elapsed time and ETA; a real 5:43 BAIF sample completed end to end on the engineering Mac.
10. **What happens if processing fails?** The job becomes an explicit failed/retryable state with an actionable message; stack traces are not shown to users and completed history remains durable.
11. **What if the backend restarts?** Interrupted jobs are marked recoverable failures on startup; completed jobs and approved reviews remain.
12. **Can users cancel?** Yes, cancellation is durable and wins completion races, though an active native inference call stops at a safe processing boundary.
13. **How are translation mistakes handled?** Output is visibly a draft; reviewers correct and approve it. The approved version is auditable and can be reused only for an exact source/language match.
14. **Could fuzzy memory return the wrong sentence?** No. Automated reuse is exact-match only; machine guesses are never inserted as approved memory.
15. **How do you protect numbers and units?** The quality layer protects/restores numbers, units, URLs and email addresses and reports preservation/script/terminology findings for review.
16. **What documents are supported?** PDF, DOCX, PPTX, XLSX and CSV, plus TXT/TSV. Scanned PDFs use local OCR. Output preserves usable content, not exact visual layout.
17. **What does a field user receive?** An integrity-checked ZIP with translated text, SRT/VTT, optional media, a manifest and server-free `CONTENTS.html`.
18. **How do you know the ZIP was not altered?** Every member is size/hash listed; the verifier rejects mismatches, unexpected files, duplicate names and unsafe paths.
19. **How is access controlled?** The first administrator approves authorised users; sessions use CSRF protection, throttling and active-user checks. Localhost is the safe default; LAN exposure requires BAIF controls.
20. **Does VaaniSetu send telemetry or load CDN assets?** No runtime analytics, hosted fonts, CDN scripts or required external APIs were found. Hosted translation and runtime downloads are disabled by default.
21. **How does it scale?** One worker deliberately bounds memory on BAIF's baseline. More trainers share the durable queue; more workers are a measured infrastructure decision after capacity testing.
22. **How do you support BAIF after handover?** Setup, operations, backup/restore, support bundle, acceptance personas and role ownership are documented; KT is complete only when BAIF performs them independently.
23. **What is your strongest differentiator?** Translation is treated as a governed content workflow—validation, provenance, human approval, exact reuse and portable verified outputs—not a one-off model call.
24. **What is still unfinished?** IndicTrans2 provisioning/licence evidence, Hindi/Marathi sign-off, target Windows acceptance and final administrative submission confirmation.
25. **Would you deploy it today?** I would run the controlled demo and Windows acceptance today. I would not sign unrestricted production acceptance until the four external gates above are evidenced.

## Judge-perspective scorecard

| Dimension | Score / 10 | What prevents 9+ and realistic action |
| --- | ---: | --- |
| Problem relevance | 9.5 | Direct fit to BAIF's office-to-field multilingual learning problem |
| Usefulness to BAIF | 9.0 | Complete reusable workflow; field adoption evidence comes after deployment |
| Technical depth | 8.5 | Strong pipeline/governance; intended production translation model is not provisioned |
| AI usage | 8.0 | Appropriate ASR/MT/TTS/OCR use; bilingual validation and final model evidence remain |
| Innovation | 8.5 | Differentiated by approval, exact memory and portable integrity packages rather than a novel base model |
| Implementation completeness | 8.0 | Core flows complete; external production gates and exact layout exports remain |
| Reliability | 8.5 | Strong tests/recovery/real media; target Windows and longer soak evidence remain |
| Local/offline practicality | 8.0 | Runtime and field outputs are local; provisioning and final MIT model cache remain |
| Usability | 9.0 | Guided browser path, actionable states and clean judge flow |
| Scalability | 7.5 | Predictable single-worker queue, but no demonstrated horizontal scale |
| Maintainability | 8.5 | Clear modules/runbooks/tests; large model toolchain still carries compatibility debt |
| Presentation potential | 9.0 | Audited five-slide story plus live and offline fallback paths |
| Credibility | 9.0 | Evidence and limitations are explicit; no perfect-accuracy or instant-processing claims |
| Differentiation | 8.5 | Governance/reuse/field package are strong; competitors can imitate the workflow |
| Shortlist/deploy impression | 8.5 | Strong shortlist candidate; production sign-off depends on external gates |

## K. Final verdict

**READY WITH BLOCKERS**

VaaniSetu is ready for a controlled, high-quality demo on the verified engineering environment. It is not yet entitled to an unrestricted production-ready claim because the four P0 external gates remain open. When IndicTrans2 is provisioned/licence-confirmed, Hindi/Marathi outputs are approved, Windows acceptance passes and the organiser submission details are confirmed, the verdict can move to **DEMO READY — HIGH CONFIDENCE** without architectural rework.
