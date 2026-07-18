# Release Candidate Checklist

Last reviewed: 18 July 2026

## Verified engineering

- [x] Python compilation, frontend syntax and repository release policy pass.
- [x] All 65 unit/integration/security/format tests pass in CI, including scanned-PDF OCR.
- [x] Six-direction engineering benchmark passes with invariant, script, unchanged-output and backend checks.
- [x] Real audio/video E2E and full 30-minute audio/15-minute 1080p boundary harness pass.
- [x] Desktop/mobile, keyboard, review, retry, cancellation, offline and download journeys pass.
- [x] Offline packages open without the server and reject checksum tampering.
- [x] Backup/restore, cleanup, migration and privacy-safe support bundle are proven on disposable data.
- [x] Dependency/source evidence and privacy, licence, operation, recovery, support and UAT guides exist.
- [x] `main` matches the published release commit, CI is green and no secrets/private data/model weights are tracked.

## Internal submission packaging

- [ ] Final 4–5 slide deck is complete and consistent with the organiser requirements audit.
- [ ] Canonical public agriculture demo input/output bundle and backup demo recording are ready.
- [ ] Candidate evidence bundle contains the source manifest/SBOM, reports, model inventory and verified package.
- [ ] Demo and failure-recovery runbooks have been rehearsed from a clean checkout.

## External acceptance

- [ ] Intended IndicTrans2 checkpoints are accepted, cached, inventoried and licence-confirmed.
- [ ] Hindi and Marathi reviewers sign the representative benchmark/glossary worksheet.
- [ ] Target Windows 11 CPU worker passes installation, preflight, media processing and the three UAT personas.
- [ ] Approved BAIF sample content is included if supplied.
- [ ] Final release tag and BAIF IT knowledge-transfer record are created.

Do not tick external acceptance without the named reviewer, model inventory or target-machine evidence. Engineering completion and external validation are deliberately separate.
