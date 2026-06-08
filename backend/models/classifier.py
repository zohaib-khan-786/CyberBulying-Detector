"""
CyberbullyingClassifier
Wraps either a trained sklearn LogisticRegression (fast, default) or a
HuggingFace transformer (RobBERT / bert-base-multilingual-uncased).

Usage
-----
clf = CyberbullyingClassifier(use_transformer=False)
clf.load()                    # loads from disk or downloads
result = clf.predict("text")  # → PredictionResult
"""

from __future__ import annotations

import os
import pickle
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, cast

from models.lang_detector import detect_language, get_model_for_language

logger = logging.getLogger(__name__)

LABELS = {
    0: "clean",
    1: "cyberbullying",
    2: "harassment",
    3: "hate_speech",
    4: "threat",
    5: "religious_hate",   # blasphemous / religiously sensitive content
}

LABEL_COLORS = {
    "clean":          "#22c55e",
    "cyberbullying":  "#f97316",
    "harassment":     "#ef4444",
    "hate_speech":    "#dc2626",
    "threat":         "#7f1d1d",
    "religious_hate": "#7c3aed",  # violet — visually distinct from hate_speech red
}

MODEL_DIR = Path(__file__).parent / "saved_models"
SKLEARN_PATH = MODEL_DIR / "lr_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.pkl"
BERT_FINETUNED_PATH = MODEL_DIR / "cyberbullying_bert"  # fine-tuned BERT from Colab


@dataclass
class PredictionResult:
    text: str
    label: str
    label_id: int
    confidence: float
    scores: dict          # label → probability
    is_harmful: bool
    severity: str         # "none" | "low" | "medium" | "high" | "critical"
    color: str
    trigger_words: List[str] = field(default_factory=list)
    detected_lang: str = "en"       # ISO 639-1 language code
    lang_confidence: float = 0.0    # language detection confidence

    def to_dict(self):
        return asdict(self)


def _severity(label: str, confidence: float) -> str:
    if label == "clean":
        return "none"
    if label == "threat":
        return "critical"
    if label in ("hate_speech", "religious_hate"):
        return "high" if confidence > 0.7 else "medium"
    if confidence > 0.85:
        return "high"
    if confidence > 0.6:
        return "medium"
    return "low"


