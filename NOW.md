# VaaniSetu — Now

**Status: verified release candidate · 28 July 2026**

## The idea in one sentence

VaaniSetu helps authorised BAIF trainers turn English, Hindi and Marathi learning material into reviewed, reusable packages that work offline in the field—using BAIF's existing CPU-only office infrastructure and open-source software.

## Where we are

The complete product workflow and internal submission work are finished. The implementation, QA, repository and submission consolidation have so far been driven by Chirag; the best use of the full team now is to close the three external acceptance gates and sharpen delivery.

| Area | Current position |
| --- | --- |
| Product | Complete trainer journey: translate → inspect trust signals → correct/approve → reuse → take offline |
| Inputs | Text, recording, PDF/scanned PDF, Office/table files, audio and video |
| Outputs | Text, SRT/VTT, optional speech/video and checksum-protected offline ZIP |
| Reliability | 69 automated tests, including 20 adversarial regressions; CI and clean-install rehearsal pass |
| Real proof | CPU translation in 43.8s; approved reuse in 0.6s; four-minute public video processed in 120s |
| Submission | Final five-slide deck, 3½-minute demo, backup walkthrough and evidence bundle are ready |

## Why the direction is strong

- It follows the organiser's actual operating model: translation in Pune, offline playback in the field.
- It is designed for the stated Windows 11, 16 GB RAM, CPU-only environment—no GPU or paid API assumption.
- Quality is a workflow, not a vague model claim: invariants, target-script checks, agriculture terminology, visible provenance and human approval are built in.
- Exact approved translations can be reused locally, saving time without unsafe fuzzy matching.
- Edge cases are treated as product behaviour: corrupt state, low disk, cancellation races, restarts and tampered packages fail safely.

## What remains

There is no deferred internal engineering or submission task. Three external gates separate this release candidate from an unrestricted production claim:

1. **Model acceptance:** an authorised account must accept, cache and inventory the intended IndicTrans2 checkpoints.
2. **Language acceptance:** qualified Hindi and Marathi reviewers must sign representative outputs and terminology.
3. **Target-machine acceptance:** a clean BAIF-spec Windows 11 machine must pass setup, preflight, media processing and UAT.

If BAIF later supplies approved sample material, we will replace the public fixture. The release tag and BAIF IT knowledge transfer follow only after the three gates above.

The goal now is not to add decorative scope. It is to convert a strong, tested product into undeniable evidence on the exact environment and quality bar the judges will use.

Start here: [final deck](submission/VaaniSetu_Final_Hackathon_Deck.pptx) · [demo runbook](SUBMISSION_RUNBOOK.md) · [evidence](TEST_EVIDENCE.md) · [roadmap](IMPLEMENTATION_ROADMAP.md)
