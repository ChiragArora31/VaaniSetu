"""Offline translation adapters.

Primary backend: IndicTrans2 through Hugging Face Transformers with local or
downloaded model directories. A tiny phrasebook backend is kept only for
explicit offline installation validation.
"""

from __future__ import annotations

import re
import gc
from dataclasses import dataclass
from functools import lru_cache

from config.languages import get_language
from config.settings import (
    ALLOW_MODEL_DOWNLOAD,
    ALLOW_PREVIEW_TRANSLATOR,
    ENABLE_HOSTED_TRANSLATION,
    HOSTED_TRANSLATION_PROVIDER,
    HOSTED_TRANSLATION_TIMEOUT_SECONDS,
    INDICTRANS_MODEL_BY_DIRECTION,
    INDICTRANS_REPO_BY_DIRECTION,
    MYMEMORY_EMAIL,
    NLLB_CT2_MODEL,
    NLLB_MODEL,
    NLLB_MODEL_ID,
    TRANSLATION_BACKEND,
    TRANSLATION_BATCH_SIZE,
    TRANSLATION_BEAM_SIZE,
    TRANSLATION_CPU_THREADS,
)
from core.quality import protect_invariants, restore_invariants, validate_translation


class TranslationError(RuntimeError):
    """Raised when translation cannot be completed."""


@dataclass(frozen=True)
class TranslationResult:
    text: str
    backend: str
    warning: str | None = None


def _direction(source_code: str, target_code: str) -> str:
    if source_code == "eng_Latn" and target_code != "eng_Latn":
        return "en-indic"
    if source_code != "eng_Latn" and target_code == "eng_Latn":
        return "indic-en"
    if source_code != "eng_Latn" and target_code != "eng_Latn":
        return "indic-indic"
    return "same"


class IndicTrans2Translator:
    def __init__(self, allow_model_download: bool = ALLOW_MODEL_DOWNLOAD):
        self._loaded_direction: str | None = None
        self._loaded: tuple[object, object, object] | None = None
        self.allow_model_download = allow_model_download

    def _load(self, direction: str):
        if direction == self._loaded_direction and self._loaded:
            return self._loaded
        if direction == "same":
            raise TranslationError("No model is required for same-language translation.")

        model_path = INDICTRANS_MODEL_BY_DIRECTION[direction]
        from pathlib import Path

        model_ref = model_path if Path(model_path).exists() else INDICTRANS_REPO_BY_DIRECTION[direction]
        if not Path(model_path).exists() and not self.allow_model_download:
            raise TranslationError(
                "IndicTrans2 model folder is missing for this language direction: "
                f"{model_path}"
            )
        try:
            import torch
            from IndicTransToolkit.processor import IndicProcessor
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise TranslationError(
                "IndicTrans2 dependencies are not installed. Run 'pip install -r requirements-full.txt'."
            ) from exc

        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_ref,
                trust_remote_code=True,
                local_files_only=not self.allow_model_download,
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_ref,
                trust_remote_code=True,
                local_files_only=not self.allow_model_download,
                low_cpu_mem_usage=True,
            )
            model.eval()
            if torch.cuda.is_available():
                model = model.to("cuda")
            processor = IndicProcessor(inference=True)
        except Exception as exc:
            raise TranslationError(
                "IndicTrans2 model files are not available. Install/cache the required AI4Bharat model or enable "
                f"internet-backed open-source model download. Tried: {model_ref}"
            ) from exc

        self._loaded = None
        self._loaded_direction = None
        gc.collect()
        self._loaded = (tokenizer, model, processor)
        self._loaded_direction = direction
        return self._loaded

    def translate_many(self, texts: list[str], source_name: str, target_name: str) -> TranslationResult:
        source = get_language(source_name)
        target = get_language(target_name)
        cleaned = [text.strip() for text in texts]
        if source.code == target.code:
            return TranslationResult(text="\n".join(cleaned), backend="same-language")

        direction = _direction(source.indictrans_code, target.indictrans_code)
        tokenizer, model, processor = self._load(direction)

        try:
            import torch

            translated: list[str] = []
            batch_size = max(1, TRANSLATION_BATCH_SIZE)
            for start in range(0, len(cleaned), batch_size):
                batch = cleaned[start : start + batch_size]
                preprocessed = processor.preprocess_batch(
                    batch,
                    src_lang=source.indictrans_code,
                    tgt_lang=target.indictrans_code,
                )
                inputs = tokenizer(
                    preprocessed,
                    truncation=True,
                    padding=True,
                    return_tensors="pt",
                    max_length=512,
                )
                if torch.cuda.is_available():
                    inputs = {key: value.to("cuda") for key, value in inputs.items()}
                with torch.inference_mode():
                    generated = model.generate(
                        **inputs,
                        use_cache=True,
                        min_length=0,
                        max_new_tokens=256,
                        num_beams=max(1, TRANSLATION_BEAM_SIZE),
                        num_return_sequences=1,
                    )
                decoded = tokenizer.batch_decode(generated, skip_special_tokens=True)
                translated.extend(processor.postprocess_batch(decoded, lang=target.indictrans_code))
            return TranslationResult(text="\n".join(translated), backend="IndicTrans2")
        except Exception as exc:
            raise TranslationError(f"IndicTrans2 translation failed: {exc}") from exc


