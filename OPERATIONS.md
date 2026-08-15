# Operations Guide

Start with the [BAIF onboarding runbook](BAIF_ONBOARDING_RUNBOOK.html). It gives one role-based path for installation, first administrator, trainer approval, acceptance testing, field handoff and internal demonstration.

For a new Windows machine or formal release test, use [Windows Setup and Handover](SETUP.md). It is the canonical zero-to-ready procedure and includes the automated gate, real BAIF video cases and go/no-go record.

## Install and start

On the Windows 11 BAIF worker, run `scripts\setup_baif_worker.ps1`, then `scripts\start_baif_worker.ps1`. Complete first-admin setup in the browser. Do not expose port 8501 directly to the public internet; use the BAIF LAN or an approved reverse proxy with TLS.

Before accepting jobs:

```text
python scripts/operations.py migrate
python scripts/operations.py preflight
python scripts/operations.py model-inventory
```

`preflight` must report ready on the production machine. Set `BAIF_ALLOW_MODEL_DOWNLOAD=0` during operation and retain one worker thread. Use a strong unique administrator password and deactivate departed users promptly.

The preflight report recommends `balanced` for BAIF's confirmed 16 GB/6+ core baseline, permits `quality` only when at least 32 GB RAM and 8 cores provide headroom, and marks systems below 16 GB unsupported. It always retains one model worker; benchmark representative media before changing profiles.

## Routine operation

- Review `/health`; administrators can inspect `/metrics` for queue/failure/storage status.
- Archive completed output packages according to BAIF retention policy.
- Preview cleanup: `python scripts/operations.py cleanup --days 7 --dry-run`.
- Apply cleanup: `python scripts/operations.py cleanup --days 7`.
- Back up before upgrades: `python scripts/operations.py backup backups\vaanisetu-backup.zip`.
- Generate diagnostics: `python scripts/operations.py support-bundle outputs\support.zip`.

`GET /impact` is available to approved users and reports only aggregate operational evidence: job outcomes, media minutes, artifacts, language directions, approvals, approved-memory reuse and storage. The browser can export the same privacy-safe JSON for demonstrations or reporting.

Multi-file browser batches submit one file at a time. They do not increase `BAIF_JOB_WORKERS`, so the CPU/memory safety model remains unchanged.

The backup contains accounts, reviews, job metadata, and content artifacts; store it only in BAIF-approved encrypted storage. The support bundle excludes credentials, source/translated content, artifacts, and model weights. Inspect it before sharing.

## Restore and upgrade

Stop the worker, preserve the current `outputs` folder, verify the backup, then run `python scripts/operations.py restore BACKUP.zip --force` and `python scripts/operations.py migrate`. Restart and perform the UAT smoke path. Never restore an unknown ZIP.

## Troubleshooting

| Symptom | Safe recovery |
| --- | --- |
| Translation model not ready | Stop production jobs, cache the required IndicTrans2 assets during controlled setup, rerun preflight and keep runtime downloads disabled. |
| OCR unavailable | Install Tesseract with `eng`, `hin` and `mar` data; confirm preflight. Use selectable-text PDFs meanwhile. |
| No speech detected | Confirm the file contains audible speech, choose the spoken language and retry with a short clean sample. |
| Voice output missing | Use the text/subtitle outputs, install the configured local TTS model and rerun preflight. |
| Worker disk is low | Back up required packages, preview cleanup and then remove expired jobs through the supported cleanup command. Never manually delete `.auth` or `.reviews`. |
| Job interrupted after restart | The durable queue marks it as failed; restore readiness and use **Run again**. |
| Package will not open | Run the package verifier and redownload if any checksum fails. Never ignore a mismatch. |
| Port 8501 is busy | Stop the old worker or choose an approved alternate port. Do not run competing model workers. |
| Repeated sign-in failures | Wait for the throttle window and verify the account remains active. |

## Support ownership

BAIF owns first-line operation: user approval, readiness checks, retention, backups and basic retries. The implementation team handles reproducible application defects and model/setup escalation. Language-quality questions go to the designated Hindi and Marathi reviewers; infrastructure and security incidents follow BAIF's incident process.

For escalation, generate a privacy-safe support bundle and provide the release commit, preflight result, failure time, job ID and recovery already attempted. Never attach confidential source material unless BAIF explicitly authorises a secure transfer.

Knowledge transfer is complete when an administrator can install the worker, approve a trainer, execute the acceptance personas, verify an offline package, restore a disposable backup and produce a redacted support bundle.
