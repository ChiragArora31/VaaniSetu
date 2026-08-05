# VaaniSetu Implementation Roadmap

Last reviewed: Wednesday 5 August 2026, 21:02 IST
Submission deadline: Friday 21 August 2026
Finals: 25-27 August 2026 (tentative)

## Finish-line definition

VaaniSetu must arrive at submission as a measured BAIF deployment package, not only a feature-complete prototype. The final candidate is acceptable when:

1. a trainer can complete the realistic office-to-field journey on the intended local IndicTrans2 path;
2. Hindi and Marathi reviewers have signed representative six-direction quality evidence;
3. a clean BAIF-spec Windows 11 CPU machine has completed setup, processing, recovery and UAT;
4. every organiser criterion has a concise claim, reproducible evidence and demo moment; and
5. BAIF can install, operate, support and train users without the project team present.

Winning cannot be guaranteed. The execution standard is to remove every controllable weakness, keep claims evidence-bound and make the strongest capabilities effortless for judges to see.

## Current position

### Verified today

- `main` and `origin/main` are synchronized at `95025e6e`.
- 71/71 automated tests pass on Python 3.10, including 20 adversarial regressions, onboarding delivery and scanned-PDF OCR.
- Python compilation, frontend syntax, dependency health and repository release-policy checks pass.
- The latest GitHub Actions run for `main` is green.
- First-admin, trainer and model-unavailable paths were rechecked in a real browser on 5 August.
- The 390 x 844 layout has no horizontal overflow and keeps the primary workflow legible.
- The five-slide deck, demo runbook, fallback walkthrough, licensed public video proof and submission builder exist.

### Honest readiness estimate

These are planning estimates, not predicted judge scores.

| Measure | Position | Why it is not 100% |
| --- | ---: | --- |
| Product implementation | 93% | The committed workflow is broad and tested; remaining product work should be limited to defects found during judged-path validation. |
| New-rubric evidence readiness | 78% | Role-based onboarding is now evidenced; the strongest missing proof remains authorised IndicTrans2 quality, bilingual sign-off and measured Windows deployment. |
| Submission and demo readiness | 85% | The onboarding/demo runbook is ready, but the deck must still be realigned to the new weights and updated with final measured evidence. |
| Production acceptance | 0 of 3 external gates | Model access, bilingual review and target Windows evidence are not yet recorded. |

The July release-candidate claim remains valid. The new evaluation matrix means that evidence, deployment measurement and adoption material now require another focused pass.

## Evaluation scorecard

| Criterion | Weight | Current strengths | Gap that can lose points | Acceptance gate |
| --- | ---: | --- | --- | --- |
| Solution efficiency | 30% | End-to-end text/document/audio/video flow; six directions; exact limits; local queue; review and offline package | Current 12-sample translation report uses NLLB, not the intended IndicTrans2 path; no bilingual sign-off; limited representative corpus | IndicTrans2 inventory plus a reviewer-signed, six-direction agriculture benchmark with preservation, terminology, latency and memory evidence |
| Ease of use | 30% | Clear three-stage interface; first admin; actionable failure states; mobile layout; reusable library; 3.5-minute demo and fallback | Final deck is architecture-heavy; realistic completed result must be visible immediately; accessibility and novice UAT need final records | Three novice personas complete the journey without developer intervention; desktop/mobile/keyboard checks pass; live and fallback demos are rehearsed and timed |
| Test evidence | 10% | 71 automated tests, 20 adversarial regressions, media boundaries, failure drill, CI and clean-install rehearsal | Evidence is spread across documents; requirement-to-test traceability and defect closure need a single judge-readable view | One evidence index maps each critical journey/edge case to test ID, result, environment, artifact and closed/open defect |
| Deployment | 20% | PowerShell setup/start, preflight, model inventory, logging, queue recovery, backup/restore, cleanup and support bundle | No measured clean Windows 11 baseline run; Python launcher ambiguity remains possible; rollback and setup time are not yet demonstrated on target | Fresh Windows machine completes documented install, model cache, preflight, real job, restart, backup/restore and rollback with timing and screenshots/logs |
| Handover and training | 10% | Architecture, user/admin/UAT/privacy/licence/support/troubleshooting documents exist | Current user/support guides are concise rather than a complete adoption package; ownership, training agenda and handover acceptance need stronger artifacts | BAIF handover pack includes quick starts, ownership matrix, operating calendar, support/escalation flow, training plan, exercises and signed acceptance checklist |

## Non-negotiable external inputs

