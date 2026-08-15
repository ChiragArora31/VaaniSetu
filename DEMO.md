# Demo Guide

Last reviewed: 15 August 2026

Use this as the single judge-demo script. The prepared path uses public, non-confidential agriculture content and cached local models.

## Before the room

1. Start the worker with `scripts/start_baif_worker.ps1` on Windows or `python -m uvicorn app:app --host 127.0.0.1 --port 8501` elsewhere.
2. Confirm `System: Ready to translate`, one admin account, at least 20 GB free disk, and hosted translation/model downloads disabled.
3. Keep [the final deck](submission/VaaniSetu_Final_Hackathon_Deck.pptx), `outputs/VaaniSetu_Submission_Candidate.zip`, and the prepared demo package available offline.
4. Open `samples/demo_agriculture.txt`; set **English → Hindi** and leave optional speech off for the fastest live path.
5. Never promise IndicTrans2 approval, bilingual acceptance, or Windows proof until the named external evidence exists.

## 3½-minute judge path

| Time | Show | Say |
| --- | --- | --- |
| 0:00–0:30 | Slide 1 | BAIF translates in Pune, but learning must remain usable in the field without internet. VaaniSetu is the controlled bridge, not a one-off translator. |
| 0:30–1:10 | Paste the sample and translate | One authenticated, CPU-only local worker accepts text, recordings, documents, audio and video. Limits and language checks happen before expensive processing. |
| 1:10–1:45 | Trust card and glossary | The backend, timing, script/invariant checks and agricultural terminology are visible. Machine output is explicitly a draft. |
| 1:45–2:20 | Human review; edit if useful; **Approve final** | Approval atomically saves exactly what is visible, versions it and creates an auditable approved package. |
| 2:20–2:45 | Translate the same source again | Exact approved content returns from local translation memory in under a second; model guesses are never used for fuzzy reuse. |
| 2:45–3:10 | Download package; open `CONTENTS.html` | Text, captions, speech/video and checksums travel together and open without VaaniSetu or field internet. |
| 3:10–3:30 | Slides 4–5 | Close on evidence: 74 tests, 20 adversarial regressions, six directions, full media limits, and only three clearly named external gates. |

## Prepared public video proof

- Input: `outputs/demo_assets/Agriculture_First.webm` — 239.501 seconds, 600×480, 16,491,593 bytes.
- Source and licence: Wikimedia Commons, **CC BY 3.0**, attribution **Indian Diplomacy**.
- Verified flow: local Whisper → NLLB CTranslate2 INT8 → Hindi text/SRT/VTT/speech/video → integrity ZIP.
- Latest machine-readable evidence: `outputs/demo_e2e_report.json`.

The public video is a repeatable engineering/demo fixture. It is not a bilingual quality approval sample.

## Backup path

If the live worker is slow or unavailable:

1. Continue from the final deck.
2. Play `outputs/VaaniSetu_Backup_Walkthrough.mp4`.
3. Open the prepared verified ZIP and its server-free `CONTENTS.html`.
4. Show the real-model screenshot and `outputs/quality_report.json`; do not switch to a hosted translator.

## Failure cards

| Failure | Expected response |
| --- | --- |
| Model unavailable | Actionable local setup message; content is not sent elsewhere. |
| Low disk | Job rejected before partial job directories are created; administrator archives or cleans old jobs. |
| Cancel pressed | Cancellation wins the completion race and becomes durable. |
| Worker restart | Interrupted jobs become explicit recoverable failures; completed history remains. |
| ZIP changed | Checksum verification rejects tampering or injected files. |
| Field internet absent | Extracted package and `CONTENTS.html` continue to work offline. |

Run all six with `python scripts/failure_drill.py`.

## Likely judge questions

- **Why one worker?** It bounds memory on BAIF's CPU baseline and makes queue/recovery behaviour predictable.
- **How is quality handled?** Invariant/script/glossary checks expose risk; human correction and approval remain authoritative.
- **What scales?** More trainers share the managed worker and queue; approved exact translations remove repeated model work. A second worker is a measured deployment decision, not an accidental fork.
- **Why no cloud API?** BAIF content stays on the configured worker, avoids paid licences and remains operable with cached models.
- **What is unfinished?** Only authorised IndicTrans2 caching/terms, Hindi/Marathi sign-off, and clean Windows 11 baseline acceptance.

## Stop/go rule

Submit when the engineering checks in `ACCEPTANCE.md` are green. A production acceptance claim is allowed only after all external gates are evidenced; until then call this a verified release candidate.
