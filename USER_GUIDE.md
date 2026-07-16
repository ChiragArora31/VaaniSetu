# Trainer User Guide

1. Open the VaaniSetu address provided by the administrator. Request access if needed; wait for approval, then sign in.
2. Choose source and target languages. Auto-detect is available for text/documents, not audio/video.
3. Use **Record**, **Text**, or **Upload**. For video, optionally request captioned or translated-audio output.
4. Keep the page open while the job runs. **Cancel** requests a safe stop at the next processing boundary.
5. Review warnings, original text, and translation. Download the package for immediate offline use.
6. In **Human review**, correct the translation, save the correction, and approve the final version. Approval creates a separate version and may enable exact local reuse.
7. Use **Reusable library** to search/open previous jobs, run one again, download, or delete it.

Do not distribute unreviewed health/safety/pesticide instructions. If a job fails, retain the original input, note the displayed recovery action, and contact the administrator without emailing confidential content.

Offline recipients unzip the package, open `CONTENTS.html`, and use the listed files. An administrator can verify it with `python scripts/verify_package.py PACKAGE.zip`.
