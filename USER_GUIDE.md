# Trainer User Guide

For a first session, open the [BAIF onboarding runbook](BAIF_ONBOARDING_RUNBOOK.html) and follow **Trainer or reviewer: first translation**. The signed-in workspace also shows a state-aware **Start here** checklist until the worker, account and first completed translation are ready.

1. Open the VaaniSetu address provided by the administrator. Request access if needed; wait for approval, then sign in.
2. Choose source and target languages. Auto-detect is available for text/documents, not audio/video.
3. Use **Record**, **Text**, or **Upload**. For video, optionally request captioned or translated-audio output.
4. Keep the page open while the job runs. **Cancel** requests a safe stop at the next processing boundary.
5. Review warnings, original text, and translation. Download the package for immediate offline use.
6. In **Human review**, correct the translation, save the correction, and approve the final version. Approval creates a separate version and may enable exact local reuse.
7. Use **Reusable library** to search/open previous jobs, run one again, download, or delete it.

The three-step indicator keeps the core journey visible: **Translate → Review → Take offline**. The result's **Translation trust information** shows the local translation route, worker profile, processing time and human-review state. Treat machine output as a draft until a reviewer approves it.

For text, VaaniSetu detects seeded agriculture terms before processing and shows the expected target-language wording. The glossary is an engineering aid, not bilingual approval. While editing a correction, open the difference panel to see changed words highlighted before saving.

## Translate a batch

In **Upload**, select up to ten files together and choose **Translate selected**. VaaniSetu processes them sequentially to protect the CPU-only worker. The batch panel keeps success/failure status and a **Review** action for every completed file. **Cancel** stops the active item and prevents later batch items from starting.

## Show impact without exposing content

Open **Impact and reuse** to see completed jobs, media minutes, success rate, approvals, approved reuse, artifacts, language directions and storage. **Download impact report** creates a JSON report containing aggregate counts only—never source or translated text.
Do not distribute unreviewed health/safety/pesticide instructions. If a job fails, retain the original input, note the displayed recovery action, and contact the administrator without emailing confidential content.

Offline recipients unzip the package and open `CONTENTS.html`. Its links open every document and its built-in players run packaged audio/video without internet or a VaaniSetu server. An administrator can verify it with `python scripts/verify_package.py PACKAGE.zip`.
