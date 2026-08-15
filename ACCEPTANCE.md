# Acceptance Tests

Record pass/fail, tester, date, browser, release commit, evidence path, and issue ID for every case.

## Trainer

- Sign in as an approved user; verify an unapproved user cannot process/download.
- Translate one text and one representative DOCX/PDF; review warnings and all outputs.
- Record a voice note and upload short audio/video; verify transcript, translation, subtitles, optional speech/video, and actionable failure states.
- Correct and approve a translation; submit the exact source again and confirm visible approved-memory provenance. Repeat with memory disabled.
- Search by filename/language/status; open, run again, cancel a queued job, and delete a disposable job.
- On the final Windows worker, run BAIF `401.1.mp4` first with reviewer-confirmed Marathi source, Hindi target, subtitles on and optional speech/video off. Record timings, memory, backends, warnings and job ID; obtain Marathi transcript and Hindi translation review.
- Repeat the core path with `401.2 HOUSING OF GOAT.mp4`, then exercise one optional captioned-video or translated-speech output.

## Administrator

- Complete preflight, approve/deactivate a user, view metrics, and confirm route enforcement.
- Restart during a disposable job and confirm it becomes safely retryable.
- Preview cleanup; create a backup, restore it to a test output directory, migrate, and verify accounts/reviews.
- Generate and inspect a support bundle; confirm no source, translation, credentials, or weights appear.

## Field recipient

- Disconnect from the VaaniSetu server/network, unzip a package, open `CONTENTS.html`, and play/open every claimed artifact.
- Verify the ZIP checksum manifest; corrupt a disposable copy and confirm verification fails.
- Check long Hindi/Marathi copy on a phone-sized screen and keyboard-only operation on desktop.

## Release decision

Engineering verification is complete when compilation, frontend syntax, dependency integrity, repository policy, the automated test suite, failure drills and submission packaging all pass. Controlled BAIF deployment additionally requires every item below:

- [ ] Intended IndicTrans2 checkpoints are accepted, cached, inventoried and licence-confirmed.
- [ ] Hindi and Marathi reviewers approve representative terminology, transcript and translation samples.
- [ ] A supported Windows 11 CPU worker passes installation, preflight, media processing and all three acceptance personas.
- [x] All eight supplied BAIF videos pass privacy-safe format, size, duration, resolution and stream validation.
- [ ] The shortest supplied BAIF video completes the full local pipeline on the target worker and receives reviewer assessment.
- [ ] The final release tag, named operational owners and knowledge-transfer record are complete.

Do not convert an unchecked external item into an implied pass. Until these items are evidenced, describe the build as a verified release candidate ready for controlled acceptance testing.
