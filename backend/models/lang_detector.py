"""
Language detection module.

Uses `langdetect` to identify the language of input text and map it to the
appropriate HuggingFace toxicity model.

Usage
-----
from models.lang_detector import detect_language, get_model_for_language

lang_code, confidence = detect_language("Dit is een voorbeeldzin")
model_name = get_model_for_language(lang_code)
"""

from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not installed — language detection disabled. Install with: pip install langdetect")

# ── Language → Model mapping ──────────────────────────────────────────────────

# Model constants
MULTILINGUAL_MODEL = "gravitee-io/distilbert-multilingual-toxicity-classifier"

# Maps ISO 639-1 language codes to HuggingFace model names.
LANGUAGE_MODEL_MAP: dict[str, str] = {
    "en": "unitary/toxic-bert",        # English (best accuracy, multi-label)
    "ur": MULTILINGUAL_MODEL,          # Urdu (via Hindi/Arabic overlap in multilingual model)
    "hi": MULTILINGUAL_MODEL,          # Hindi
    "ar": MULTILINGUAL_MODEL,          # Arabic
    "fr": MULTILINGUAL_MODEL,          # French
    "de": MULTILINGUAL_MODEL,          # German
    "es": MULTILINGUAL_MODEL,          # Spanish
    "zh": MULTILINGUAL_MODEL,          # Chinese
    "ja": MULTILINGUAL_MODEL,          # Japanese
    "ru": MULTILINGUAL_MODEL,          # Russian
    "pt": MULTILINGUAL_MODEL,          # Portuguese
    "it": MULTILINGUAL_MODEL,          # Italian
    "nl": MULTILINGUAL_MODEL,          # Dutch
}

# Fallback: multilingual model for ALL unmapped languages
DEFAULT_MODEL = MULTILINGUAL_MODEL

# Confidence threshold — below this we fall back to the default model
CONFIDENCE_THRESHOLD = 0.5


def detect_language(text: str) -> tuple[str, float]:
    """
    Detect the language of the input text.

    Returns:
        (lang_code, confidence) — e.g. ("en", 0.95)
        Returns ("en", 0.0) if detection fails or langdetect is unavailable.
    """
    if not LANGDETECT_AVAILABLE:
        return ("en", 0.0)

    if not text or len(text.strip()) < 3:
        return ("en", 0.0)

    try:
        results = detect_langs(text)
        if results:
            best = results[0]  # e.g. "en:0.95"
            lang_code = best.lang
            confidence = best.prob
            logger.debug("Detected language: %s (%.2f)", lang_code, confidence)
            return (lang_code, confidence)
    except Exception as exc:
        logger.debug("Language detection failed: %s", exc)

    return ("en", 0.0)


def get_model_for_language(lang_code: str, confidence: float = 1.0) -> str:
    """
    Return the HuggingFace model name best suited for the given language.

    Falls back to DEFAULT_MODEL if:
    - confidence is below CONFIDENCE_THRESHOLD
    - the language has no mapped model
    """
    if confidence < CONFIDENCE_THRESHOLD:
        logger.debug(
            "Low confidence (%.2f) for lang '%s' — using default model",
            confidence, lang_code,
        )
        return DEFAULT_MODEL

    model = LANGUAGE_MODEL_MAP.get(lang_code)
    if model:
        logger.debug("Using model '%s' for language '%s'", model, lang_code)
        return model

    logger.debug("No model mapped for language '%s' — using default", lang_code)
    return DEFAULT_MODEL


def get_supported_languages() -> dict[str, str]:
    """Return a dict of supported language codes and their model names."""
    return dict(LANGUAGE_MODEL_MAP)
