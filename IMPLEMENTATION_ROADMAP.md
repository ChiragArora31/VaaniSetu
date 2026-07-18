# VaaniSetu Winning Roadmap

Last reviewed: 18 July 2026
Implementation window: 9 July–14 August 2026
Finals (tentative): 17 August 2026

## Goal

Deliver a production-ready, zero-paid-licence translation workflow for BAIF's CPU-only Windows office environment. A trainer should be able to translate English, Hindi or Marathi material, review it and send a trustworthy package for offline field use without technical assistance.

The complete organiser mapping is in [HACKATHON_REQUIREMENTS_AUDIT.md](HACKATHON_REQUIREMENTS_AUDIT.md).

## Engineering status — complete

- [x] Text, recording, audio, video and common Office/PDF/table inputs
- [x] All six English/Hindi/Marathi directions
- [x] Local transcription, translation, subtitles, optional speech/video and offline ZIP outputs
- [x] Exact organiser size, duration and resolution limits
- [x] Human correction, versioned approval and approved translation-memory reuse
- [x] Agriculture glossary, invariant/script checks, trust/provenance and correction differences
- [x] Authenticated browser app, durable one-worker CPU queue and searchable library
- [x] Sequential multi-file batches and privacy-safe impact reporting/export
- [x] Windows setup/preflight, backup/restore, cleanup, diagnostics and handover material
- [x] 65-test clean CI, adversarial race/security coverage, real media/browser E2E and boundary stress evidence
- [x] Requirement, licence, privacy, support, UAT and release documentation

No known critical or high-severity engineering issue is open.

## Internal work we can do now

These tasks improve submission quality without external access or new product risk.

### Submission story

- [ ] Produce the final 4–5 slide deck: problem/impact, workflow, architecture/stack, evaluation evidence and deployment readiness.
- [ ] Write and rehearse a 3–5 minute judge demo: **translate → trust checks → correct/approve → reuse → take offline → impact**.
- [ ] Select one public agriculture video and create a repeatable demo-input/output bundle with no confidential content.
- [ ] Record a short backup demo and capture clean desktop/mobile screenshots.

### Release packaging

- [ ] Create a candidate evidence bundle containing source manifest/SBOM, test report, quality report, model inventory, preflight, stress report and verified sample package.
- [ ] Perform a fresh-repository installation rehearsal on an available supported non-target machine and record any documentation corrections.
- [ ] Run one final demo-day failure drill: no model, low disk, cancelled job, worker restart, corrupted ZIP and offline playback.

### Documentation

- [x] Remove stale test milestones and duplicated setup/model instructions.
- [x] Separate completed engineering from internal packaging and external acceptance.
- [x] Keep one concise entry point in `README.md` with specialised operator guides linked from it.

## Optional feature parking lot

Do not build these before the submission story and acceptance evidence are secure:

- Admin-managed glossary import/version history/rollback
- Near-duplicate suggestions beyond exact approved-memory reuse
- Batch pause/resume and an exportable batch manifest

They are useful extensions, not requirements or release blockers.

Avoid cloud translation dependencies, paid APIs, GPU-only features, live field translation, generic chatbots or decorative analytics that weaken the trainer journey.

## External acceptance — defer until available

- [ ] Authorised team account accepts and caches the intended IndicTrans2 checkpoints.
- [ ] Hindi and Marathi reviewers approve representative translations and terminology.
- [ ] Clean Windows 11 CPU-only installation, preflight, performance and UAT evidence is recorded.
- [ ] Approved BAIF content is used if the panel supplies it; otherwise retain public agriculture fixtures.
- [ ] Release tag and BAIF IT knowledge-transfer session are completed after the acceptance gates.

## Current evidence

- `main` and GitHub CI are green.
- All 65 tests pass in CI; 18 adversarial regressions also passed 25 consecutive randomized runs locally.
- Six-direction engineering quality has no preservation, script, untranslated or backend-provenance failure.
- Real audio/video, 30-minute audio and 15-minute 1080p boundary flows pass.
- Desktop and 390×844 mobile journeys pass without console errors or horizontal overflow.
- Offline packages have direct playback/links, checksums and deliberate-tamper rejection.

## Finishing line

Internally, the product is feature-complete; the next milestone is a polished submission package. Final production readiness requires the three external gates—IndicTrans2, bilingual approval and Windows-baseline proof—followed by the release tag and handover.
