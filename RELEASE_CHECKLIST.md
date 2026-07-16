# Release Candidate Checklist

## Engineering evidence

- [ ] Python compile and frontend syntax checks pass on Python 3.10/Node.
- [ ] Unit/integration/security/format tests pass, including OCR on CI.
- [ ] Six-direction benchmark gate passes; reviewer worksheet is signed by Hindi and Marathi reviewers.
- [ ] Audio/video E2E and full boundary stress reports pass on the target Windows CPU worker.
- [ ] Desktop/mobile keyboard, focus, contrast, long-script, loading, empty, failure, retry, cancel, offline, and download flows pass.
- [ ] Preflight is green with runtime model downloads and hosted translation disabled.
- [ ] Offline packages verify and open without a server connection.

## Governance and handover

- [ ] Model inventory records exact installed file checksums/revisions; licenses are accepted by BAIF.
- [ ] Dependency SBOM, source archive, approved samples, reports, and demonstration outputs are archived.
- [ ] Privacy, known limitations, setup, operating, recovery, support, and UAT documents are reviewed.
- [ ] Backup/restore is proven on a disposable copy; support bundle is inspected for redaction.
- [ ] `main` matches the release commit, GitHub CI is green, no secrets/private data/generated weights are tracked, and the release tag is created.

External acceptance boxes must not be ticked without the named reviewer/machine evidence. Engineering completion and external validation remain separate.
