"""
Evaluate a trained model against a test CSV.

Usage
-----
python evaluate.py --test path/to/test.csv
python evaluate.py --test path/to/test.csv --report-dir ./reports
"""

from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from ml_pipeline.preprocess import clean_batch

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

SAVE_DIR = Path(__file__).parent.parent / "backend" / "models" / "saved_models"
LABELS   = {0: "clean", 1: "cyberbullying", 2: "harassment", 3: "hate_speech", 4: "threat", 5: "religious_hate"}


def load_model():
    with open(SAVE_DIR / "lr_model.pkl",   "rb") as f: model = pickle.load(f)
    with open(SAVE_DIR / "vectorizer.pkl", "rb") as f: vec   = pickle.load(f)
    return model, vec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test",       required=True, help="Path to test CSV (columns: text, label)")
    parser.add_argument("--text-col",   default="text")
    parser.add_argument("--label-col",  default="label")
    parser.add_argument("--report-dir", default="./reports")
    args = parser.parse_args()

    logger.info("Loading model …")
    model, vec = load_model()

    logger.info("Loading test data from %s …", args.test)
    df = pd.read_csv(args.test)[[args.text_col, args.label_col]].dropna()
    df.columns = ["text", "label"]
    df["text"] = clean_batch(df["text"].tolist())

    X = vec.transform(df["text"])
    y_true = df["label"].astype(int).tolist()
    y_pred = model.predict(X).tolist()
    y_prob = model.predict_proba(X)

    label_names = [LABELS[i] for i in sorted(LABELS)]
    acc = accuracy_score(y_true, y_pred)

    print(f"\n── Accuracy: {acc:.4f} ─────────────────────────────────────────")
    print(classification_report(y_true, y_pred, target_names=label_names, zero_division=0))
    print("── Confusion Matrix ──────────────────────────────────────────")
    cm = confusion_matrix(y_true, y_pred)
    print(cm)

    # Save JSON report
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "accuracy": round(acc, 4),
        "per_class": classification_report(
            y_true, y_pred,
            target_names=label_names,
            zero_division=0,
            output_dict=True,
        ),
        "confusion_matrix": cm.tolist(),
    }
    out_path = report_dir / "eval_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    logger.info("Report saved to %s", out_path)


if __name__ == "__main__":
    main()
