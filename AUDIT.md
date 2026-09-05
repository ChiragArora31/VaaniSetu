# Final Pre-Demo Audit

Audit date: 1 September 2026
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
| S7 | Final implementation-review rubric | Late August 2026, supplied 1 September | Operative six-part judging split, including a new 10% USP comparison and reduced 10% deployment weight |
| S8 | 9 September review invite and vanilla Windows 11 laptop FAQ | Supplied 1 September 2026 | Final run-of-show, setup window, controlled event-device/network/data/software/USB rules, teardown and team-owned troubleshooting |

Interpretations that must remain explicit:

- S1 calls a fully offline model non-negotiable, while S2/S3 allow internet at the BAIF office for installation and translation. These are compatible when provisioning may use internet but normal processing remains capable of using locally cached models, and exported field outputs require neither the worker nor internet. Office internet is permission, not a required runtime dependency.
- S2 says smaller models can be feasible at approximately 8 GB with accuracy trade-offs. S3 is later and expressly defines 16 GB as the target minimum. Therefore 8 GB is an engineering/test possibility, not a production acceptance baseline.
- S1 permitted prioritising three or four document formats for an MVP, while S3 says its listed file specifications “must be supported.” VaaniSetu treats PDF, DOCX, PPTX, XLSX and CSV as mandatory; TSV is an additional supported format.
- S2's tentative 17 August final was superseded by S5's later tentative 25–27 August finals. No supplied source gives a newer implementation submission format beyond the design deck; this remains a human confirmation item.
- S7 supersedes S5 only for the judging allocation: Deployment changes from 20% to 10%, while a dedicated USP comparison with Bhashini/similar solutions receives 10%. The other weights remain unchanged.
- S8's temporary vanilla Windows 11 laptop rules govern the event device, not BAIF's eventual production worker. They require organiser approval for demo software, Guest Wi-Fi/mobile-hotspot networking, approved demo data only and complete teardown. The supplied instruction to bring a screen-share-ready team laptop is treated as a fallback, not silent permission to ignore the provided demo laptop.

## Requirements and compliance matrix

Status vocabulary is restricted to **PASS**, **PARTIAL**, **FAIL**, **NOT APPLICABLE**, and **NEEDS HUMAN CONFIRMATION**.

