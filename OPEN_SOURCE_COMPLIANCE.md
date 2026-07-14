# Open-Source Compliance

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

## Deployment rule

The final judged deployment must use local copies of these open-source models on the BAIF worker. Free third-party translation APIs are not an acceptable substitute for the judged quality path because their underlying models, availability, and data handling cannot be independently guaranteed.

NLLB is currently retained as an ungated local engineering and resilience fallback. Its checkpoint is licensed CC-BY-NC-4.0, so it must not be presented as the final unrestricted open-source submission model unless BAIF confirms that license is acceptable. The intended judged translation path is the MIT-licensed IndicTrans2 checkpoint set.

## Quality rule

Do not describe output quality as best-in-class without a reproducible evaluation. Run:

```bash
pip install -r requirements-quality.txt
python scripts/evaluate_quality.py
```

Expand `benchmarks/translation_seed.jsonl` with BAIF-reviewed sentences, dialects, names, agricultural terminology, and noisy field recordings before final judging.
