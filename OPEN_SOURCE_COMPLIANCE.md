# Open-Source Compliance

VaaniSetu's judged production path uses models and software that can be run on provider-owned infrastructure without paid APIs or per-request usage fees.

| Capability | Preferred production component | License |
| --- | --- | --- |
| Speech recognition | AI4Bharat IndicConformer or faster-whisper | MIT |
| Translation | AI4Bharat IndicTrans2 model checkpoints | MIT |
| High-quality speech | AI4Bharat Indic Parler TTS | Apache-2.0 |
| Lightweight speech | Piper | MIT |
| Media processing | FFmpeg | LGPL/GPL depending on build |
| API | FastAPI | MIT |

## Deployment rule

The final judged deployment must use locally hosted or provider-hosted copies of these open-source models. Free third-party translation APIs are not an acceptable substitute for the judged quality path because their underlying models, availability, and data handling cannot be independently guaranteed.

## Quality rule

Do not describe output quality as best-in-class without a reproducible evaluation. Run:

```bash
pip install -r requirements-quality.txt
python scripts/evaluate_quality.py
```

Expand `benchmarks/translation_seed.jsonl` with BAIF-reviewed sentences, dialects, names, agricultural terminology, and noisy field recordings before final judging.