| Requirement | Source | Mandatory / Optional | Current implementation | Evidence | Status | Gap / risk | Required action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Improve BAIF eLearning accessibility for staff, farmers and other learners | S1 | Mandatory | Office-to-field multilingual content workflow | `README.md`; browser product copy; offline package | PASS | Impact still depends on adoption and reviewer quality | Demonstrate the complete office-to-field journey |
| English, Hindi and Marathi as initial languages | S1, S6 | Mandatory | Three configured languages | `config/languages.py`; `/languages` | PASS | None | Retain |
| Any supported source language to either other supported language (six directions) | S6 | Mandatory | Direction-aware local translation | `core/translator.py`; six-direction benchmark seed | PASS | Linguistic adequacy lacks BAIF reviewer sign-off | Complete bilingual review |
| Lightweight, minimalist, production-deployable web solution | S1, S4 | Mandatory | FastAPI worker with static browser UI and one model worker | `app.py`, `api.py`, `frontend/`, `core/job_manager.py` | PARTIAL | Formal production deployment remains unproven on target Windows machine | Complete Windows acceptance; describe current state as release candidate |
| Fully offline-capable model/runtime | S1 | Mandatory | Runtime downloads disabled; hosted translation implementation removed; local model routes | `config/settings.py`; `core/translator.py`; startup scripts | PARTIAL | Intended MIT IndicTrans2 checkpoints are not yet accepted/cached; current engineering fallback is NLLB | Cache/inventory IndicTrans2; rerun offline test |
| Office internet may be used for installation/translation | S2, S3 | Permitted | Controlled setup downloads dependencies/models | `scripts/one_click_setup.py`, `scripts/setup_models.py`, `scripts/setup_ocr.py` | PASS | Setup time can be long and gated-model access is manual | Measure clean Windows setup and retain offline installer evidence if practical |
| Translation happens at BAIF Pune office, not live in the field | S2 | Mandatory deployment constraint | Managed local/on-prem worker; browser clients; field uses exports | `ARCHITECTURE.md`; `SETUP.md` | PASS | LAN security is BAIF IT responsibility | Demo local-only mode; require IT approval for LAN mode |
| Field outputs usable without internet/server | S2 | Mandatory | Server-free ZIP with `CONTENTS.html`, direct links and media playback | `core/export_utils.py`; `scripts/verify_package.py` | PASS | Package must be extracted and kept together | Show verified package with worker disconnected |
| CPU-only, no GPU, low-spec optimisation | S2, S3 | Mandatory | INT8 CTranslate2 routes, one worker, bounded queue, balanced ASR | `config/settings.py`; `core/job_manager.py`; BAIF benchmark in `TESTING.md` | PASS | Target Windows performance still external | Run measured Windows BAIF video test |
| Target CPU: i5 11th Gen+/equivalent or Ryzen 5, 6+ cores | S3 | Mandatory baseline | Preflight records CPU and recommends profile | `scripts/operations.py`; `COMPATIBILITY.md` | PARTIAL | Current evidence is an 8-core Mac, not target Windows CPU | Execute Windows preflight/UAT |
| Target RAM: minimum 16 GB | S3 | Mandatory baseline | Preflight blocks machines below 16 GB for production | `scripts/operations.py`; memory regression test | PASS | Must still be observed on target worker | Capture machine evidence |
| Target storage: 512 GB/1 TB; sufficient working free space | S3 | Mandatory baseline | 20 GB free-space preflight and per-job low-disk guard | `scripts/operations.py`; `core/file_utils.py` | PARTIAL | App checks free space, not physical drive capacity | Human records installed drive capacity during acceptance |
| Windows 11 | S3 | Mandatory baseline | PowerShell setup/start/acceptance scripts; early MSVC compiler preflight for IndicTransToolkit | `scripts/setup_baif_worker.ps1`; `scripts/windows_acceptance.ps1`; `SETUP.md` | PARTIAL | Clean setup reached dependency installation and exposed the now-documented C++ workload; full acceptance has not completed | Install Desktop development with C++, then complete Windows acceptance |
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
| Clear time-boxed walkthrough with fallback | S5 | Judging criterion, 30% | 30-minute core-first run-of-show with live, prepared-evidence and recovery paths | `DEMO.md`; onboarding runbook | PASS | Backup assets must exist on the actual demo laptop | Smoke-test every referenced asset before the room |
| Documented critical/edge test evidence | S5 | Judging criterion, 10% | Automated/adversarial suite, failure drill, BAIF inventory and reports | `tests/`; `TESTING.md` | PASS | Evidence counts and stale commit references must be kept current | Re-run and refresh final report |
| Repeatable deployment, prerequisites, rollback and logging | S7 | Judging criterion, 10% | One-click/PowerShell setup, preflight, logs, backup/restore and support bundle | `SETUP.md`; `OPERATIONS.md`; scripts | PARTIAL | Clean Windows execution, setup time and rollback rehearsal remain external | Run and record Windows acceptance |
| Complete handover/adoption plan enabling operation without team | S5 | Judging criterion, 10% | Role-based guides, ownership model, training journeys and acceptance record | `HANDOVER.md`; onboarding runbook | PASS | Owners/session evidence not yet filled | Assign owners and conduct recorded exercises |
| USP versus Bhashini or similar solutions | S7 | Judging criterion, 10% | VaaniSetu implements a governed BAIF content-production layer: local execution, validation, human approval, exact reuse, durable library and verified offline field packages | `README.md`; `core/review_store.py`; `core/export_utils.py`; `DEMO.md` | PARTIAL | No like-for-like Bhashini quality/latency benchmark or production trial exists; claiming model superiority would be misleading | Present an evidence-backed best-fit comparison and explicit trade-offs; do not invent uplift |
| 30-minute final review: 2-minute problem, 18-minute core-first demo, 5-minute Q&A, 5-minute buffer | S8 | Recommended event run-of-show | Exact allocation, core-first live path, prepared evidence and recovery buffer documented | `DEMO.md` | PASS | Team rehearsal remains human work | Rehearse once on each presentation path |
| Use organiser-provided vanilla Windows 11 demo laptop; bring screen-share-ready laptop and power adapter | S8 | Mandatory event logistics | Windows setup/start/acceptance scripts exist; engineering laptop is a tested fallback | `SETUP.md`; PowerShell scripts | PARTIAL | Provided device has not completed setup/acceptance; exact hardware and permissions are unknown | Use setup window; prepare verified fallback laptop/package; record go/no-go before the room |
| Install only organiser-approved demo software | S8 | Mandatory event-device control | Required components are documented and setup preflights the compiler | `SETUP.md`; `scripts/setup_baif_worker.ps1` | NEEDS HUMAN CONFIRMATION | Python, C++ Build Tools, FFmpeg, Tesseract and model provisioning require organiser approval | Send the exact prerequisite list for written approval before 9 September; do not install unapproved software |
| Event network limited to HSBC Guest or presenter's hotspot; no corporate Wi-Fi/LAN | S8 | Mandatory event-device control | Localhost mode needs no network after provisioning; fallback packages work offline | `scripts/start_baif_worker.ps1`; `core/export_utils.py` | PASS | Setup downloads still need an allowed connection | Provision only via approved Guest/hotspot; keep the live demo local to `127.0.0.1` |
| Event device may use only demo/public/synthetic/approved Hackathon data and demo-required websites | S8 | Mandatory data/use control | Synthetic fixtures and approved BAIF media are separated from Git; no hosted runtime calls by default | `samples/`; `.gitignore`; `PRIVACY.md`; release policy | PASS | BAIF sample approval must remain explicit; unrelated browsing cannot be proven by code | Use synthetic/public live input unless organiser explicitly approves a BAIF clip for the room |
| USB only when necessary; no unattended device; copy only required demo files | S8 | Mandatory removable-media control | Submission builder produces a bounded candidate ZIP; transfer and removal rules are explicit | `scripts/build_submission_bundle.py`; `DEMO.md` | PASS | Physical compliance remains the presenter's responsibility | Verify the minimal bundle and remove USB immediately |
| Temporary storage only; sign out, remove files/USB, disconnect and return event laptop | S8 | Mandatory teardown control | Dedicated event teardown covers accounts, repository, models, outputs, caches, USB and network | `DEMO.md`; `PRIVACY.md`; `/auth/logout` | PASS | Physical completion cannot be automated | Assign one teammate to execute and witness teardown |
| Team is responsible for demo technical troubleshooting | S8 | Mandatory responsibility | Smoke test, failure drills, fallback ZIP/walkthrough and recovery guidance exist | `scripts/demo_smoke_test.py`; `scripts/failure_drill.py`; `DEMO.md` | PASS | Backup assets must be verified on both presentation paths | Assign presenter/operator roles and rehearse failure switching |
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
| Organiser approval for Python, C++ Build Tools, FFmpeg, Git, Tesseract and local models on the shared demo laptop is not evidenced | S8; `SETUP.md`; `scripts/setup_baif_worker.ps1` | **OPEN — organiser approval** |
| Exact final portal, deadline timezone and submission contents were not supplied | S5 explicitly says further details will follow | **OPEN — organiser/team confirmation** |