class CyberbullyingClassifier:
    """
    Wraps sklearn (default) or HuggingFace transformer.
    Falls back to a rule-based heuristic if neither model is available —
    so the API always returns a result during development.
    """

    def __init__(self, use_transformer: bool = False):
        self.use_transformer: bool = use_transformer
        self.is_loaded: bool = False
        self.model_name: str = ""
        self._model: Any = None
        self._vectorizer: Any = None
        self._pipeline: Any = None
        self._lang_models: Dict[str, Any] = {}

    # ── Public ────────────────────────────────────────────────────────────────

    def load(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        if BERT_FINETUNED_PATH.exists() and (BERT_FINETUNED_PATH / "config.json").exists():
            self._load_finetuned_bert()
            self._lang_models = {"en": self._pipeline}
        elif self.use_transformer:
            self._load_transformer()
            self._lang_models = {"en": self._pipeline}

        if not self.is_loaded:
            self._lang_models = {}
            self._load_sklearn()

    def _get_pipeline_for_lang(self, lang_code: str):
        """Return pipeline for language — always uses the default model (no per-language loading)."""
        return self._pipeline

    def predict(self, text: str) -> PredictionResult:
        lang_code, lang_confidence = detect_language(text)

        if not self.is_loaded:
            result = self._heuristic_predict(text)
            result.detected_lang = lang_code
            result.lang_confidence = lang_confidence
            return result

        if BERT_FINETUNED_PATH.exists() and (BERT_FINETUNED_PATH / "config.json").exists():
            result = self._predict_finetuned_bert(text)
        elif self.use_transformer:
            result = self._predict_transformer(text, lang_code)
        else:
            result = self._predict_sklearn(text)

        if not result.is_harmful:
            heuristic = self._heuristic_predict(text)
            if heuristic.is_harmful:
                result = heuristic

        result.detected_lang = lang_code
        result.lang_confidence = lang_confidence
        return result

    def predict_batch(self, texts: List[str]) -> List[PredictionResult]:
        return [self.predict(t) for t in texts]

    # ── Loaders ───────────────────────────────────────────────────────────────

    def _load_sklearn(self):
        if SKLEARN_PATH.exists() and VECTORIZER_PATH.exists():
            with open(SKLEARN_PATH, "rb") as f:
                self._model = pickle.load(f)
            with open(VECTORIZER_PATH, "rb") as f:
                self._vectorizer = pickle.load(f)
            self.is_loaded = True
            logger.info("Sklearn model loaded from disk.")
        else:
            logger.warning(
                "Sklearn model not found at %s. "
                "Run `python ml_pipeline/train.py` to train. "
                "Using heuristic fallback.",
                SKLEARN_PATH,
            )

    def _predict_sklearn(self, text: str) -> PredictionResult:
        vec = self._vectorizer.transform([text])
        probs = self._model.predict_proba(vec)[0]
        pred = self._model.predict(vec)[0]
        label_id = int(pred)
        label = LABELS.get(label_id, "clean")
        confidence = float(max(probs))
        scores = {LABELS[i]: round(float(p), 4) for i, p in enumerate(probs)}
        for i in range(len(LABELS)):
            scores.setdefault(LABELS[i], 0.0)
        trigger_words = self._extract_trigger_words_sklearn(text, label_id) if label != "clean" else []
        return PredictionResult(
            text=text,
            label=label,
            label_id=label_id,
            confidence=round(confidence, 4),
            scores=scores,
            is_harmful=(label != "clean"),
            severity=_severity(label, confidence),
            color=LABEL_COLORS[label],
            trigger_words=trigger_words,
        )

    def _load_transformer(self):
        try:
            from transformers import pipeline as hf_pipeline
            self.model_name = os.getenv("HF_MODEL", "unitary/toxic-bert")
            token = os.getenv("HF_TOKEN")
            self._pipeline = hf_pipeline(
                "text-classification",
                model=self.model_name,
                token=token,
                top_k=None,
            )
            self.is_loaded = True
            logger.info("Transformer model '%s' loaded.", self.model_name)
        except Exception as exc:
            logger.error("Failed to load transformer: %s", exc)
            self.use_transformer = False

    def _load_finetuned_bert(self):
        """Load the fine-tuned BERT model trained in Colab."""
        try:
            from transformers import pipeline as hf_pipeline
            self.model_name = str(BERT_FINETUNED_PATH)
            self._pipeline = hf_pipeline(
                "text-classification",
                model=self.model_name,
                tokenizer=self.model_name,
                top_k=None,
            )
            self.is_loaded = True
            logger.info("Fine-tuned BERT model loaded from %s", BERT_FINETUNED_PATH)
        except Exception as exc:
            logger.error("Failed to load fine-tuned BERT: %s", exc)

    def _predict_finetuned_bert(self, text: str) -> PredictionResult:
        pipe = self._pipeline
        raw_output: Any = pipe(text[:512])
        if isinstance(raw_output, list) and len(raw_output) > 0 and isinstance(raw_output[0], list):
            results = cast(list[dict[str, Any]], raw_output[0])
        else:
            results = cast(list[dict[str, Any]], raw_output)

        scores_raw = {}
        for r in results:
            label_raw = str(r["label"]).lower()
            score = float(r["score"])
            if label_raw in ("LABEL_0", "label_0", "clean"):
                scores_raw["clean"] = score
            elif label_raw in ("LABEL_1", "label_1", "cyberbullying"):
                scores_raw["cyberbullying"] = score
            elif label_raw in ("LABEL_2", "label_2", "harassment"):
                scores_raw["harassment"] = score
            elif label_raw in ("LABEL_3", "label_3", "hate_speech"):
                scores_raw["hate_speech"] = score
            elif label_raw in ("LABEL_4", "label_4", "threat"):
                scores_raw["threat"] = score
            elif label_raw in ("LABEL_5", "label_5", "religious_hate"):
                scores_raw["religious_hate"] = score
            else:
                scores_raw[label_raw] = score

        for lbl in ("clean", "cyberbullying", "harassment", "hate_speech", "threat", "religious_hate"):
            scores_raw.setdefault(lbl, 0.0)

        best = max(results, key=lambda r: float(r["score"]))
        label_raw = str(best["label"]).lower()
        confidence = float(best["score"])

        label_map = {
            "LABEL_0": "clean", "label_0": "clean", "clean": "clean",
            "LABEL_1": "cyberbullying", "label_1": "cyberbullying", "cyberbullying": "cyberbullying",
            "LABEL_2": "harassment", "label_2": "harassment", "harassment": "harassment",
            "LABEL_3": "hate_speech", "label_3": "hate_speech", "hate_speech": "hate_speech",
            "LABEL_4": "threat", "label_4": "threat", "threat": "threat",
            "LABEL_5": "religious_hate", "label_5": "religious_hate", "religious_hate": "religious_hate",
        }
        label = label_map.get(label_raw, "clean")
        label_id = {v: k for k, v in LABELS.items()}.get(label, 0)
        scores = {k: round(v, 4) for k, v in scores_raw.items()}

        trigger_words = self._extract_trigger_words_bert(text, label, pipe) if label != "clean" else []

        return PredictionResult(
            text=text,
            label=label,
            label_id=label_id,
            confidence=round(confidence, 4),
            scores=scores,
            is_harmful=(label != "clean"),
            severity=_severity(label, confidence),
            color=LABEL_COLORS[label],
            trigger_words=trigger_words,
        )

    def _extract_trigger_words_transformer(self, text: str, label: str, pipeline: Any) -> List[str]:
        """Extract words via perturbation — remove each word and measure score drop."""
        words = text.split()
        if len(words) < 2 or len(words) > 20:
            return []
        import time
        try:
            baseline_raw = pipeline(text[:512])
            raw_b = baseline_raw[0] if isinstance(baseline_raw[0], list) else baseline_raw
            base_scores = {r["label"].lower(): float(r["score"]) for r in raw_b}

            # For threats, use threat score; for hate, use identity_hate; else use general toxic
            if label == "threat":
                baseline_toxic = base_scores.get("threat", base_scores.get("toxic", 0))
            elif label == "hate_speech":
                baseline_toxic = base_scores.get("identity_hate", base_scores.get("toxic", 0))
            else:
                baseline_toxic = base_scores.get("toxic",
                    max(s for k, s in base_scores.items() if k not in ("clean", "non-toxic", "not-toxic", "neutral", "normal", "obscene", "insult", "threat", "identity_hate", "severe_toxic")))

            triggers = []
            checked = 0
            for word in words:
                if checked >= 8:
                    break
                stripped = word.strip(".,!?;:\"'()[]{}")
                if len(stripped) < 2:
                    continue
                checked += 1
                modified = " ".join(w for w in words if w != word)
                if not modified.strip():
                    continue
                try:
                    result = pipeline(modified[:512])
                    raw2 = result[0] if isinstance(result[0], list) else result
                    scores2 = {r["label"].lower(): float(r["score"]) for r in raw2}

                    if label == "threat":
                        new_score = scores2.get("threat", scores2.get("toxic", 0))
                    elif label == "hate_speech":
                        new_score = scores2.get("identity_hate", scores2.get("toxic", 0))
                    else:
                        new_score = scores2.get("toxic",
                            max(s for k, s in scores2.items() if k not in ("clean", "non-toxic", "not-toxic", "neutral", "normal", "obscene", "insult", "threat", "identity_hate", "severe_toxic")))

                    drop = baseline_toxic - new_score
                    if drop > 0.03:
                        triggers.append((stripped.lower(), drop))
                except Exception:
                    continue

            triggers.sort(key=lambda x: x[1], reverse=True)
            return [w for w, _ in triggers[:5]]
        except Exception:
            return []

    def _extract_trigger_words_sklearn(self, text: str, label_id: int) -> List[str]:
        """Extract words/ngrams from text that most contribute to the predicted label."""
        if not hasattr(self._model, "coef_") or not hasattr(self._vectorizer, "get_feature_names_out"):
            return []
        feature_names = self._vectorizer.get_feature_names_out()
        coefs = self._model.coef_[label_id]
        top_indices = (-coefs).argsort()[:30]
        lower = text.lower()
        trigger_words = []
        for idx in top_indices:
            if coefs[idx] <= 0:
                continue
            feature = feature_names[idx]
            if feature in lower:
                trigger_words.append(feature)
                if len(trigger_words) >= 10:
                    break
        return trigger_words

    def _extract_trigger_words_bert(self, text: str, label: str, pipe: Any) -> List[str]:
        """Perturbation-based trigger word extraction for fine-tuned BERT."""
        words = text.split()
        if len(words) < 2 or len(words) > 20:
            if len(words) == 1 and len(words[0]) >= 2:
                return [words[0].strip(".,!?;:\"'()[]{}").lower()]
            return []

        LABEL_TO_MODEL_KEY = {
            "clean": ("clean", "label_0", "LABEL_0"),
            "cyberbullying": ("cyberbullying", "label_1", "LABEL_1"),
            "harassment": ("harassment", "label_2", "LABEL_2"),
            "hate_speech": ("hate_speech", "label_3", "LABEL_3"),
            "threat": ("threat", "label_4", "LABEL_4"),
            "religious_hate": ("religious_hate", "label_5", "LABEL_5"),
        }

        def _get_score(scores, model_keys, default=0):
            for k in model_keys:
                if k in scores:
                    return scores[k]
            return default

        model_keys = LABEL_TO_MODEL_KEY.get(label, (label,))

        try:
            base = pipe(text[:512])
            raw = base[0] if isinstance(base[0], list) else base
            base_scores = {r["label"].lower(): float(r["score"]) for r in raw}
            base_toxic = _get_score(base_scores, model_keys, 0)
            triggers = []
            checked = 0
            for word in words:
                if checked >= 8:
                    break
                stripped = word.strip(".,!?;:\"'()[]{}")
                if len(stripped) < 2:
                    continue
                checked += 1
                modified = " ".join(w for w in words if w != word)
                if not modified.strip():
                    continue
                try:
                    result = pipe(modified[:512])
                    raw2 = result[0] if isinstance(result[0], list) else result
                    scores2 = {r["label"].lower(): float(r["score"]) for r in raw2}
                    new_score = _get_score(scores2, model_keys, default=_get_score(scores2, ("toxic",), 0))
                    drop = base_toxic - new_score
                    if drop > 0.01:
                        triggers.append((stripped.lower(), drop))
                except Exception:
                    continue
            triggers.sort(key=lambda x: x[1], reverse=True)
            return [w for w, _ in triggers[:5]]
        except Exception:
            return []

    def _predict_transformer(self, text: str, lang_code: str = "en") -> PredictionResult:
        pipeline = self._get_pipeline_for_lang(lang_code)
        raw_output: Any = pipeline(text[:512])
        # With top_k=None, pipeline returns list-of-lists: [[{...}, {...}]]
        if isinstance(raw_output, list) and len(raw_output) > 0 and isinstance(raw_output[0], list):
            results: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_output[0])
        else:
            results = cast(list[dict[str, Any]], raw_output)

        # Map HF labels to our schema
        scores_raw: dict[str, float] = {}
        for r in results:
            lbl = r["label"].lower()
            scores_raw[lbl] = float(r["score"])

        best: dict[str, Any] = max(results, key=lambda r: float(r["score"]))
        label_raw: str = str(best["label"]).lower()
        confidence: float = float(best["score"])

        def _get_score(scores: dict, *keys: str, default: float = 0) -> float:
            for k in keys:
                if k in scores:
                    return scores[k]
            return default

        # Handle multi-label models (unitary/toxic-bert outputs: toxic, severe_toxic, obscene, insult, threat, identity_hate)
        _BINARY_LABELS = {"toxic", "non-toxic", "not-toxic", "toxicity", "neutral", "abusive", "normal"}
        _MULTI_SUB_LABELS = {"insult", "obscene", "threat", "identity_hate", "severe_toxic"}
        has_specific_labels = any(k in scores_raw for k in _MULTI_SUB_LABELS)

        if has_specific_labels:
            # Multi-label model — map sub-labels to best category
            threat_score  = _get_score(scores_raw, "threat", 0)
            hate_score    = _get_score(scores_raw, "identity_hate", 0)
            insult_score  = _get_score(scores_raw, "insult", 0)
            obscene_score = _get_score(scores_raw, "obscene", 0)
            toxic_score   = _get_score(scores_raw, "toxic", 0)
            severe_toxic  = _get_score(scores_raw, "severe_toxic", 0)

            # Prioritize specific sub-labels over generic "toxic"
            if threat_score > 0.5:
                label = "threat"
            elif hate_score > 0.3:
                label = "hate_speech"
            elif max(insult_score, obscene_score) > 0.5:
                label = "harassment"
            elif toxic_score > 0.3 or severe_toxic > 0.3:
                label = "cyberbullying"
            else:
                label = "clean"

            scores = {
                "clean": 1 - toxic_score if toxic_score < 1 else 0,
                "cyberbullying": max(toxic_score, severe_toxic),
                "harassment": max(insult_score, obscene_score),
                "hate_speech": hate_score,
                "threat": threat_score,
                "religious_hate": hate_score * 0.5,
            }
            confidence = max(v for k, v in scores.items() if k != "clean")
        elif label_raw in _BINARY_LABELS:
            # Binary model — just toxic vs non-toxic
            toxic_score = _get_score(scores_raw, "toxic", "toxicity", "abusive")
            is_toxic = toxic_score > 0.25
            label = "cyberbullying" if is_toxic else "clean"
            scores = {
                "clean": _get_score(scores_raw, "non-toxic", "not-toxic", "neutral", "normal", default=1 - toxic_score),
                "cyberbullying": toxic_score,
                "harassment": toxic_score * 0.3,
                "hate_speech": toxic_score * 0.2,
                "threat": toxic_score * 0.1,
                "religious_hate": toxic_score * 0.1,
            }
        elif "toxic" in label_raw:
            label = "cyberbullying"
            scores = scores_raw
        elif "hate" in label_raw:
            label = "hate_speech"
            scores = scores_raw
        elif "threat" in label_raw:
            label = "threat"
            scores = scores_raw
        elif "insult" in label_raw or "obscene" in label_raw:
            label = "harassment"
            scores = scores_raw
        else:
            label = "clean"
            scores = scores_raw

        label_id = {v: k for k, v in LABELS.items()}.get(label, 0)

        trigger_words = self._extract_trigger_words_transformer(text, label, pipeline) if label != "clean" else []
        return PredictionResult(
            text=text,
            label=label,
            label_id=label_id,
            confidence=round(confidence, 4),
            scores={k: round(v, 4) for k, v in scores.items()},
            is_harmful=(label != "clean"),
            severity=_severity(label, confidence),
            color=LABEL_COLORS[label],
            trigger_words=trigger_words,
        )

    def _heuristic_predict(self, text: str) -> PredictionResult:
        """
        Keyword-based fallback used when no model is trained yet.
        NOT suitable for production — train a real model first.
        """
        _TOXIC_WORDS = {
            # English
            "idiot", "stupid", "hate", "kill", "die", "ugly",
            "loser", "worthless", "moron", "dumb", "shut up",
            "fuck", "ass", "bitch", "damn", "crap", "hell",
            "shit", "trash", "garbage", "disgusting", "pathetic",
            # Dutch
            "idioot", "dom", "haat", "dood", "lelijk", "loser",
            "waardeloos", "mongool", "kanker", "tering", "lul",
            "tyfus", "cholera", "eikel", "eikel", "sukkel",
            # Urdu Roman
            "bewaqoof", "pagal", "kutta", "kamina", "harami",
            "badtameez", "jahil", "gandu", "ullu", "chutiya",
            "madarchod", "bhenchod", "randi", "saala", "bhosdi",
            "lund", "laude", "tatti", "gobar", "nikal",
            "marunga", "maarunga", "maronga", "marongi", "marenge", "maarenge",
            "mar dunga", "maar dunga", "mar dunga", "ghus",
            "tujhe", "teri", "joote", "maa ki", "behen ki",
            "kutte", "kutti", "sale", "sali", "saali", "rand",
            # Hindi Roman
            "madarchod", "bhenchod", "gandu", "chutiya", "bhosdi",
            "randi", "saala", "laude", "nikal", "haramkhor",
            "kamine", "bewakoof", "suar", "garda", "khotta",
            # Arabic Roman
            "klb", "hamar", "ghabni", "ahbal", "akhraf",
            # Spanish
            "idiota", "estupido", "malo", "feo", "basura",
            "maldito", "carajo", "pendejo", "imbecil",
            # French
            "idiot", "stupide", "sale", "vilain", "ordure",
            "maudit", "connard", "emmerdeur",
            # German
            "idiot", "dummkopf", "hass", "töten", "hässlich",
            "mist", "verdammt", "arschloch", "schwein",
        }
        _RELIGIOUS_WORDS = {
            # English
            "infidel", "blasphemy", "heretic", "kafir", "apostate",
            "burn in hell", "go to hell", "god hates", "damn god",
            "curse god", "hate religion", "destroy religion",
            # Dutch
            "ongelovige", "godslastering", "ketter",
            # Urdu Roman
            "kafir", "gustakh", "murtad", "bidat", "shirk",
            "lahanat", "jahanum", "dozakh", "gunahgar",
            "dehshatgird", "fitna", "taghut",
            # Arabic Roman
            "kafir", "murtad", "fasiq", "mushrik", "zindiq",
            # Hindi Roman
            "kafir", "murtad", "paapi", "narak", "jahannum",
            # Spanish
            "hereje", "infiel", "blasfemia", "maldito",
            # French
            "hérétique", "infidèle", "blasphème",
            # German
            "ketzer", "ungläubiger", "gotteslästerung",
        }
        lower = text.lower()
        religious_hit = any(w in lower for w in _RELIGIOUS_WORDS)
        toxic_hit     = any(w in lower for w in _TOXIC_WORDS)

        trigger_words = []
        if religious_hit:
            label = "religious_hate"
            label_id = 5
            confidence = 0.72
            for w in sorted(_RELIGIOUS_WORDS, key=len, reverse=True):
                if w in lower:
                    trigger_words.append(w)
                    if len(trigger_words) >= 10:
                        break
            scores = {
                "clean": 0.05, "cyberbullying": 0.05, "harassment": 0.05,
                "hate_speech": 0.10, "threat": 0.03, "religious_hate": 0.72,
            }
        elif toxic_hit:
            label = "cyberbullying"
            label_id = 1
            confidence = 0.75
            for w in sorted(_TOXIC_WORDS, key=len, reverse=True):
                if w in lower:
                    trigger_words.append(w)
                    if len(trigger_words) >= 10:
                        break
            scores = {
                "clean": 0.09, "cyberbullying": 0.75, "harassment": 0.07,
                "hate_speech": 0.05, "threat": 0.02, "religious_hate": 0.02,
            }
        else:
            label = "clean"
            label_id = 0
            confidence = 0.90
            scores = {
                "clean": 0.90, "cyberbullying": 0.04, "harassment": 0.02,
                "hate_speech": 0.02, "threat": 0.01, "religious_hate": 0.01,
            }

        return PredictionResult(
            text=text,
            label=label,
            label_id=label_id,
            confidence=confidence,
            scores=scores,
            is_harmful=(label != "clean"),
            severity=_severity(label, confidence),
            color=LABEL_COLORS[label],
            trigger_words=trigger_words,
        )