These three requests must be initiated immediately because no amount of independent coding can substitute for them.

| Needed by | Owner | Input | Proof required |
| --- | --- | --- | --- |
| 6 Aug | Chirag/team account owner | Accept the AI4Bharat/IndicTrans2 repository terms and cache the intended checkpoints without sharing credentials | `model_inventory.json` with repository, revision, local path, size, checksum where available and licence |
| 7 Aug | Chirag | Confirm one qualified Hindi reviewer and one qualified Marathi reviewer, with review slots on 10-12 Aug and 15 Aug | Named reviewer worksheet/sign-off with date, release commit and unresolved concerns |
| 8 Aug | Chirag/BAIF IT | Secure a clean Windows 11 machine meeting 16 GB RAM and six-core CPU baseline for 13-15 Aug | Machine specification, clean-install log, preflight, timings, UAT record and support bundle |

Optional but valuable: request a small set of non-confidential, approved BAIF agriculture samples by 8 August. If none is supplied, retain the licensed public fixture and state that boundary explicitly.

## Execution plan

### Phase 0 - alignment and unblock (5-6 Aug)

Goal: convert the new scoring matrix into one source of truth and start every external dependency.

- [x] Read the new organiser evaluation criteria and timeline.
- [x] Re-audit Git, CI, automated tests, first-run UI, mobile layout and final deck.
- [x] Reframe the roadmap around the five weighted criteria.
- [ ] Send the three external requests above and record owners/confirmed dates.
- [ ] Create a single evidence register with rubric claim, test/evidence path, environment, owner and status.
- [ ] Decide the exact Windows release profile and model revisions; freeze dependencies after validation.

Exit gate: every external gate has a named owner and date; no critical work is hidden behind “later”.

### Phase 1 - judged translation quality (6-12 Aug)

Goal: make the 30% solution-efficiency claim defensible on the intended backend.

- [ ] Cache and inventory all three IndicTrans2 direction checkpoints through an authorised account.
- [ ] Prove the application reports IndicTrans2 provenance and does not silently fall back during judged runs.
- [ ] Expand the immutable engineering seed into a separate reviewer corpus of at least 120 examples: 20 per language direction.
- [ ] Cover agriculture instructions, crop/soil/water/livestock terms, names/places, numbers/units/dates/phone numbers, safety/pesticide cautions, long sentences, colloquial phrasing and code-switching.
- [ ] Record source, reference, machine output, adequacy, fluency, terminology, preservation, critical-error class and reviewer correction for every example.
- [ ] Run chrF++ and preservation/script/backend checks by direction; report latency and peak memory on CPU.
- [ ] Complete Hindi and Marathi review round one; convert recurring corrections into glossary entries only when reviewers approve them.
- [ ] Re-run all six directions after fixes and complete reviewer sign-off.
- [ ] Add representative Hindi/Marathi speech clips for ASR evidence, including clean/noisy and phone-microphone conditions; report WER/CER with limitations.

Quality release gate:

- all six directions present on IndicTrans2;
- zero critical number, unit, name, URL, email or target-script failures in the signed set;
- no unlabelled backend fallback;
- preferred agriculture terminology misses reviewed and either corrected or explicitly accepted;
- every safety-critical sample marked for mandatory human approval;
- report names model revision, hardware, corpus version and reviewer.

The threshold will not be weakened to make the report green. Failed cases become visible defects and are corrected, guarded or documented.

### Phase 2 - product and accessibility hardening (9-15 Aug)

Goal: protect the 30% ease-of-use score using realistic novice journeys.

- [ ] Run the complete trainer path with text, one document and one public agriculture video on the final model build.
- [ ] Verify first-run admin, account request/approval/deactivation and secure session expiry from a novice perspective.
- [ ] Verify review differences, correction, atomic approval, exact reuse provenance, search, retry, cancel and safe delete.
- [ ] Test 360, 390, 768 and 1440 pixel layouts; keyboard-only operation; visible focus; labels; contrast; zoom/reflow; long Hindi/Marathi text; reduced-motion behaviour; and screen-reader landmarks.
- [ ] Make only evidence-driven UI changes. No decorative dashboard, chatbot or speculative feature expansion.
- [ ] Replace technical or ambiguous user-facing errors found in UAT with specific recovery guidance.
- [ ] Time three personas: trainer, administrator and offline field recipient. Record confusion points and close all severity-1/2 usability defects.
- [ ] Capture final real-model screenshots and a short fallback walkthrough from the same release commit.
- [x] Add a state-aware first-run checklist that routes administrators/trainers directly to System readiness, first translation or user approvals.