### P1 — Internal must-fix findings

All reasonably addressable internal P1 items are resolved:

- Forced Windows Whisper execution to CPU INT8 after real Windows testing exposed CUDA auto-detection without the required `cublas64_12.dll`; the default, launcher and acceptance gate now agree with BAIF's no-GPU constraint.
- Removed the hosted MyMemory code and configuration surface; changing an environment variable can no longer send a translation to that service.
- Fixed an internal invariant-marker leak found in the final browser run. Phone numbers are protected as one value and mutation-tolerant restoration preserves `1800-123-456` exactly.
- Changed shared-Windows setup to stop for approval instead of silently installing FFmpeg, Git or Tesseract; an administrator must explicitly request the approved installation switch.
- Rebuilt the runbook around the 9 September 30-minute review, organiser-laptop rules, two presentation paths and full teardown.
- Replaced the stale final slide with an evidence-safe Bhashini comparison; all five slides render and the overflow test is clean.
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
| Windows video transcription failed on missing `cublas64_12.dll` | faster-whisper device `auto` selected CUDA when a driver was visible, despite BAIF's CPU-only target | Default and Windows scripts force Whisper `cpu` with `int8`; setup documents verification and rejects random-DLL/CUDA workarounds | Configuration regression checks, transcriber tests and release policy pass |
| Phone number became `ZXQQ0003QXZ ... 456` in a real Hindi result | The model duplicated a marker letter and the number pattern split a telephone number into groups | Protect structured phone numbers as one invariant and accept bounded marker-letter duplication during restoration | New regression test; repeated live browser result preserves `1800-123-456`; no marker leak |
| A hidden cloud route could be enabled by configuration | Legacy MyMemory implementation remained behind an off-by-default flag | Removed provider, endpoint, credentials and runtime fallback; release policy prevents reintroduction | 79 tests; source/network search; full local smoke |
| Event setup could silently install unapproved software | General worker setup assumed an administrator-owned BAIF machine | Default to a clear stop; require explicit `-InstallApprovedSystemTools` after organiser approval | PowerShell/source review; setup and event docs agree |
| Demo script and deck did not reflect the final rubric/schedule | Late-August communications arrived after the previous audit | 30-minute core-first runbook, event compliance/teardown, Bhashini best-fit slide and source notes | Five-slide render/visual review; no overflow; local links pass |
| Crafted PDFs could consume excessive memory/time | Vulnerable pypdf pin | `pypdf==6.15.0` | 79 tests; PDF/OCR/adversarial tests pass; advisory no longer appears in audit |
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
| Full unit/adversarial suite | PASS — 79/79; 20 adversarial cases |
| `pip check` after dependency changes | PASS |
| Dependency vulnerability audit | 8 known advisories in 3 model-toolchain/build packages; no pypdf advisory; constrained residuals documented below |
| Release policy, secret/generated-data policy and documentation-link audit | PASS — 90 repository paths |
| Six failure drills | PASS |
| Quick pre-demo smoke test | PASS |
| Full real-model English→Hindi smoke and offline ZIP verification | PASS — NLLB CTranslate2 INT8, no runtime downloads/hosted API |
| Six-direction translation engineering gate | PASS — 12/12, all required directions, no critical preservation/script/backend failure |
| Browser login/workspace/result journey | PASS — local English→Hindi in 5.7 seconds; phone number preserved; approval and exact-memory reuse at 0.0 seconds |
| Final UI defaults | PASS — English→Hindi, TTS off, subtitles on |
| Offline ZIP integrity and server-free contents page | PASS |
| BAIF sample inventory | PASS — 8/8 technical limits/streams |
| Real BAIF shortest-video pipeline | PASS — 5:43 Marathi→Hindi completed in 227.22 seconds on the 8 GB engineering Mac; 33 segments; verified ZIP; no warnings |
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