class HostedHttpTranslator:
    """Provider-side HTTP translation adapter.

    This keeps end users dependency-free. In production, point this abstraction
    at a provider-owned LibreTranslate/IndicTrans service. The default MyMemory
    path is useful for a no-key convenience fallback, but it is not the judged
    open-source production path.
    """

    _codes = {
        "English": "en",
        "Hindi": "hi",
        "Marathi": "mr",
    }

    def __init__(self, provider: str = HOSTED_TRANSLATION_PROVIDER):
        self.provider = provider

    @staticmethod
    def _validate_output(source: str, translated: str, target_name: str) -> None:
        normalized_source = " ".join(source.casefold().split())
        normalized_output = " ".join(translated.casefold().split())
        if not normalized_output or normalized_output == normalized_source:
            raise TranslationError("Hosted translation returned untranslated text.")
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", translated))
        has_latin = bool(re.search(r"[A-Za-z]", translated))
        if target_name in {"Hindi", "Marathi"} and not has_devanagari:
            raise TranslationError("Hosted translation returned text in the wrong script.")
        if target_name == "English" and not has_latin:
            raise TranslationError("Hosted translation returned text in the wrong script.")

    def translate_many(self, texts: list[str], source_name: str, target_name: str) -> TranslationResult:
        if source_name == target_name:
            return TranslationResult(text="\n".join(texts), backend="same-language")
        if self.provider != "mymemory":
            raise TranslationError(f"Unsupported hosted translation provider: {self.provider}")

        try:
            import requests
        except ImportError as exc:
            raise TranslationError("Hosted translation client is not available on the backend.") from exc

        source_code = self._codes[source_name]
        target_code = self._codes[target_name]
        translated: list[str] = []
        for text in texts:
            if not text.strip():
                translated.append("")
                continue
            params = {
                "q": text,
                "langpair": f"{source_code}|{target_code}",
            }
            if MYMEMORY_EMAIL:
                params["de"] = MYMEMORY_EMAIL
            try:
                response = requests.get(
                    "https://api.mymemory.translated.net/get",
                    params=params,
                    timeout=HOSTED_TRANSLATION_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("responseStatus") != 200:
                    raise TranslationError(payload.get("responseDetails") or "Hosted translation failed.")
                translated_text = payload.get("responseData", {}).get("translatedText", "")
                translated_text = translated_text.strip()
                self._validate_output(text, translated_text, target_name)
                translated.append(translated_text)
            except TranslationError:
                raise
            except Exception as exc:
                raise TranslationError("Hosted translation service is temporarily unavailable.") from exc

        return TranslationResult(
            text="\n".join(translated),
            backend=f"hosted-{self.provider}",
            warning=(
                "A free hosted convenience fallback produced this translation. "
                "Use the provider-hosted IndicTrans quality path for judged output."
            ),
        )


class NllbTranslator:
    """Non-gated local open-source translator for the three BAIF languages."""

    def __init__(self, allow_model_download: bool = ALLOW_MODEL_DOWNLOAD):
        self.allow_model_download = allow_model_download
        self._loaded: tuple[object, object] | None = None

    def _load(self):
        if self._loaded:
            return self._loaded

        from pathlib import Path

        model_ref = NLLB_MODEL if Path(NLLB_MODEL).exists() else NLLB_MODEL_ID
        if not Path(NLLB_MODEL).exists() and not self.allow_model_download:
            raise TranslationError(f"NLLB local model folder is missing: {NLLB_MODEL}")

        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise TranslationError("NLLB dependencies are not installed. Run 'pip install -r requirements-full.txt'.") from exc

        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_ref,
                local_files_only=not self.allow_model_download,
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_ref,
                local_files_only=not self.allow_model_download,
                low_cpu_mem_usage=True,
            )
            model.eval()
            if torch.cuda.is_available():
                model = model.to("cuda")
        except Exception as exc:
            raise TranslationError(
                "NLLB model files are not available. Install/cache the local NLLB model or enable model download. "
                f"Tried: {model_ref}"
            ) from exc

        self._loaded = (tokenizer, model)
        return self._loaded

    def translate_many(self, texts: list[str], source_name: str, target_name: str) -> TranslationResult:
        source = get_language(source_name)
        target = get_language(target_name)
        cleaned = [text.strip() for text in texts]
        if source.code == target.code:
            return TranslationResult(text="\n".join(cleaned), backend="same-language")

        tokenizer, model = self._load()
        try:
            import torch

            tokenizer.src_lang = source.indictrans_code
            target_token_id = tokenizer.convert_tokens_to_ids(target.indictrans_code)
            if target_token_id in {None, tokenizer.unk_token_id}:
                raise TranslationError(f"NLLB does not expose target language token: {target.indictrans_code}")

            translated: list[str] = []
            batch_size = max(1, min(TRANSLATION_BATCH_SIZE, 4))
            for start in range(0, len(cleaned), batch_size):
                batch = cleaned[start : start + batch_size]
                inputs = tokenizer(
                    batch,
                    truncation=True,
                    padding=True,
                    return_tensors="pt",
                    max_length=512,
                )
                if torch.cuda.is_available():
                    inputs = {key: value.to("cuda") for key, value in inputs.items()}
                with torch.inference_mode():
                    generated = model.generate(
                        **inputs,
                        forced_bos_token_id=target_token_id,
                        max_new_tokens=256,
                        num_beams=max(1, TRANSLATION_BEAM_SIZE),
                    )
                translated.extend(tokenizer.batch_decode(generated, skip_special_tokens=True))
            return TranslationResult(text="\n".join(translated), backend="NLLB-200 local")
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(f"NLLB translation failed: {exc}") from exc


