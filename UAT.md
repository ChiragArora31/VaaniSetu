# User Acceptance Tests

Record pass/fail, tester, date, browser, release commit, evidence path, and issue ID for every case.

## Trainer

- Sign in as an approved user; verify an unapproved user cannot process/download.
- Translate one text and one representative DOCX/PDF; review warnings and all outputs.
- Record a voice note and upload short audio/video; verify transcript, translation, subtitles, optional speech/video, and actionable failure states.
- Correct and approve a translation; submit the exact source again and confirm visible approved-memory provenance. Repeat with memory disabled.
- Search by filename/language/status; open, run again, cancel a queued job, and delete a disposable job.

## Administrator

- Complete preflight, approve/deactivate a user, view metrics, and confirm route enforcement.
- Restart during a disposable job and confirm it becomes safely retryable.
- Preview cleanup; create a backup, restore it to a test output directory, migrate, and verify accounts/reviews.
- Generate and inspect a support bundle; confirm no source, translation, credentials, or weights appear.

## Field recipient

- Disconnect from the VaaniSetu server/network, unzip a package, open `CONTENTS.html`, and play/open every claimed artifact.
- Verify the ZIP checksum manifest; corrupt a disposable copy and confirm verification fails.
- Check long Hindi/Marathi copy on a phone-sized screen and keyboard-only operation on desktop.
