# Demo Runbook

Last reviewed: 1 September 2026

This is the single operating script for the 30-minute implementation review on 9 September 2026. Keep the live path core-first, local, and time-boxed. Use only public, synthetic, or organiser-approved content on the event device.

## Event-device rules

- Use the organiser-provided Windows 11 laptop only for the hackathon demonstration.
- Obtain organiser approval before installing the documented Python, Microsoft C++ Build Tools, FFmpeg, Git, Tesseract or eSpeak NG prerequisites. Do not change security policy to bypass a restriction.
- Connect only to the HSBC Guest network or the presenter's hotspot when setup connectivity is required. Never use corporate Wi-Fi, wired LAN, HSBC systems, or confidential/customer data.
- Copy only required demo files by USB. Never leave the drive unattended; remove it immediately after transfer and take it away after the demo.
- Do not leave personal credentials signed in. Save files temporarily, transfer only what must be retained, and delete the application, models, outputs, caches, and temporary content before returning the device.
- The team owns technical troubleshooting. Bring the verified team laptop, power adapter, final deck, release ZIP, and offline evidence as the screen-share fallback.

## Two-hour setup window

1. Confirm written approval for the software list, then follow [Setup](SETUP.md) from a clean Windows 11 account.
2. Run `python scripts/demo_smoke_test.py --full`. Stop if any required check is false.
3. Start with `scripts/start_baif_worker.ps1`; confirm only `127.0.0.1:8501` is in use and the browser shows **Ready to translate**.
4. Confirm the balanced profile, one approved demo account, at least 20 GB free disk, and no runtime model download or hosted translation route.
5. Open the final deck and verify the prepared public-video evidence, backup walkthrough, and offline package without internet.
6. Close unrelated apps, notifications, personal sessions, terminals, and browser tabs. Keep one clean application tab and the deck ready.

## Recommended 30-minute run of show

| Time | Action | Presenter focus |
| --- | --- | --- |
| 0:00–2:00 | Problem and users | BAIF prepares learning content at the office; farmers and field teams need accurate Hindi, Marathi, or English material that remains usable offline. |
| 2:00–4:00 | Readiness and architecture | Show the local worker, CPU profile, supported languages, human review, and offline export boundary. |
| 4:00–8:00 | Live English → Hindi text | Use `samples/demo_agriculture.txt`. Point out input validation, agricultural terminology, preserved numbers/units, timing, and model provenance. |
| 8:00–11:00 | Review and approve | Correct only if needed, save, and approve the visible text. Explain that machine output is a draft and approval is versioned. |
| 11:00–13:00 | Exact reuse | Submit the identical source again. Show the approved local result returning without another model run; VaaniSetu never performs fuzzy automatic reuse. |
| 13:00–16:00 | Take content offline | Download the package, open `CONTENTS.html`, show captions/media links and checksums, then disconnect network if permitted. |
| 16:00–18:00 | Realistic media evidence | Show the prepared public-video result and privacy-safe BAIF validation evidence. Do not live-process a multi-minute video on CPU. Explain visible stage progress and expected CPU latency. |
| 18:00–23:00 | Product differentiation and evidence | Use the final slides: BAIF workflow, durable library, failure handling, test evidence, deployment, handover, and honest limitations. |
| 23:00–28:00 | Panel questions | Keep answers tied to implemented evidence; do not claim benchmark superiority or bilingual approval. |
| 28:00–30:00 | Buffer | Recover from a slow screen share or open the prepared evidence path. Do not add an untested feature. |

## Safest live input

Use a short synthetic agricultural sentence containing a number and unit, for example:

> Apply 25 kg of compost per acre before using pesticide.

Select English → Hindi, subtitles on, and speech off for the fastest path. A full BAIF video is deliberately not the live centrepiece: CPU transcription and media encoding are real, useful capabilities, but their latency is unsuitable for an 18-minute demonstration window.

## Prepared evidence path

- Public fixture: `outputs/demo_assets/Agriculture_First.webm` — 239.501 seconds, 600×480, 16,491,593 bytes.
- Source/licence: Wikimedia Commons, CC BY 3.0, attribution Indian Diplomacy.
- Verified flow: local Whisper → local NLLB CTranslate2 INT8 → Hindi text/SRT/VTT/speech/video → integrity ZIP.
- Machine-readable evidence: `outputs/demo_e2e_report.json`.
- Backup walkthrough: `outputs/VaaniSetu_Backup_Walkthrough.mp4`.

This proves engineering completion, not bilingual acceptance. Use the release report for private BAIF-video completion evidence; do not copy BAIF source media or generated content into the public repository or event screenshots.

## Recovery cards

| Failure | Recovery |
| --- | --- |
| Event laptop setup is blocked | Use the verified team laptop through screen share; show the release evidence and offline package. |
| Worker or model is unavailable | Show the actionable readiness error, then use the prepared walkthrough and package. Never switch to a hosted translator. |
| Live job is unexpectedly slow | Leave it queued, explain the visible stages, and open the completed evidence. |
| Low disk | Stop; archive or clean old jobs. VaaniSetu rejects the job before creating partial output. |
| Worker restart | Restart once. Interrupted work becomes an explicit recoverable failure; completed history remains. |
| Package is changed | Run the checksum verifier; tampering or injected files must fail verification. |
| Field internet is absent | Extract the package and open `CONTENTS.html`; the field recipient does not need VaaniSetu. |

Run the six deterministic engineering drills with `python scripts/failure_drill.py`.

## Defensible Bhashini answer

Bhashini is a broad Indian-language model and API ecosystem. VaaniSetu does not claim a more accurate foundation model without a controlled benchmark. Its differentiation is the BAIF-specific operating workflow around local processing: input limits, visible provenance, agricultural review prompts, human approval, exact approved reuse, durable history, failure recovery, and integrity-checked offline field packages. Bhashini is the stronger fit when national language breadth or hosted API integration is the priority; VaaniSetu is designed for controlled office-to-field content operations and can adopt an approved future model adapter.

## After the demo

1. Transfer only approved evidence that must be retained.
2. Sign out of VaaniSetu, Git hosting, email, and every other application.
3. Delete the repository, models, runtime outputs, downloads, caches, and temporary files created for the demo.
4. Remove the USB drive, disconnect from the network, close the browser, and return the device to the organisers.
5. Confirm no credentials or BAIF/HSBC data remain.

## Stop/go rule

Proceed only when [Acceptance](ACCEPTANCE.md) is green for the chosen device and the fallback path has been opened successfully. Call the build a verified release candidate until Windows 11 acceptance, authorised production-model inventory, and Hindi/Marathi reviewer sign-off are evidenced.