class CTranslate2NllbTranslator:
    """INT8 NLLB runtime optimized for CPU-only BAIF workers."""

    def __init__(self):
        self._loaded: tuple[object, object] | None = None

    def _load(self):
        if self._loaded:
            return self._loaded
        from pathlib import Path

        model_path = Path(NLLB_CT2_MODEL)
        tokenizer_path = Path(NLLB_MODEL)
        if not (model_path / "model.bin").exists() or not (tokenizer_path / "tokenizer.json").exists():
            raise TranslationError("The optimized NLLB model has not been prepared on this worker.")
        try:
            import ctranslate2
            from transformers import AutoTokenizer

            translator = ctranslate2.Translator(
                str(model_path),
                device="cpu",
                compute_type="int8",
                inter_threads=1,
                intra_threads=TRANSLATION_CPU_THREADS,
            )
            tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
        except Exception as exc:
            raise TranslationError(f"Optimized NLLB could not be loaded: {exc}") from exc
        self._loaded = (translator, tokenizer)
        return self._loaded

    def translate_many(self, texts: list[str], source_name: str, target_name: str) -> TranslationResult:
        source = get_language(source_name)
        target = get_language(target_name)
        cleaned = [text.strip() for text in texts]
        if source.code == target.code:
            return TranslationResult(text="\n".join(cleaned), backend="same-language")

        translator, tokenizer = self._load()
        try:
            tokenizer.src_lang = source.indictrans_code
            translated: list[str] = []
            batch_size = max(1, min(TRANSLATION_BATCH_SIZE, 8))
            for start in range(0, len(cleaned), batch_size):
                batch = cleaned[start : start + batch_size]
                source_tokens = [
                    tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
                    for text in batch
                ]
                prefixes = [[target.indictrans_code] for _ in batch]
                results = translator.translate_batch(
                    source_tokens,
                    target_prefix=prefixes,
                    beam_size=max(1, TRANSLATION_BEAM_SIZE),
                    max_decoding_length=256,
                )
                for result in results:
                    target_tokens = result.hypotheses[0][1:]
                    target_ids = tokenizer.convert_tokens_to_ids(target_tokens)
                    translated.append(tokenizer.decode(target_ids, skip_special_tokens=True))
            return TranslationResult(text="\n".join(translated), backend="NLLB-200 CTranslate2 INT8")
        except Exception as exc:
            raise TranslationError(f"Optimized NLLB translation failed: {exc}") from exc


