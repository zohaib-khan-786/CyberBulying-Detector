"""
Training script — Cyberbullying Detector

Trains two classifiers on the dataset:
  1. TF-IDF + Logistic Regression  (saved as lr_model.pkl)   ← production default
  2. TF-IDF + Naive Bayes          (saved as nb_model.pkl)   ← fast baseline

Labels
------
  0  clean
  1  cyberbullying
  2  harassment
  3  hate_speech
  4  threat
  5  religious_hate   ← added per project requirements

Usage
-----
# Synthetic demo data (no download):
python train.py

# Real Kaggle data:
python train.py --data path/to/train.csv --text-col comment_text --label-col toxic

# Multilabel Kaggle format:
python train.py --data path/to/train.csv --text-col comment_text \
    --label-cols toxic severe_toxic obscene threat insult identity_hate
"""

from __future__ import annotations

import argparse
import logging
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from ml_pipeline.preprocess import clean_batch

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

LABELS = {
    0: "clean",
    1: "cyberbullying",
    2: "harassment",
    3: "hate_speech",
    4: "threat",
    5: "religious_hate",
}

SAVE_DIR = Path(__file__).parent.parent / "backend" / "models" / "saved_models"


def load_data(
    path: str | None,
    text_col: str,
    label_col: str | None,
    label_cols: list[str] | None,
) -> pd.DataFrame:
    if path is None:
        logger.error("No data file provided. Use --data PATH to specify a CSV file.")
        logger.error("Example: python ml_pipeline/train.py --data data/merged_dataset_v3.csv --text-col text --label-col label")
        raise SystemExit(1)

    logger.info("Loading data from %s …", path)
    df = pd.read_csv(path)

    if label_cols:
        priority   = ["threat", "severe_toxic", "obscene", "insult", "identity_hate", "toxic"]
        label_map  = {
            "threat": 4, "severe_toxic": 3, "identity_hate": 3,
            "obscene": 2, "insult": 1, "toxic": 1,
        }
        def row_to_label(row):
            for col in priority:
                if col in label_cols and row.get(col, 0):
                    return label_map.get(col, 1)
            return 0
        df["label"] = df.apply(row_to_label, axis=1)
    else:
        df = df.rename(columns={label_col: "label"})

    df = df.rename(columns={text_col: "text"})
    df = df[["text", "label"]].dropna()
    df["label"] = df["label"].astype(int)
    logger.info("Loaded %d rows. Distribution:\n%s", len(df), df["label"].value_counts())
    return df


def _tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=50_000,
        sublinear_tf=True,
        strip_accents="unicode",
        analyzer="word",
        min_df=2,
    )


def build_lr_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", _tfidf()),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=1.0,
            class_weight="balanced",
            solver="lbfgs",
        )),
    ])


def build_nb_pipeline() -> Pipeline:
    """
    ComplementNB is better than MultinomialNB for imbalanced text corpora.
    Works with TF-IDF directly (no non-negative constraint issues).
    """
    return Pipeline([
        ("tfidf", _tfidf()),
        ("clf", ComplementNB(alpha=0.5)),
    ])


def evaluate(name: str, model, X_test, y_test):
    y_pred = model.predict(X_test)
    label_names = [LABELS[i] for i in sorted(LABELS)]
    print(f"\n== {name} ======================================================")
    print(classification_report(y_test, y_pred, target_names=label_names, zero_division=0))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))


def save_model(pipeline: Pipeline, name: str):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    prefix = "lr" if "LogisticRegression" in type(pipeline.named_steps["clf"]).__name__ else "nb"
    model_path = SAVE_DIR / f"{prefix}_model.pkl"
    vec_path   = SAVE_DIR / "vectorizer.pkl"   # shared vectorizer (same config)

    with open(model_path, "wb") as f:
        pickle.dump(pipeline.named_steps["clf"], f)
    # Save vectorizer once (LR run writes it; NB reuses it)
    if prefix == "lr":
        with open(vec_path, "wb") as f:
            pickle.dump(pipeline.named_steps["tfidf"], f)
    logger.info("%s saved -> %s", name, model_path)


def main():
    parser = argparse.ArgumentParser(description="Train cyberbullying classifiers")
    parser.add_argument("--data",       default=None)
    parser.add_argument("--text-col",   default="text")
    parser.add_argument("--label-col",  default="label")
    parser.add_argument("--label-cols", nargs="+")
    parser.add_argument("--test-size",  type=float, default=0.2)
    parser.add_argument("--seed",       type=int,   default=42)
    args = parser.parse_args()

    df = load_data(args.data, args.text_col, args.label_col, args.label_cols)

    logger.info("Cleaning text …")
    df["text"] = clean_batch(df["text"].tolist())

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"],
        test_size=args.test_size,
        random_state=args.seed,
        stratify=df["label"],
    )
    logger.info("Train: %d  |  Test: %d", len(X_train), len(X_test))

    # ── Logistic Regression ────────────────────────────────────────────────────
    logger.info("Training Logistic Regression …")
    lr = build_lr_pipeline()
    lr.fit(X_train, y_train)
    evaluate("Logistic Regression", lr, X_test, y_test)
    save_model(lr, "Logistic Regression")

    # ── Naive Bayes baseline ───────────────────────────────────────────────────
    logger.info("Training Complement Naive Bayes baseline …")
    nb = build_nb_pipeline()
    nb.fit(X_train, y_train)
    evaluate("Complement Naive Bayes", nb, X_test, y_test)
    save_model(nb, "Complement Naive Bayes")

    logger.info("\nBoth models trained and saved to %s", SAVE_DIR)


if __name__ == "__main__":
    main()
