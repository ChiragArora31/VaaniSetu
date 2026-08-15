# Requirements Alignment

Initial audit: 16 July 2026
Last reviewed: 15 August 2026
Source of truth: the organiser screenshots supplied by the team on 16 July 2026 plus the 5 August 2026 implementation-review email containing the weighted evaluation criteria and timeline. No requirement beyond those supplied materials is assumed.

## Executive conclusion

VaaniSetu is aligned to the requested product: a production-ready, zero-license-cost web application that runs on BAIF's CPU-only Windows office infrastructure, translates English/Hindi/Marathi learning material, and creates reusable outputs for offline field use. The remaining external gates are model-account acceptance, bilingual human sign-off, and proof on the target Windows machine. They are tracked separately and do not block independent product work.

The 5 August rubric makes the remaining proof especially important: solution efficiency and ease of use are worth 30% each, deployment is worth 20%, and test evidence plus handover/training are worth 10% each. The implementation is a release candidate; the final submission must now convert its capabilities into measured IndicTrans2, novice-journey, Windows and adoption evidence.

## Implementation-review scoring criteria received 5 August

| Criterion | Weight | Organiser emphasis | VaaniSetu finishing response |
| --- | ---: | --- | --- |
| Solution efficiency | 30% | Working end-to-end core journey; translation accuracy; language, format and scenario coverage | Run the final local IndicTrans2 path, expand the six-direction agriculture corpus, obtain bilingual sign-off and report preservation/performance evidence |
| Ease of use | 30% | Clear, time-boxed walkthrough demonstrating journey, value and impact with a fallback | Complete novice persona UAT, final accessibility/mobile checks, real-product deck visuals, timed live demo and offline fallback |
| Test evidence | 10% | Documented critical journeys, edge cases, results and understood defects | Consolidate automated, adversarial, browser, media and UAT results into one traceability/defect evidence index |
| Deployment | 20% | Repeatable configuration/setup, prerequisites, downloads, rollback and logging | Measure a clean BAIF-spec Windows install, model cache, recovery, backup/restore, rollback and support flow |
| Handover and training | 10% | Ownership, support/runbook, adoption and documentation sufficient without the team | Expand quick starts, ownership/escalation, operating calendar, training exercises, KT and acceptance records |

Timeline received with the rubric: implementation phase 15 July-21 August, submission deadline 21 August, tentative finals 25-27 August and tentative winner announcement 31 August.

## Requirement-by-requirement compliance

| Organiser requirement | Status | VaaniSetu evidence | Remaining action |
| --- | --- | --- | --- |
| Impact | Met | Converts text, recordings, audio, video and office documents into reusable translated text, subtitles, speech and offline packages; privacy-safe dashboard shows throughput, minutes, reuse and approvals | Continue collecting representative evidence |
| Scalability and production readiness | Met | Durable one-worker CPU queue, restart recovery, bounded uploads, disk guard, metrics, backup/restore, cleanup, support bundle and model preflight | Prove on the external Windows baseline |
| Usability/UX | Met | Browser workflow, recording, multi-file batches, progress, actionable errors, atomic review/approval, retry/cancel/delete, searchable library, trust card and mobile layout | None internally |
| Tech safety, fairness and inclusivity | Met | No silent hosted processing, local-first privacy, RBAC, human approval, source/output preservation checks, target-script checks, glossary findings, model provenance and accessible controls | Obtain bilingual human sign-off externally |
| Zero cost / open source only | Met | Open-source stack, pinned dependencies, model/license manifest, SBOM/source manifest, no BAIF paid service requirement | Confirm gated model terms through the team account |
| Differentiate through edge cases and optimisation | Met | Corrupt-file handling, adversarial state/race/path/resource tests, size/duration/resolution limits, scanned PDF OCR, invariant protection, restart recovery, tamper detection, low-disk handling and CPU-optimised routes | Make these strengths explicit in the demo and deck |
| Existing low-spec BAIF infrastructure, no GPU | Met by design | CPU-only CTranslate2/Whisper paths, one heavy worker, int8 profiles, no GPU assumption | External Windows performance proof remains |
| Target hardware: i5 11th Gen/equivalent or Ryzen 5 6+ cores; 16 GB RAM; 512 GB/1 TB storage | Met by configuration | Hardware-aware preflight, one worker, disk checks and bounded media | Run the preflight on the target machine |
| Windows 11 and Office 2020+ | Implemented, proof pending | PowerShell setup/start scripts and Office/PDF/table ingestion | External clean-machine installation evidence |
| Internet available at BAIF office for setup/translation | Met | Controlled model setup permits downloads; normal jobs can run from cached local models | Cache approved production models externally |
| Translation occurs at BAIF office, not live in the field | Met | Local/on-prem worker architecture is stated throughout the product and documentation | None |
| Outputs usable offline in the field | Met | Integrity-protected ZIP with text, subtitles, audio/video and a server-free landing page with direct links and playback | None |
| Audio: up to 30 min; 50 MB compressed MP3/OGG; 150 MB WAV | Met | Exact type-aware size and duration enforcement plus boundary stress evidence | None |
| Video: MP4/MKV, 720p/1080p, up to 15 min and 200 MB | Met | Exact size/duration/resolution enforcement, subtitle/voice outputs and 15-minute 1080p stress evidence | None |
| Store previous translations for reference and reuse | Met | Durable library, local manifest, approved translation memory, searchable results, reuse metrics and controlled batch workflow | None |
| Test with public agriculture/crop videos up to 15 minutes | Met | Four-minute CC BY 3.0 India agriculture video completed the real local pipeline; full 15-minute boundary harness also passes | None internally |
| Personal-laptop/DLP guidance | Met | Repository policy excludes credentials, generated media, private BAIF data and model weights | Continue the same policy |
| Production-ready web application | Met | Authenticated browser app, API, durable processing, diagnostics and handover tooling | External deployment acceptance remains |
| Handover source, documentation and training/KT | Met | Source repository plus user/admin/privacy/support/troubleshooting/UAT/handover documents | Conduct the external KT session if selected |
| 4–5 slide design deliverable covering problem, architecture, stack and pillars | Met | Final five-slide deck covers the gap/impact, trainer journey, constrained architecture, quality controls and honest readiness | None |

## Deferred external list

1. Accept the AI4Bharat/IndicTrans2 model access terms in the team Hugging Face account and cache the intended checkpoints without sharing credentials.
2. Obtain Hindi and Marathi reviewer approval for the benchmark, glossary and representative outputs.
3. Run installation, preflight, processing and UAT on a clean Windows 11 CPU-only machine matching BAIF's baseline.
4. Eight BAIF videos are now supplied and technically validated in place. Complete the shortest full-pipeline Windows run and bilingual review; keep BAIF content out of Git/public evidence.
5. Create the release tag and conduct the BAIF IT knowledge-transfer session after the three acceptance gates above.

## Audit risks to keep visible

- Engineering scores from NLLB are not evidence of IndicTrans2 readiness or bilingual approval.
- An internet connection at the office does not authorise sending BAIF content to third-party translation services.
- “Offline” means downloaded field outputs work without VaaniSetu; the office translation worker itself is not a live field app.
- Quality claims must always name the model/backend and distinguish machine output from approved human corrections.
- The final demo shows the core trainer journey before operational depth or optional document formats; follow [DEMO.md](DEMO.md).
