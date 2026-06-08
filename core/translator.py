"""Offline translation adapters.

Primary backend: IndicTrans2 through Hugging Face Transformers with local or
downloaded model directories. A tiny phrasebook backend is kept only for
explicit offline installation validation.
"""

from __future__ import annotations

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
    TRANSLATION_BACKEND,
    TRANSLATION_BATCH_SIZE,
)


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
        self._cache: dict[str, tuple[object, object, object]] = {}
        self.allow_model_download = allow_model_download

    def _load(self, direction: str):
        if direction in self._cache:
            return self._cache[direction]
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

        self._cache[direction] = (tokenizer, model, processor)
        return self._cache[direction]

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
                with torch.no_grad():
                    generated = model.generate(
                        **inputs,
                        use_cache=True,
                        min_length=0,
                        max_length=512,
                        num_beams=5,
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
    path is useful for a no-key hosted fallback in this local build.
    """

    _codes = {
        "English": "en",
        "Hindi": "hi",
        "Marathi": "mr",
    }

    def __init__(self, provider: str = HOSTED_TRANSLATION_PROVIDER):
        self.provider = provider

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
                translated.append(translated_text.strip() or text)
            except TranslationError:
                raise
            except Exception as exc:
                raise TranslationError("Hosted translation service is temporarily unavailable.") from exc

        return TranslationResult(text="\n".join(translated), backend=f"hosted-{self.provider}")


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
                "Setup preview phrasebook was used. This is not production translation. "
                "Install the local IndicTrans2 model for real output."
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
        self.hosted = HostedHttpTranslator()
        self.preview = PreviewPhrasebookTranslator()
        self.allow_preview = allow_preview

    def translate_many(self, texts: list[str], source_name: str, target_name: str) -> TranslationResult:
        try:
            return self.indictrans.translate_many(texts, source_name, target_name)
        except TranslationError as exc:
            indic_error = exc
            if ENABLE_HOSTED_TRANSLATION:
                try:
                    return self.hosted.translate_many(texts, source_name, target_name)
                except TranslationError:
                    pass
            if not self.allow_preview:
                raise TranslationError(
                    "The provider translation backend is temporarily unavailable. Please try again in a moment."
                ) from indic_error
            fallback = self.preview.translate_many(texts, source_name, target_name)
            detail = str(indic_error).strip()
            warning = fallback.warning or "Setup preview phrasebook was used."
            if detail:
                warning = f"{warning} IndicTrans2 was unavailable: {detail}"
            return TranslationResult(text=fallback.text, backend=fallback.backend, warning=warning)


def translate_text(
    text: str,
    source_name: str,
    target_name: str,
    allow_preview: bool = False,
    allow_model_download: bool = ALLOW_MODEL_DOWNLOAD,
) -> TranslationResult:
    return get_translator(allow_preview, allow_model_download).translate_many([text], source_name, target_name)


def translate_segments(
    texts: list[str],
    source_name: str,
    target_name: str,
    allow_preview: bool = False,
    allow_model_download: bool = ALLOW_MODEL_DOWNLOAD,
) -> TranslationResult:
    return get_translator(allow_preview, allow_model_download).translate_many(texts, source_name, target_name)