Experience release gate: a first-time trainer completes translate -> inspect trust cues -> correct -> approve -> download -> open offline with no terminal use and no coaching beyond the user guide.

### Phase 3 - Windows deployment and operations (13-16 Aug)

Goal: turn “Windows-ready” into measured target-machine proof for the 20% deployment category.

- [ ] Start from a clean Windows 11 account with no project Python environment.
- [ ] Record hardware, OS build, free disk, network assumption and administrator permissions.
- [ ] Run the PowerShell setup exactly as documented; record hands-on steps, total elapsed time, download volume and disk consumption.
- [ ] Eliminate Python launcher ambiguity: scripts must detect unsupported versions and explain the exact correction before installation.
- [ ] Cache pinned model revisions, run checksum/inventory checks and then disable runtime downloads and hosted translation.
- [ ] Run preflight and process text, a scanned document, audio and video on CPU; record per-stage timings and peak memory.
- [ ] Restart during a disposable job, verify recovery, inspect structured logs and generate a privacy-safe support bundle.
- [ ] Back up, restore into a disposable location, verify checksums and document rollback to the previous release package.
- [ ] Run retention cleanup in dry-run and controlled modes; verify no approved artifact is removed unexpectedly.
- [ ] Complete the trainer/admin/field UAT record on the same release commit.

Deployment release gate: one documented setup path works from a clean machine; normal operation requires no developer; rollback, recovery and support evidence are reproducible; all prerequisites and timings are reported honestly.

### Phase 4 - evidence, handover and training (15-18 Aug)

Goal: make the remaining 20% easy to assess in under two minutes.

- [ ] Consolidate automated, adversarial, browser, quality, media, Windows, recovery and UAT results into a traceability matrix.
- [ ] Give every defect an ID, severity, discovered-by test, disposition, release commit and retest evidence.
- [ ] Create a one-page trainer quick start with screenshots and a one-page admin start/stop/recovery card.
- [x] Create a printable role-based BAIF onboarding runbook covering administrator, trainer, field recipient, internal demo, recovery and handover acceptance.
- [ ] Expand the handover pack with system owner, model/data owner, reviewer owner, backup owner, first-line support and escalation contacts/roles.
- [ ] Add daily/weekly/monthly operating checks, retention rules, update process, model-change approval and incident/support workflow.
- [ ] Prepare a 60-minute administrator session, 45-minute trainer session and 20-minute field-recipient orientation with exercises and completion checks.
- [ ] Create a BAIF knowledge-transfer checklist and handover acceptance record.
- [ ] Ensure user guidance is non-technical, while the technical appendix is sufficient to install, diagnose, restore and extend the solution.

Handover release gate: a person who did not build VaaniSetu can complete the documented install or user journey and knows who owns each operational decision.

### Phase 5 - submission and pitch lock (17-21 Aug)

Goal: present one memorable story backed by visible proof, with no stale or unsupported claim.

- [ ] Rebuild the five-slide deck around the new weights:
  1. BAIF problem and measurable office-to-field outcome;
  2. the trainer journey using real product visuals;
  3. IndicTrans2 six-direction quality and human-review evidence;
  4. Windows deployment, formats, reliability and test proof; and
  5. adoption, handover and why VaaniSetu is ready for BAIF.
- [ ] Remove “ready tomorrow” and other date-relative copy; replace architecture-heavy space with final evidence.
- [ ] Put full sources and claim provenance in speaker notes; ensure no clipping, unreadable text or unsupported metric.
- [ ] Rehearse a 3.5-minute primary demo and a 90-second backup path. Both must show value, review trust and offline playback.
- [ ] Prepare concise answers for accuracy, licence, privacy, no-cloud rationale, scaling, failure recovery, ownership, costs and remaining limitations.
- [ ] Build the privacy-safe candidate ZIP; verify source manifest, SBOM, model inventory, checksums and exclusion of accounts, sessions, BAIF content, secrets, logs and model weights.
- [ ] Run a red-team review against every organiser criterion and every claim in the deck/demo.
- [ ] Freeze the release candidate, create the final tag only when acceptance gates are satisfied, and upload at least 24 hours before the deadline where the portal permits.
- [ ] Download/reopen the submitted artifact from the submission destination and preserve receipt/checksum evidence.

Submission release gate: every slide claim points to evidence; the live and fallback paths work offline; the uploaded package reopens cleanly; no confidential or unlicensed asset is included.

## Calendar

