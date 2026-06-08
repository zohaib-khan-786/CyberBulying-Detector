"""
Train on real data only. Focus on quality over quantity.
Uses improved preprocessing and balanced Logistic Regression.
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from datasets import load_dataset

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

LABELS = {0: "clean", 1: "cyberbullying", 2: "harassment", 3: "hate_speech", 4: "threat", 5: "religious_hate"}
SAVE_DIR = Path(__file__).parent.parent / "backend" / "models" / "saved_models"
ROWS = []


def add(text: str, label: int):
    if isinstance(text, str) and len(text.strip()) > 3:
        ROWS.append({"text": text.strip().lower(), "label": label})


def load_cyberbullying_tweets():
    """47k rows with cyberbullying types including religion."""
    path = Path(__file__).parent.parent / "data" / "cyberbullying_tweets.csv"
    df = pd.read_csv(path)
    for _, r in df.iterrows():
        text = r.get("tweet_text", "")
        ctype = str(r.get("cyberbullying_type", "")).lower()
        if ctype == "not_cyberbullying":
            add(text, 0)
        elif ctype == "religion":
            add(text, 5)
        elif ctype == "ethnicity":
            add(text, 3)
        elif ctype in ("gender", "age"):
            add(text, 2)
        else:
            add(text, 1)
    logger.info("cyberbullying_tweets: %d rows", len(df))


def load_merged():
    """68k rows pre-labeled with all 6 classes."""
    path = Path(__file__).parent.parent / "data" / "merged_dataset_v3.csv"
    df = pd.read_csv(path)
    for _, r in df.iterrows():
        add(r["text"], int(r["label"]))
    logger.info("merged_dataset_v3: %d rows", len(df))


def load_unfair():
    """UNFAIR dataset - sample toxic and clean comments."""
    path = Path(__file__).parent.parent / "data" / "train.csv"
    df = pd.read_csv(path)
    # Take ALL toxic rows + balanced clean sample
    labels = ["malignant", "highly_malignant", "rude", "threat", "abuse", "loathe"]
    is_toxic = df[labels].any(axis=1)
    toxic = df[is_toxic]
    clean = df[~is_toxic].sample(n=min(30000, len(df[~is_toxic])), random_state=42)
    combined = pd.concat([toxic, clean]).sample(frac=1, random_state=42)
    for _, r in combined.iterrows():
        text = r.get("comment_text", "")
        if not text:
            continue
        if r["threat"] == 1:
            add(text, 4)
        elif r["highly_malignant"] == 1:
            add(text, 2)
        elif r["loathe"] == 1:
            add(text, 3)
        elif r["abuse"] == 1:
            add(text, 1)
        elif r["malignant"] == 1:
            add(text, 2)
        elif r["rude"] == 1:
            add(text, 1)
        else:
            add(text, 0)
    logger.info("UNFAIR train.csv: %d rows used", len(combined))


def load_davidson():
    """24k rows: hate speech, offensive, neither."""
    try:
        ds = load_dataset("hate_speech_offensive", split="train")
        for item in ds:
            cls = item["class"]
            text = item["tweet"]
            if cls == 0:
                add(text, 3)
            elif cls == 1:
                add(text, 2)
            else:
                add(text, 0)
        logger.info("Davidson/HuggingFace: %d rows", len(ds))
    except Exception as e:
        logger.warning("HF load failed: %s", e)
        # Fallback to local
        path = Path(__file__).parent.parent / "data" / "labeled_data.csv"
        if path.exists():
            df = pd.read_csv(path)
            for _, r in df.iterrows():
                text = r.get("tweet", "")
                cls = r.get("class", 2)
                if cls == 0:
                    add(text, 3)
                elif cls == 1:
                    add(text, 2)
                else:
                    add(text, 0)
            logger.info("Davidson local: %d rows", len(df))


def clean_text(texts):
    """Efficient batch text cleaning."""
    import re
    cleaned = []
    for t in texts:
        t = re.sub(r"http\S+|www\S+", "", t)
        t = re.sub(r"@\w+|#\w+", "", t)
        t = re.sub(r"[^a-z\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        cleaned.append(t)
    return cleaned


def main():
    load_cyberbullying_tweets()
    load_merged()
    load_unfair()
    load_davidson()

    df = pd.DataFrame(ROWS)
    logger.info("Total rows: %d", len(df))
    logger.info("Distribution:\n%s", df["label"].value_counts().sort_index())

    # Clean
    df["text"] = clean_text(df["text"].tolist())
    df = df[df["text"].str.len() > 2].reset_index(drop=True)
    logger.info("After cleaning: %d rows", len(df))

    # ── Balance the dataset ─────────────────────────────────────────────
    # Threat class is tiny (956). Duplicate it.
    # Cap each class at 15000 for cleaner training.
    MAX_PER_CLASS = 15000
    balanced = []
    for label_id in sorted(df["label"].unique()):
        subset = df[df["label"] == label_id]
        if len(subset) > MAX_PER_CLASS:
            subset = subset.sample(n=MAX_PER_CLASS, random_state=42)
        elif len(subset) < 2000 and label_id != 0:
            # Upsample minority classes (not clean)
            n_needed = min(4000, MAX_PER_CLASS)
            if len(subset) < n_needed:
                dupes = subset.sample(n=n_needed - len(subset), replace=True, random_state=42)
                subset = pd.concat([subset, dupes])
        balanced.append(subset)

    df = pd.concat(balanced, ignore_index=True).sample(frac=1, random_state=42)
    logger.info("Balanced distribution:\n%s", df["label"].value_counts().sort_index())

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"],
    )
    logger.info("Train: %d | Test: %d", len(X_train), len(X_test))

    label_names = [LABELS[i] for i in sorted(LABELS)]

    # TF-IDF with optimized params
    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=40000,
        sublinear_tf=True,
        strip_accents="unicode",
        analyzer="word",
        min_df=3,
        max_df=0.85,
    )
    logger.info("Fitting TF-IDF...")
    X_train_vec = vec.fit_transform(X_train)
    X_test_vec = vec.transform(X_test)
    logger.info("  TF-IDF shape: %s", str(X_train_vec.shape))

    # ── Logistic Regression ──────────────────────────────────────────────
    logger.info("Training Logistic Regression...")
    lr = LogisticRegression(
        max_iter=2000, C=2.0, class_weight="balanced",
        solver="saga", random_state=42, n_jobs=-1,
    )
    lr.fit(X_train_vec, y_train)
    y_pred = lr.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n== Logistic Regression (accuracy: {acc:.4f}) =====================")
    print(classification_report(y_test, y_pred, target_names=label_names, zero_division=0))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    # ── Save ─────────────────────────────────────────────────────────────
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SAVE_DIR / "lr_model.pkl", "wb") as f:
        pickle.dump(lr, f)
    with open(SAVE_DIR / "vectorizer.pkl", "wb") as f:
        pickle.dump(vec, f)
    logger.info("Saved to %s", SAVE_DIR)

    # ── Validate ─────────────────────────────────────────────────────────
    print("\n== Validation ===================================================")
    cases = [
        ("kafir hate", "you are a kafir and infidel go to hell"),
        ("threat", "I will kill you and make you die tonight"),
        ("insult", "you are a stupid idiot and a complete loser"),
        ("hate all", "I hate all of you people you are all disgusting"),
        ("harass", "shut up you worthless piece of trash nobody likes you"),
        ("swear", "Fuck this shit"),
        ("clean", "thank you for your help I really appreciate it"),
        ("clean2", "The weather is nice today"),
        ("muslim pos", "Muslims are good people"),
        ("muslim neg", "Muslims are terrorists and should die"),
        ("god bless", "God bless you"),
        ("short", "stupid idiot"),
    ]
    for desc, text in cases:
        v = vec.transform([text])
        proba = lr.predict_proba(v)[0]
        pred_id = int(lr.predict(v)[0])
        pred = LABELS.get(pred_id, "?")
        conf = round(float(proba[pred_id]), 4)
        top3 = sorted(
            [(LABELS.get(i, "?"), round(float(proba[i]), 4)) for i in range(len(proba))],
            key=lambda x: -x[1],
        )[:3]
        print(f"  {desc:12s} -> {pred:15s} (conf={conf:.4f}) top3={top3}")

    print(f"\n=== DONE === Accuracy: {acc:.4f}")


if __name__ == "__main__":
    main()
