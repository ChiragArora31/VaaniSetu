# VaaniSetu Implementation Roadmap

Last reviewed: 28 July 2026

## Finish-line summary

All work that can be completed independently is done. VaaniSetu is a verified release candidate with a complete trainer workflow, submission deck, rehearsable demo, public agriculture video proof, backup walkthrough, evidence bundle tooling and handover documentation.

Production acceptance remains deliberately separate: **0 of 3 external gates** have evidence today. They are listed at the end of this document and are the only blockers to an unrestricted production claim.

## Achieved

### Product and experience

- [x] Text, recording, PDF/scanned PDF, Office/table, audio and video inputs
- [x] All six English/Hindi/Marathi directions with distinct-language enforcement
- [x] Exact organiser size, duration and resolution limits
- [x] Local transcription/translation, subtitles, optional speech/video and verified offline ZIP
- [x] Human correction, atomic final approval, version history and exact approved-memory reuse
- [x] Agriculture glossary, invariant/script checks, provenance and review differences
- [x] Authenticated responsive UI, keyboard tabs, durable CPU queue, cancellation/restart recovery and searchable library
- [x] Sequential ten-file batches, privacy-safe impact metrics and safe delete/reset behaviour

### Reliability and operations

- [x] 69 automated tests, including 20 adversarial regressions
- [x] Corrupt review/report recovery, bounded state/resources, archive/path protection and checksum tamper rejection
- [x] Low-disk refusal before partial job creation and concise optional-media fallbacks
- [x] Six-direction quality gate with local NLLB CTranslate2 INT8 and no critical preservation/script/backend failure
- [x] Full 30-minute audio and 15-minute 1080p boundary harness
- [x] Windows setup/start scripts, preflight, inventory, backup/restore, cleanup, migration and support bundle

### Submission package

- [x] Final five-slide deck aligned to every evaluation pillar
- [x] 3½-minute demo script and judge Q&A
- [x] Canonical CC BY 3.0 public agriculture video and verified real-model output package
- [x] Clean real-model desktop/mobile screenshots and 22-second offline backup walkthrough
- [x] Source manifest, SBOM, quality, stress, preflight, model, failure-drill and demo evidence
- [x] Privacy-safe candidate ZIP builder that excludes users, sessions, secrets, BAIF content, models and logs
- [x] Complete user, admin, UAT, handover, privacy, licence, support and troubleshooting documentation

## Verified evidence

- 69/69 tests pass locally; Python compilation, frontend syntax, dependency and repository policy checks pass.
- Real browser run: English→Hindi NLLB CTranslate2 INT8 completed in 43.8 seconds; approved exact reuse completed in 0.6 seconds.
- Public four-minute agriculture video completed local transcription, translation, captions, speech/video and checksum package generation in 120 seconds.
- Six demo-day failures pass: no model, low disk, cancel race, worker restart, corrupted ZIP and offline playback.
- Desktop and 390×844 mobile journeys have no horizontal overflow, duplicate IDs, unlabeled controls or console failures.

Detailed evidence is in [TEST_EVIDENCE.md](TEST_EVIDENCE.md); the exact demo is in [SUBMISSION_RUNBOOK.md](SUBMISSION_RUNBOOK.md).

## Deliberate release boundary

The following ideas are not unfinished requirements and are intentionally excluded from this release:

- Fuzzy/near-duplicate translation reuse, because an approximate agricultural match can silently change meaning. Only exact human-approved reuse is permitted.
- Live field translation or cloud APIs, because the organiser defined office translation and offline field playback.
- Decorative dashboards or chatbot features that distract from the trainer journey.
- Admin glossary rollback and batch pause/resume until BAIF assigns governance and operator ownership.

## External gates — owner action required

- [ ] An authorised team account accepts the intended IndicTrans2 terms and caches/inventories the selected checkpoints.
- [ ] Qualified Hindi and Marathi reviewers sign the representative translation and terminology worksheet.
- [ ] A clean Windows 11 machine matching BAIF's 16 GB/six-core CPU baseline passes setup, preflight, media processing and UAT.

After those gates:

- [ ] Substitute approved BAIF material if the panel supplies it; otherwise retain the licensed public fixture.
- [ ] Create the final release tag and conduct BAIF IT knowledge transfer if selected.

Nothing else is being deferred as internal product or submission work.
