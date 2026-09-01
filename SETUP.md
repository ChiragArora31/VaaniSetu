# Windows Setup and Handover

Audience: release testers, BAIF IT administrators, trainers and reviewers

Release state: candidate until every go/no-go item in this guide passes

Target: Windows 11, 16 GB RAM, six or more CPU cores, 20 GB free disk, CPU-only

This is the zero-to-ready path for a new VaaniSetu worker. Follow it in order. Do not use real BAIF content until the automated acceptance check passes. Do not publish screenshots, transcripts, translations, model tokens or BAIF videos.

On an organiser-provided hackathon laptop, obtain approval for every prerequisite before installation. Use only the HSBC Guest network or the presenter's hotspot, public/synthetic/approved data, and the minimum required USB files. Do not alter security settings. Follow the teardown in [Demo](DEMO.md) before returning the device.

## 1. Record the acceptance identity

Fill this before setup:

| Field | Value |
| --- | --- |
| Tester | |
| Date/time | |
| Computer make/model | |
| Windows edition/build | |
| RAM / CPU / free disk | |
| VaaniSetu commit | |
| BAIF video folder | |
| Hindi reviewer | |
| Marathi reviewer | |

Keep the generated `outputs\windows_acceptance` folder with the private release evidence. It excludes video/transcript/translation content, but it still belongs in BAIF-approved storage.

## 2. Prepare the computer from zero

