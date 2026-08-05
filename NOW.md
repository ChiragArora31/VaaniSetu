# VaaniSetu — Now

**Project update · 28 July 2026**

## What we are building

VaaniSetu is a local translation workspace for BAIF training material. It helps a trainer translate English, Hindi and Marathi content, review and correct the result, reuse approved translations, and export a package that can be played offline in the field.

The design follows the constraints shared by the organisers: translation happens at BAIF's Pune office, the application runs on an existing Windows 11 CPU-only machine, and the software stack is open source.

## What works today

| Area | Current state |
| --- | --- |
| Input | Text, microphone recordings, documents, audio and video are supported |
| Translation | English, Hindi and Marathi workflows run locally, with source-language detection and terminology support |
| Review | Users can inspect warnings and provenance, edit translations, approve them and reuse exact approved results |
| Output | The app produces translated text, SRT/VTT subtitles, optional speech/video and an offline ZIP with checksums |
| Operations | Jobs can be cancelled, resumed after restart, deleted safely and diagnosed through health/preflight checks |
| Submission | A five-slide deck, demo runbook, backup walkthrough and test evidence are prepared |

## What we have verified

- The automated suite has 71 passing tests, including 20 tests for malformed inputs, boundary conditions, race conditions and recovery paths.
- A clean installation rehearsal and GitHub CI pass.
- A real four-minute public agriculture video completed the local transcription, translation, subtitle, audio and packaging workflow on CPU.
- All six English/Hindi/Marathi translation directions have been benchmarked; the results and known quality limits are recorded in the repository.
- The stated 30-minute audio and 15-minute 1080p input boundaries have been exercised.

These checks make the project suitable for a controlled demo and evaluation. They do not replace review by native speakers or validation on BAIF's exact machine.

## Where we are heading

The product workflow and submission materials are in place. The next step is to validate the same build under the conditions that will matter in final use:

1. Cache and verify the intended IndicTrans2 models through an authorised account.
2. Ask qualified Hindi and Marathi reviewers to assess representative translations and terminology.
3. Run installation, preflight, media processing and user acceptance testing on a clean BAIF-spec Windows 11 machine.

If BAIF provides approved sample material, we will run it through the same review process and include the results in the evidence pack. The final release tag and handover material should follow these checks.

## Current position

We have a working, tested release candidate and a clear path to final acceptance. The remaining work depends mainly on access to the approved models, language reviewers and target BAIF environment; until those checks are complete, we should describe the project as demo-ready rather than fully production-approved.

More detail: [final deck](submission/VaaniSetu_Final_Hackathon_Deck.pptx) · [demo runbook](SUBMISSION_RUNBOOK.md) · [test evidence](TEST_EVIDENCE.md) · [roadmap](IMPLEMENTATION_ROADMAP.md)