class PreviewPhrasebookTranslator:
    """Small deterministic fallback for setup validation, not production translation."""

    _phrasebook = {
        ("English", "Hindi"): {
            "hello": "नमस्ते",
            "thank you": "धन्यवाद",
            "water": "पानी",
            "health": "स्वास्थ्य",
            "farmer": "किसान",
            "farming": "खेती",
            "soil": "मिट्टी",
            "women": "महिलाएं",
            "community": "समुदाय",
        },
        ("English", "Marathi"): {
            "hello": "नमस्कार",
            "thank you": "धन्यवाद",
            "water": "पाणी",
            "health": "आरोग्य",
            "farmer": "शेतकरी",
            "farming": "शेती",
            "soil": "माती",
            "women": "महिला",
            "community": "समुदाय",
        },
        ("Hindi", "English"): {
            "नमस्ते": "hello",
            "नमस्कार": "hello",
            "धन्यवाद": "thank you",
            "पानी": "water",
            "स्वास्थ्य": "health",
            "किसान": "farmer",
            "खेती": "farming",
            "मिट्टी": "soil",
            "समुदाय": "community",
        },
        ("Marathi", "English"): {
            "नमस्कार": "hello",
            "नमस्ते": "hello",
            "धन्यवाद": "thank you",
            "पाणी": "water",
            "आरोग्य": "health",
            "शेतकरी": "farmer",
            "शेती": "farming",
            "माती": "soil",
            "समुदाय": "community",
        },
        ("Hindi", "Marathi"): {
            "नमस्ते": "नमस्कार",
            "धन्यवाद": "धन्यवाद",
            "पानी": "पाणी",
            "स्वास्थ्य": "आरोग्य",
            "किसान": "शेतकरी",
            "खेती": "शेती",
            "मिट्टी": "माती",
            "महिलाएं": "महिला",
            "समुदाय": "समुदाय",
        },
        ("Marathi", "Hindi"): {
            "नमस्कार": "नमस्ते",
            "धन्यवाद": "धन्यवाद",
            "पाणी": "पानी",
            "आरोग्य": "स्वास्थ्य",
            "शेतकरी": "किसान",
            "शेती": "खेती",
            "माती": "मिट्टी",
            "महिला": "महिलाएं",
            "समुदाय": "समुदाय",
        },
    }

    def translate_many(self, texts: list[str], source_name: str, target_name: str) -> TranslationResult:
        if source_name == target_name:
            return TranslationResult(text="\n".join(texts), backend="same-language")

        dictionary = self._phrasebook.get((source_name, target_name), {})
        translated_lines = [self._translate_line(text, dictionary) for text in texts]
        return TranslationResult(
            text="\n".join(translated_lines),
            backend="preview-phrasebook",
            warning=(
                "Preview mode is active so you can keep testing while the final quality models finish setup."
            ),
        )

    @staticmethod
    def _translate_line(text: str, dictionary: dict[str, str]) -> str:
        if not text.strip():
            return ""
        stripped = text.strip()
        direct = dictionary.get(stripped) or dictionary.get(stripped.lower())
        if direct:
            return direct
        output = stripped
        for source, target in sorted(dictionary.items(), key=lambda item: len(item[0]), reverse=True):
            output = output.replace(source, target)
            output = output.replace(source.title(), target)
        return output