The canonical timed script is `DEMO.md`. Use 2 minutes for the problem, 18 minutes for the core-first demonstration/evidence, 5 minutes for Q&A and retain 5 minutes as recovery buffer. Safest sequence:

1. Obtain organiser approval for the exact software list; use only Guest Wi-Fi/hotspot and synthetic/public/approved data.
2. Run `python scripts/demo_smoke_test.py --full`; stop if any check is false.
3. Start one worker on `127.0.0.1:8501`; open Edge/Chrome with only the deck and VaaniSetu tabs.
4. Sign in with a disposable approved account and confirm **Ready to translate**.
5. Translate the short English agriculture sample to Hindi with speech off. Point out provenance, terminology prompts, elapsed time and exact number/unit preservation.
6. Review and approve the visible result; rerun the exact source to show approved local reuse.
7. Download/open the offline package and checksums. Use prepared public-video and privacy-safe BAIF evidence rather than live-processing a long CPU video.
8. Close on the best-fit Bhashini comparison and honest external acceptance gates.

Backup path: switch to the verified team laptop, prepared package and `outputs/VaaniSetu_Backup_Walkthrough.mp4`; never switch to a cloud translator. After the demo, sign out, transfer only approved evidence, delete repository/models/outputs/caches/temp files from the shared laptop, remove USB, disconnect and return the device.

