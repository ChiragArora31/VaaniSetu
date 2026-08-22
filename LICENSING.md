# Licensing

VaaniSetu's judged production path uses models and software that can be run on provider-owned infrastructure without paid APIs or per-request usage fees.

| Capability | Preferred production component | License |
| --- | --- | --- |
| Speech recognition | AI4Bharat IndicConformer or faster-whisper | MIT |
| Translation | AI4Bharat IndicTrans2 model checkpoints | MIT |
| Translation evaluation fallback | Meta NLLB-200 distilled 600M | CC-BY-NC-4.0; non-commercial restriction |
| CPU inference runtime | CTranslate2 | MIT |
| High-quality speech | AI4Bharat Indic Parler TTS | Apache-2.0 |
| Lightweight speech | Piper | MIT |
| Compact speech fallback | eSpeak NG | GPL-3.0 |
| Media processing | FFmpeg | LGPL/GPL depending on build |
| API | FastAPI | MIT |

## Major software inventory

| Area | Components | Declared licence |
| --- | --- | --- |
| Web/API | FastAPI, Pydantic | MIT |
| ASGI/runtime | Starlette, Uvicorn, httpx2 | BSD-3-Clause |
| Local model execution | faster-whisper, CTranslate2 | MIT |
| Model framework | Transformers, Hugging Face Hub | Apache-2.0 |
| Tensor runtime | PyTorch | BSD-3-Clause |
| PDF/OCR plumbing | pypdf 6.15.0, pypdfium2 | BSD-3-Clause; pypdfium2 also carries dependency notices |
| Media/Python | PyAV | BSD-3-Clause |
| Images | Pillow | MIT-CMU |
| HTTP | Requests | Apache-2.0 |
| Indic processing | IndicTransToolkit, indic-nlp-library | MIT |
| Optional inference/evaluation | ONNX Runtime, SacreBLEU | MIT; Apache-2.0 |

The complete installed Python inventory is generated as `outputs/release_evidence/python_sbom.cdx.json`; source/model origins and required revisions are recorded in `config/model_manifest.json`. FFmpeg licence depends on the selected build, so BAIF IT must retain the notice supplied with the installed binary.

## Deployment rule

The final judged deployment must use local copies of these open-source models on the BAIF worker. Free third-party translation APIs are not an acceptable substitute for the judged quality path because their underlying models, availability, and data handling cannot be independently guaranteed.

NLLB is currently retained as an ungated local engineering and resilience fallback. Its checkpoint is licensed CC-BY-NC-4.0, so it must not be presented as the final unrestricted open-source submission model unless BAIF confirms that license is acceptable. The intended judged translation path is the MIT-licensed IndicTrans2 checkpoint set.

Security scanning on 22 August 2026 found and fixed the applicable pypdf 6.14.2 issues by pinning 6.15.0. Remaining advisories affect the pinned PyTorch/Transformers model toolchain or a setuptools version newer than PyTorch 2.12 permits. VaaniSetu mitigates those paths by accepting no user-supplied models/checkpoints, using fixed locally provisioned model directories and disabling normal runtime downloads. They still require a compatibility-tested post-demo upgrade; this is mitigation, not a claim that the advisories do not exist.

## Quality rule

Do not describe output quality as best-in-class without a reproducible evaluation. Run:

```bash
pip install -r requirements-quality.txt
python scripts/evaluate_quality.py
```

The checked-in six-direction seed is an engineering corpus. Add reviewer-approved BAIF-style sentences, dialects, names, agricultural terminology and noisy field recordings before final judging; do not alter predictions merely to pass the gate.
