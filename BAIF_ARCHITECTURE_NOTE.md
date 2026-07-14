# BAIF Architecture Note

## Recommended Delivery Model

VaaniSetu should be delivered as a local/on-prem open-source model worker with a browser UI.

This means BAIF installs the versioned Python environment, media/OCR tools, and approved model assets once on an office workstation or LAN server. Users open a web interface on that same machine or office network. The worker performs document extraction, transcription, translation, speech synthesis, subtitle generation, and packaging.

## Why This Fits The Hackathon Constraints

The Q&A clarification says internet is available at BAIF premises for installation and translation, but not guaranteed in the field. This points to a central translation workflow:

- Install/cache open-source models once on BAIF's available infrastructure.
- Run translation at the BAIF office or another approved provider machine.
- Export translated documents, audio, subtitles, text, and ZIP bundles.
- Share generated outputs for offline field playback.

That is exactly what the current API/UI architecture supports.

## Internet Use

Internet can be used in two legitimate places:

1. Setup time: download open-source model weights and Python packages.
2. Runtime at BAIF premises: submit and process translation jobs on the local/on-prem worker. User jobs do not silently download models or call hosted translation services.

Internet should not be required for field playback after outputs are generated.

## Why Not Install Everything On Every User Machine

Per-user installation on every phone/laptop would create avoidable problems:

- Low-spec laptops and phones may not run speech and translation models reliably.
- Model versions could drift across devices, making output quality inconsistent.
- Setup would require technical support for Python, FFmpeg, model paths, and storage.
- Large model downloads would repeat unnecessarily.

The better architecture is one managed model worker plus a simple browser interface for everyone else. This still counts as locally installed model execution when the worker runs on BAIF premises or a BAIF-approved machine.

## Quality Path

The judged production path should use locally hosted, license-approved model checkpoints:

- Speech-to-text: benchmark AI4Bharat IndicConformer against faster-whisper large-v3 on BAIF-style audio.
- Translation: AI4Bharat IndicTrans2 for English, Hindi, and Marathi.
- Text-to-speech: AI4Bharat Indic Parler TTS for natural speech, with Piper or eSpeak NG as CPU-friendly fallbacks.
- Media handling: FFmpeg.
- Documents: built-in Office XML extraction, pypdf for selectable PDFs, and automatic local PDFium/Tesseract OCR for scanned PDFs.

Convenience hosted fallbacks are acceptable for demos only when clearly marked in the job report and UI warnings. They should not be used as evidence of final quality.

## Deployment Shapes

### Local BAIF Worker

Use this when BAIF has one Windows/Linux workstation or server available at the office.

```bash
python scripts/one_click_setup.py --profile balanced
python -m uvicorn api:app --host 0.0.0.0 --port 8501
```

Users then open the web app from the office network.

### Provider-Managed Worker

Use this when the team operates the model service for BAIF.

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8501
```

The provider manages model caching, logs, updates, and benchmarking. Users still only need the browser.

## Submission Positioning

The strongest claim is not that VaaniSetu avoids all internet. The stronger and more accurate claim is:

VaaniSetu runs open-source models on a local/on-prem worker for quality and reproducibility, keeps normal BAIF users dependency-light through a browser UI, uses BAIF-premises internet for setup and translation when needed, and produces offline-ready artifacts for field use.