## I. Pre-demo checklist

- [ ] Correct Git commit/tag recorded; working tree contains no private/runtime data.
- [ ] Organiser software approval recorded; only Guest Wi-Fi/hotspot planned.
- [ ] `python scripts/demo_smoke_test.py --full` is green.
- [ ] `/health` is reachable; local translation, FFmpeg, ffprobe and OCR are ready.
- [ ] Hosted translation route is absent; runtime model downloads are off.
- [ ] One worker only; at least 20 GB free disk; laptop on power; sleep disabled.
- [ ] Demo account approved and sign-in tested.
- [ ] English→Hindi, speech off, subtitles on.
- [ ] Sample text, audited deck, verified ZIP and backup walkthrough open locally.
- [ ] Verified team laptop, power adapter and minimal USB transfer bundle are ready.
- [ ] Browser console has no errors; downloads work; `CONTENTS.html` opens offline.
- [ ] Presenter knows the external gates and does not claim perfect accuracy, Bhashini superiority, exact formatting or instant long-video processing.
- [ ] One teammate owns the shared-device sign-out, file cleanup, USB removal and return checklist.

## J. Likely judge questions and defensible answers

1. **What problem does VaaniSetu solve?** It turns BAIF office learning content into reviewed Hindi/Marathi/English text, subtitles, speech/video options and reusable offline field packages.
2. **Why not use only a public translator?** BAIF needs controlled content handling, reusable artefacts, human approval and offline field delivery; VaaniSetu supplies that operating workflow around a locally provisioned model.
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
20. **Does VaaniSetu send telemetry or load CDN assets?** No runtime analytics, hosted fonts, CDN scripts or required external APIs were found. The hosted translation route was removed and runtime model downloads are disabled.
21. **How does it scale?** One worker deliberately bounds memory on BAIF's baseline. More trainers share the durable queue; more workers are a measured infrastructure decision after capacity testing.
22. **How do you support BAIF after handover?** Setup, operations, backup/restore, support bundle, acceptance personas and role ownership are documented; KT is complete only when BAIF performs them independently.
23. **What is your strongest differentiator?** Translation is treated as a governed content workflow—validation, provenance, human approval, exact reuse and portable verified outputs—not a one-off model call.
24. **What is still unfinished?** IndicTrans2 provisioning/licence evidence, Hindi/Marathi sign-off, target Windows acceptance and final administrative submission confirmation.
25. **Would you deploy it today?** I would run the controlled demo and Windows acceptance today. I would not sign unrestricted production acceptance until the external gates above are evidenced.
26. **How is this different from Bhashini?** Bhashini is a broad Indian-language model/API ecosystem. VaaniSetu does not claim a better foundation model without a controlled benchmark; it differentiates through BAIF-specific local validation, human approval, exact reuse, durable recovery and verified offline field packages. Bhashini is stronger for platform breadth; VaaniSetu is built for controlled office-to-field content operations.

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

VaaniSetu is ready for a controlled, high-quality demo on the verified engineering environment. It is not yet entitled to an unrestricted production-ready claim because five external gates remain open: authorised IndicTrans2 provisioning/licence confirmation, Hindi/Marathi reviewer approval, clean Windows 11 acceptance, organiser approval for shared-laptop software, and final submission administration. Closing those gates can move the verdict to **DEMO READY — HIGH CONFIDENCE** without architectural rework.