| Date | Primary outcome | No-slip decision |
| --- | --- | --- |
| 5 Aug night | Rubric-aligned plan and external requests | Stop adding unscored features |
| 6-8 Aug | IndicTrans2 cache/inventory, benchmark expansion, Windows slot confirmed | Escalate immediately if any external owner/date is missing |
| 9-12 Aug | Six-direction runs, quality corrections and bilingual sign-off | Quality claims remain explicitly limited until signed |
| 13-15 Aug | Clean Windows deployment, measured E2E, accessibility and persona UAT | Freeze feature work after severity-1/2 fixes |
| 16-17 Aug | Handover/training and evidence index complete | Documentation must match the exact release commit |
| 18 Aug | Deck, demo video, judge Q&A and candidate bundle rebuilt | No new capability claims after evidence freeze |
| 19 Aug | Full dress rehearsal and adversarial review | Fix only release-blocking defects |
| 20 Aug | Final verification, upload and downloaded-artifact check | Preserve a full day of contingency |
| 21 Aug | Submission deadline | No untested last-minute changes |
| 22-24 Aug | Finals rehearsal and role practice | Use the submitted build only |
| 25-27 Aug | Tentative finals | Lead with the trainer outcome, then evidence |

## Defect and scope policy

- Severity 1: privacy/security breach, data loss, wrong-language/critical preservation failure, broken install or unusable core journey. Must close before submission.
- Severity 2: failed supported format, inaccessible primary action, unreliable recovery or misleading provenance. Must close before submission.
- Severity 3: non-blocking usability/documentation issue. Close when it materially improves a scored criterion.
- Severity 4: cosmetic or speculative enhancement. Defer unless it is trivial and introduces no release risk.

No fuzzy translation reuse, hosted translation, live field translation, decorative analytics or new platform expansion enters this release. Exact approved reuse and the office-to-offline workflow remain the product boundary.

## Evidence required in the final candidate

- release commit/tag and GitHub CI URL;
- Python/dependency/SBOM/source manifests;
- IndicTrans2 model inventory and explicit licences/revisions;
- six-direction machine and reviewer quality reports;
- ASR/OCR/media and format-boundary evidence;
- Windows hardware/preflight/setup/performance record;
- browser/mobile/accessibility/UAT evidence;
- failure drill, logs, support bundle, backup/restore and rollback evidence;
- final offline package and integrity verification;
- complete handover/training pack;
- final deck, demo script, fallback walkthrough and submission receipt.

## Immediate next three priorities

1. Unblock authorised IndicTrans2 access and run the judged backend with recorded provenance.
2. Confirm Hindi/Marathi reviewers and expand the six-direction agriculture corpus for signed quality evidence.
3. Reserve the clean BAIF-spec Windows 11 machine and prepare the measured deployment acceptance sheet.

Until these are complete, describe VaaniSetu as a verified, demo-ready release candidate, not fully production-approved.

## Session ledger

### 5 Aug 21:02 - onboarding and runbook slice

Completed:

- Added a signed-in **Start here** panel with worker, access and first-translation readiness, one next action, and a direct runbook link.
- Added the printable `BAIF_ONBOARDING_RUNBOOK.html` and stylesheet with role-based administrator, trainer, field-recipient and internal-demo paths, fast recovery and handover acceptance.
- Hardened Windows setup to select Python 3.11/3.10 explicitly, create/use a private `.venv`, stop early on unsupported Python and print one clear next step.
- Added the runbook to the README, user/admin guides, handover index, submission index, release-policy gate and candidate bundle.

Evidence:

- 71/71 tests pass; Python compilation, frontend syntax, `pip check` and repository release policy pass.
- Focused onboarding endpoint/asset/Windows-launcher tests pass.
- Real browser first-admin and Start here journeys pass on desktop and 390 x 844 mobile with no horizontal overflow or console warnings/errors.
- The standalone runbook renders on desktop/mobile under the existing strict content-security policy.

Blockers:

- PowerShell was unavailable on the local Mac; execute the revised setup/start scripts on the clean BAIF-spec Windows 11 acceptance machine before claiming measured deployment readiness.
- IndicTrans2 access, Hindi/Marathi reviewer sign-off and target Windows evidence remain the three external production gates.

Next three priorities:

1. Cache and inventory the authorised IndicTrans2 checkpoints, then run all six directions with explicit provenance.
2. Expand the reviewer corpus and schedule Hindi/Marathi quality sign-off.
3. Run the revised onboarding/install path on the clean Windows 11 baseline and record hands-on time, downloads, disk, preflight and UAT.
