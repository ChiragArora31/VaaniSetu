# Administrator Guide

## Install and start

On the Windows 11 BAIF worker, run `scripts\setup_baif_worker.ps1`, then `scripts\start_baif_worker.ps1`. Complete first-admin setup in the browser. Do not expose port 8501 directly to the public internet; use the BAIF LAN or an approved reverse proxy with TLS.

Before accepting jobs:

```text
python scripts/operations.py migrate
python scripts/operations.py preflight
python scripts/operations.py model-inventory
```

`preflight` must report ready on the production machine. Set `BAIF_ALLOW_MODEL_DOWNLOAD=0` during operation and retain one worker thread. Use a strong unique administrator password and deactivate departed users promptly.

## Routine operation

- Review `/health`; administrators can inspect `/metrics` for queue/failure/storage status.
- Archive completed output packages according to BAIF retention policy.
- Preview cleanup: `python scripts/operations.py cleanup --days 7 --dry-run`.
- Apply cleanup: `python scripts/operations.py cleanup --days 7`.
- Back up before upgrades: `python scripts/operations.py backup backups\vaanisetu-backup.zip`.
- Generate diagnostics: `python scripts/operations.py support-bundle outputs\support.zip`.

The backup contains accounts, reviews, job metadata, and content artifacts; store it only in BAIF-approved encrypted storage. The support bundle excludes credentials, source/translated content, artifacts, and model weights. Inspect it before sharing.

## Restore and upgrade

Stop the worker, preserve the current `outputs` folder, verify the backup, then run `python scripts/operations.py restore BACKUP.zip --force` and `python scripts/operations.py migrate`. Restart and perform the UAT smoke path. Never restore an unknown ZIP.