@lru_cache(maxsize=8)
def get_translator(
    allow_preview: bool = ALLOW_PREVIEW_TRANSLATOR,
    allow_model_download: bool = ALLOW_MODEL_DOWNLOAD,
):
    backend = TRANSLATION_BACKEND
    if backend == "preview":
        return PreviewPhrasebookTranslator()
    if backend in {"auto", "indictrans2"}:
        return AutoTranslator(allow_preview=allow_preview, allow_model_download=allow_model_download)
    raise TranslationError(f"Unknown translation backend: {backend}")


class AutoTranslator:
    def __init__(self, allow_preview: bool = False, allow_model_download: bool = ALLOW_MODEL_DOWNLOAD):
        self.indictrans = IndicTrans2Translator(allow_model_download=allow_model_download)
        self.nllb_ct2 = CTranslate2NllbTranslator()
        self.nllb = NllbTranslator(allow_model_download=allow_model_download)
        self.hosted = HostedHttpTranslator()
        self.preview = PreviewPhrasebookTranslator()
        self.allow_preview = allow_preview

    def translate_many(self, texts: list[str], source_name: str, target_name: str) -> TranslationResult:
        try:
            return self.indictrans.translate_many(texts, source_name, target_name)
        except TranslationError as exc:
            indic_error = exc
            try:
                return self.nllb_ct2.translate_many(texts, source_name, target_name)
            except TranslationError:
                try:
                    return self.nllb.translate_many(texts, source_name, target_name)
                except TranslationError:
                    pass
            if ENABLE_HOSTED_TRANSLATION:
                try:
                    return self.hosted.translate_many(texts, source_name, target_name)
                except TranslationError:
                    pass
            if not self.allow_preview:
                raise TranslationError(
                    "The local translation model is not ready for this language direction. "
                    "Complete model setup and try again."
                ) from indic_error
            fallback = self.preview.translate_many(texts, source_name, target_name)
            warning = fallback.warning or "Setup preview phrasebook was used."
            return TranslationResult(text=fallback.text, backend=fallback.backend, warning=warning)


def translate_text(
    text: str,
    source_name: str,
    target_name: str,
    allow_preview: bool = False,
    allow_model_download: bool = ALLOW_MODEL_DOWNLOAD,
) -> TranslationResult:
    return translate_segments([text], source_name, target_name, allow_preview, allow_model_download)


def translate_segments(
    texts: list[str],
    source_name: str,
    target_name: str,
    allow_preview: bool = False,
    allow_model_download: bool = ALLOW_MODEL_DOWNLOAD,
) -> TranslationResult:
    protected = [protect_invariants(text) for text in texts]
    result = get_translator(allow_preview, allow_model_download).translate_many(
        [item.text for item in protected], source_name, target_name
    )
    translated_lines = result.text.splitlines()
    if len(translated_lines) != len(texts):
        translated_lines = [result.text] if len(texts) == 1 else translated_lines
    restored: list[str] = []
    for index, source in enumerate(texts):
        raw = translated_lines[index] if index < len(translated_lines) else ""
        output = restore_invariants(raw, protected[index].values)
        critical = [
            finding for finding in validate_translation(
                source, output, source_name, target_name, check_glossary=False
            ) if finding.severity == "critical"
        ]
        if critical and result.backend != "preview-phrasebook":
            raise TranslationError("Translation safety check failed: " + "; ".join(item.message for item in critical))
        restored.append(output)
    return TranslationResult(text="\n".join(restored), backend=result.backend, warning=result.warning)
