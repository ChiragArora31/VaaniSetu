# Troubleshooting

| Symptom | Safe recovery |
| --- | --- |
| Translation model not ready | Stop accepting production jobs, accept/cache the required IndicTrans2 assets during controlled setup, rerun preflight, keep runtime downloads disabled. |
| OCR unavailable | Install Tesseract with `eng`, `hin`, and `mar` data; confirm preflight. Use a selectable-text PDF meanwhile. |
| No speech detected | Confirm the file has audible spoken voice, choose the spoken language, and retry with a short clean sample. |
| Voice output missing | Review/download text and subtitles; install Indic Parler/Piper/eSpeak and rerun preflight. |
| Worker disk is low | Back up/archive required packages, preview cleanup, then clean stale temporary files. Do not manually remove `.auth` or `.reviews`. |
| Job interrupted after restart | The durable queue marks it failed instead of silently resuming; use **Run again** after readiness is restored. |
| Package will not open | Run the package verifier. Redownload if any checksum fails. Never ignore a mismatch. |
| Port 8501 is busy | Stop the old worker or choose an approved alternate port; do not start competing model workers. |
| Repeated sign-in failures | Wait for the throttle window; verify the account is active. An admin may deactivate/reapprove as policy permits. |

For escalation, generate a privacy-safe support bundle and include the app release, preflight result, time of failure, job ID, and recovery already attempted—never the confidential source file unless BAIF explicitly authorises secure transfer.
