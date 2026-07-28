# Release Candidate Checklist

Last reviewed: 28 July 2026

## Verified engineering

- [x] Python compilation, frontend syntax and repository release policy pass.
- [x] All 69 unit/integration/security/format tests pass locally, including scanned-PDF OCR; the published CI gate is green.
- [x] Six-direction engineering benchmark passes with invariant, script, unchanged-output and backend checks.
- [x] Real audio/video E2E and full 30-minute audio/15-minute 1080p boundary harness pass.
- [x] Desktop/mobile, keyboard, review, retry, cancellation, offline and download journeys pass.
- [x] Offline packages open without the server and reject checksum tampering.
- [x] Backup/restore, cleanup, migration and privacy-safe support bundle are proven on disposable data.
- [x] Dependency/source evidence and privacy, licence, operation, recovery, support and UAT guides exist.
- [x] `main` matches the published release commit, CI is green and no secrets/private data/model weights are tracked.

## Internal submission packaging — complete

- [x] Final five-slide deck is complete, visually inspected and consistent with the organiser requirements audit.
- [x] Canonical licensed public agriculture input/output bundle, real-model screenshots and backup walkthrough are ready.
- [x] Candidate builder packages the source manifest/SBOM, reports, model inventory and verified demo package without private runtime state.
- [x] Demo runbook and all six failure-recovery scenarios pass; a clean-install rehearsal is recorded in the release evidence.

## External acceptance

- [ ] Intended IndicTrans2 checkpoints are accepted, cached, inventoried and licence-confirmed.
- [ ] Hindi and Marathi reviewers sign the representative benchmark/glossary worksheet.
- [ ] Target Windows 11 CPU worker passes installation, preflight, media processing and the three UAT personas.
- [ ] Approved BAIF sample content is included if supplied.
- [ ] Final release tag and BAIF IT knowledge-transfer record are created.

Do not tick external acceptance without the named reviewer, model inventory or target-machine evidence. Engineering completion and external validation are deliberately separate.
