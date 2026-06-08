# Debugging Guide

## Error: `'CyberbullyingClassifier' object has no attribute '_predict_finetuned_bert'`

### What It Means

The server loads a fine-tuned BERT model (`backend/models/saved_models/cyberbullying_bert/`) and tries to call `_predict_finetuned_bert()` on it, but that method does not exist in the class.

```
AttributeError: 'CyberbullyingClassifier' object has no attribute '_predict_finetuned_bert'
  File "...\backend\models\classifier.py", line 152, in predict
    result = self._predict_finetuned_bert(text)
```

### Root Cause

A missing method in `classifier.py`. The `load()` method detects the BERT model folder and calls `_load_finetuned_bert()` to load it. Then `predict()` tries to call `_predict_finetuned_bert()` on line 152 — but that method was never written.

### How to Fix

1. Open `backend/models/classifier.py`.
2. Add the `_predict_finetuned_bert` method. A working implementation:

```python
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
```

3. **Restart the server** (simply stopping `python app.py` and running it again is usually enough).

### Why It Happened Initially

The `_load_finetuned_bert()` method was added to load the Colab-trained BERT model, and `predict()` was updated to prefer the fine-tuned model over the sklearn/transformer models — but the corresponding predict method was overlooked.

### How to Prevent

When adding a new model type to the classifier, always add **three methods** together:

| Method | Purpose |
|---|---|
| `_load_<model>()` | Load model from disk |
| `_predict_<model>(text)` | Run inference and return a `PredictionResult` |
| `_extract_trigger_words_<model>(...)` | (if needed) Feature attribution |

Then wire them in `load()` and `predict()`.