1. Sign in with a Windows account allowed to install Python, Microsoft C++ Build Tools, FFmpeg and Tesseract.
2. Connect to the controlled office internet and power.
3. Install 64-bit Python 3.11 from python.org. In the installer, enable the Python launcher. Python 3.10 is supported if 3.11 is unavailable; do not use 3.9, 3.12 or 3.13. Install Git for Windows as well; it is used to prove the exact source release.
4. Install [Microsoft C++ Build Tools](https://learn.microsoft.com/en-us/cpp/overview/acquire-msvc?view=msvc-170). In the Visual Studio Installer, select **Desktop development with C++** and retain its recommended MSVC x64/x86 compiler and Windows SDK components. This compiler is required to build IndicTransToolkit; installing only the Visual C++ Redistributable does not provide it.
5. Close and reopen PowerShell, then confirm:

   ```powershell
   py -0p
   py -3.11 --version  # or: py -3.10 --version
   git --version
   $VsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
   & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
   ```

   The last command must print a Visual Studio or Build Tools installation path. If it prints nothing, open Visual Studio Installer, choose **Modify**, add **Desktop development with C++**, and rerun the check.

6. Copy or extract the release into a simple local path such as `C:\VaaniSetu`. Do not use OneDrive, a public sync folder, Downloads shared by multiple users, or a path controlled by an untrusted account.
7. Keep the BAIF test videos outside the repository, for example `C:\BAIF-Test-Data\Videos`. Never add them to Git or the submission ZIP.

If PowerShell blocks project scripts, stop and ask the device owner or BAIF IT for the approved execution method. Do not change execution policy or other security settings on a shared Hackathon laptop.

## 3. Install VaaniSetu and its local models

Open PowerShell in the VaaniSetu folder:

```powershell
cd C:\VaaniSetu
.\scripts\setup_baif_worker.ps1
```

The script selects Python 3.11/3.10, creates the private `.venv`, installs pinned packages, caches OCR languages and downloads the balanced CPU model set. It does not silently install system software. If approved prerequisites are missing, install them through the device owner's approved method; only after explicit approval may an administrator rerun `.\scripts\setup_baif_worker.ps1 -InstallApprovedSystemTools` to request FFmpeg, Git and Tesseract through Windows Package Manager. The balanced set uses multilingual large-v3-turbo INT8: it completed the real 5:43 BAIF sample end to end on the engineering Mac while the previous large-v3/beam-3 default did not. Downloads can take a long time; do not close the window.

The script checks the C++ compiler before any large installation starts. If it reports `Microsoft Visual C++ 14.0 or greater is required` or says that C++ Build Tools are missing, install/modify the Build Tools workload described in section 2, reopen PowerShell and rerun the same setup command. A failed run may leave `.venv`; rerunning is safe and resumes the installation.

### IndicTrans2 access

The authorised team account must first accept the access conditions for the three balanced IndicTrans2 repositories named by `config\model_manifest.json`. If setup reports that any IndicTrans2 model is unavailable:

```powershell
.\.venv\Scripts\hf.exe auth login
.\.venv\Scripts\python.exe scripts\setup_models.py --profile balanced --with-translation
.\.venv\Scripts\python.exe scripts\convert_nllb_ct2.py
```

Paste the authorised Hugging Face token only into the hidden CLI prompt. Do not put it in a command, screenshot, `.env`, support bundle, chat or Git. Sign out/remove the cached credential after model setup if BAIF policy requires it.

Close and reopen PowerShell once after Windows Package Manager installs FFmpeg or Tesseract, then return to `C:\VaaniSetu`. This refreshes the command path.

## 4. Run the automated Windows acceptance gate

Stop VaaniSetu if it is already running; port 8501 must be free. Then run:

```powershell
.\scripts\windows_acceptance.ps1 -VideosPath "C:\BAIF-Test-Data\Videos"
```

This performs dependency integrity, 78 automated tests, repository/privacy policy, production preflight, model inventory and all-video compatibility checks. It writes:

- `outputs\windows_acceptance\acceptance_summary.json`
- `outputs\windows_acceptance\acceptance.log`
- `outputs\windows_acceptance\machine.json`
- `outputs\windows_acceptance\preflight_report.json`
- `outputs\windows_acceptance\model_inventory.json`
- `outputs\windows_acceptance\baif_sample_validation.json`

Expected result: every check says `PASSED` and `acceptance_summary.json` says `"status": "passed"`. Preflight requires the balanced large-v3-turbo ASR model, all configured IndicTrans2 directions, local translation, FFmpeg/ffprobe, OCR, 16 GB RAM, 20 GB free disk, hosted translation off and runtime model downloads off. A failed preflight is a stop signal, not a warning to ignore. Correct the named issue and rerun the entire command.

The supplied BAIF set should report 8/8 compatible videos, about 70.55 minutes total, with audio and 1920×1080 video streams. A different count or hash means the tester must confirm which approved set was supplied; do not silently substitute files.

## 5. Start safely

For testing on the same computer:

```powershell
.\scripts\start_baif_worker.ps1
```

Open `http://127.0.0.1:8501`. Keep the PowerShell window open. Press `Ctrl+C` once to stop safely.

For an IT-approved private BAIF LAN only:

```powershell
.\scripts\start_baif_worker.ps1 -HostAddress 0.0.0.0
```

Use the computer's approved private IP address from other BAIF devices. Do not expose port 8501 to the public internet. BAIF IT must provide firewall rules and TLS/reverse-proxy controls before routine LAN use.

## 6. Create accounts and prove access control

1. The first browser user creates the administrator account with a unique password of at least 10 characters.
2. In a private/incognito window, a trainer chooses **Request access** and creates a separate account.
3. Confirm the pending trainer cannot translate or download.
4. The administrator opens **User approvals** and approves the trainer.
5. The trainer signs in successfully.
6. The administrator deactivates a disposable test user and confirms its session loses access.

Never share the administrator account for routine work.

## 7. Run the short functional journey

Use non-confidential text first:

> Apply 25 kg of compost per acre and call 1800-123-456 before using pesticide.

1. Choose **English → Hindi**, open **Text**, paste the sentence and translate.
2. Confirm `25 kg` and `1800-123-456` are preserved and the trust card names a local backend.
3. Read every warning. Machine output must be shown as a draft.
4. Correct the translation, inspect the difference and choose **Approve final**.
5. Submit the exact source again and confirm the approved local reuse provenance.
6. Download the approved ZIP and record its job ID.

## 8. Run the real BAIF video journey

The technical probe indicates Marathi speech, but a Marathi reviewer must confirm the source language. Audio/video intentionally does not auto-detect because a wrong source choice harms transcription.

Start with the shortest supplied file, `401.1.mp4` (about 5 minutes 43 seconds):

1. Choose **Marathi → Hindi**.
2. Open **Upload** and select `401.1.mp4` from the external BAIF test-data folder.
3. For the first pass, keep subtitles on and optional speech, caption burn-in and translated-audio video off. This isolates ASR + translation + offline packaging.
4. Start translation and leave the page open. The balanced multilingual large-v3-turbo profile is CPU-bounded but a long video can still take several minutes; use the visible stage, elapsed time and ETA instead of assuming the page is stuck. Record start/end time, peak memory from Task Manager, job ID, warnings, ASR backend and translation backend.
5. Ask the Marathi reviewer to compare representative transcript sections against the audio. Ask the Hindi reviewer to assess adequacy, fluency, agriculture/livestock terminology, names, numbers, units and safety meaning.
6. Correct and approve only after review. Download the ZIP.
7. Repeat with `401.2 HOUSING OF GOAT.mp4` because its topic and title are directly relevant to livestock training.
8. After the core passes, run one optional captioned-video or translated-speech job and record the extra time. Optional media failure must leave usable text/SRT/VTT outputs.

Do not paste BAIF transcript or translation content into public issues, screenshots or the privacy-safe acceptance folder. Reviewer worksheets must stay in approved private storage.

## 9. Prove the field package offline

On a disposable copy of the approved ZIP:

```powershell
.\.venv\Scripts\python.exe scripts\verify_package.py "C:\path\to\vaanisetu_outputs.zip"
```

Then disconnect the test device from the VaaniSetu server/network, extract the ZIP and open `CONTENTS.html`. Open every claimed text/subtitle/audio/video link. Corrupt one disposable copy and confirm the verifier rejects it. Never use a package with a checksum error.

## 10. Prove recovery and operations

Run from the project folder while the worker is stopped:

```powershell
.\.venv\Scripts\python.exe scripts\operations.py cleanup --days 7 --dry-run
.\.venv\Scripts\python.exe scripts\operations.py backup backups\acceptance-backup.zip
.\.venv\Scripts\python.exe scripts\operations.py support-bundle outputs\windows_acceptance\support.zip
```

Inspect the dry run before cleanup. Store backups only in BAIF-approved encrypted storage. Confirm the support ZIP contains preflight and redacted events only—no account records, source, transcript, translation, artifacts, tokens or model weights.

For restore testing, use a disposable copy of the runtime storage, never the sole live copy:

```powershell
.\.venv\Scripts\python.exe scripts\operations.py restore backups\acceptance-backup.zip --force
.\.venv\Scripts\python.exe scripts\operations.py migrate
```

Restart and repeat the short text journey.

## 11. Final go/no-go

Ship for controlled BAIF UAT only when every item is checked:

- [ ] `windows_acceptance.ps1` passes with no ignored failure.
- [ ] The release commit and generated machine/model/preflight evidence are recorded.
- [ ] All 8 approved BAIF videos pass compatibility checks.
- [ ] `401.1.mp4` completes ASR, translation, subtitles and verified offline packaging on Windows.
- [ ] Hindi and Marathi reviewers record findings; no unresolved critical meaning, number, unit, name or safety error remains.
- [ ] Text correction, approval and exact approved reuse pass.
- [ ] The field package opens without the server/network and checksum tampering is rejected.
- [ ] Account request, approval, deactivation and sign-in boundaries pass.
- [ ] Restart/retry, backup, disposable restore, cleanup dry run and support bundle pass.
- [ ] No BAIF data, credentials or model weights are present in Git/submission/public evidence.
- [ ] BAIF administrator, reviewer, backup owner and first-line support owner are named.

Any unchecked item is either a release blocker or an explicitly documented limitation with an owner and decision. Do not describe the build as production-approved until the Windows run and bilingual review are signed.

## 12. Handover ownership and routine

| Frequency | Owner | Action |
| --- | --- | --- |
| Before each session | Administrator | Start worker, open **System**, confirm readiness and free disk. |
| Every job | Trainer/reviewer | Read warnings, review consequential content, approve only the final correction. |
| Daily during active use | Administrator | Review failures/queue, archive required packages, stop worker safely. |
| Weekly | Backup owner | Create encrypted backup; verify a disposable package; preview retention cleanup. |
| Monthly or before upgrade | BAIF IT | Record commit/model inventory, test restore/rollback, apply approved updates only. |
| Model/glossary change | Language owner + IT | Re-run representative quality cases and record approval before rollout. |
| Incident | First-line support | Preserve job ID/time/release/preflight; create redacted support bundle; follow BAIF incident policy. |

Recovery and administration are covered in `OPERATIONS.md`; complete test personas are in `ACCEPTANCE.md`. The browser-served printable guide is available at `/onboarding` after VaaniSetu starts.
