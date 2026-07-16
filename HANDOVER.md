# VaaniSetu Handover Pack

## Solution and scope

VaaniSetu is a local/on-prem browser application for authorised BAIF staff to translate English, Hindi, and Marathi text, documents, recordings, audio, and video. One CPU worker holds the models and files; normal jobs do not call paid APIs or silently download models. Field recipients use the exported ZIP, text, audio, video, or subtitle files offline.

The supported formats and enforced limits are in `DELIVERY_COMPATIBILITY.md`. Exact Office layout preservation is not promised: translated TXT, Markdown, and table exports are reviewable and can be reflowed into BAIF templates.

## Process flow

1. An administrator installs dependencies/models and completes the preflight.
2. The first administrator creates an account; later users request access and require approval.
3. A trainer records, pastes, or uploads content and chooses the language pair and outputs.
4. The single model worker extracts/transcribes, translates, validates, synthesises optional speech, and packages outputs.
5. A trainer reviews the machine output, saves a corrected version, and approves it.
6. Exact approved source segments may be reused locally with provenance; the user can opt out.
7. The integrity manifest proves the downloaded package is intact and usable without the server.

## Handover contents

- Setup and architecture: `README.md`, `BAIF_ARCHITECTURE_NOTE.md`, `config/model_manifest.json`
- Operation: `USER_GUIDE.md`, `ADMIN_GUIDE.md`, `TROUBLESHOOTING.md`
- Governance: `PRIVACY.md`, `OPEN_SOURCE_COMPLIANCE.md`, `SUPPORT_MODEL.md`
- Acceptance: `UAT.md`, `RELEASE_CHECKLIST.md`, `benchmarks/README.md`
- Engineering evidence: `TEST_EVIDENCE.md`
- Organiser alignment: `HACKATHON_REQUIREMENTS_AUDIT.md`
- Recovery: `scripts/operations.py`, `scripts/verify_package.py`

The runtime includes a privacy-safe impact view/export containing aggregate counts only. It never includes source or translated content. Multi-file batches remain sequential and therefore preserve the one-worker CPU safety boundary.

## Assumptions and external acceptance

- BAIF supplies a Windows 11 CPU worker with at least 16 GB RAM and adequate free disk.
- An authorised team account accepts the AI4Bharat model terms and caches the three IndicTrans2 checkpoints.
- Hindi and Marathi reviewers approve representative BAIF terminology and benchmark material.
- The engineering seed benchmark is evidence of tooling, not BAIF linguistic approval.

## Known risks

- Accuracy varies with dialect, noise, OCR quality, and model availability. Human review remains required for health, safety, pesticide, financial, or legally consequential content.
- NLLB is a non-commercial fallback and cannot support an unrestricted production-license claim.
- Natural Marathi/Hindi TTS availability depends on cached Indic Parler/Piper voices; browser/eSpeak speech is a lower-quality fallback.
- Cooperative cancellation stops at the next stage boundary; an active model call is not force-killed.
