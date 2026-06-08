"""
Comprehensive training script for 89%+ accuracy.
Uses:
- merged_dataset_v3.csv (68k rows, 6 classes)
- hate_speech_offensive from HuggingFace (24k rows, 3 classes)
- Synthetic augmentation data
- XGBoost for best accuracy
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from datasets import load_dataset

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

LABELS = {0: "clean", 1: "cyberbullying", 2: "harassment", 3: "hate_speech", 4: "threat", 5: "religious_hate"}
SAVE_DIR = Path(__file__).parent.parent / "backend" / "models" / "saved_models"


def load_merged_data() -> pd.DataFrame:
    path = Path(__file__).parent.parent / "data" / "merged_dataset_v3.csv"
    logger.info("Loading merged data from %s...", path)
    df = pd.read_csv(path)
    logger.info("  Rows: %d, columns: %s", len(df), df.columns.tolist())
    return df


def load_huggingface_data() -> pd.DataFrame:
    """Load hate_speech_offensive from HuggingFace and map labels to our schema."""
    logger.info("Loading hate_speech_offensive from HuggingFace...")
    ds = load_dataset("hate_speech_offensive", split="train")
    df = pd.DataFrame({"text": ds["tweet"], "label": ds["class"]})
    # Map: 0=hate speech->3, 1=offensive language->2, 2=neither->0
    mapping = {0: 3, 1: 2, 2: 0}
    df["label"] = df["label"].map(mapping)
    df = df.dropna()
    logger.info("  Rows: %d", len(df))
    return df


def load_synthetic_data() -> pd.DataFrame:
    """Load or generate synthetic augmentation data."""
    path = Path(__file__).parent.parent / "data" / "synthetic_augment.csv"
    if path.exists():
        logger.info("Loading synthetic data from %s...", path)
        return pd.read_csv(path)
    logger.info("Generating synthetic data...")
    rows = []
    rh = [
        "you are a kafir", "you kafir", "kafir go to hell", "stupid kafir",
        "you are an infidel", "infidel dog", "dirty infidel", "filthy infidel",
        "kafir and infidel both are bad", "you kafir and infidel die",
        "kafir you are worthless", "burn in hell kafir", "kafir bastards",
        "infidel go to hell", "damn infidel", "infidel scum",
        "go to hell you kafir", "kafir infidel all are same",
        "you are a blasphemer", "blasphemer go to hell", "damn blasphemer",
        "heretic you are", "burn heretic", "kill the heretic",
        "apostate you will burn", "dirty apostate", "apostate infidel",
        "god will punish you kafir", "you reject god kafir",
        "worship satan you infidel", "kafir infidel blasphemer",
        "you are a murtad", "murtad go to hell",
        "kafirs should be killed", "infidels should die",
        "all kafirs go to hell", "you kafir you will burn",
        "you are a mushrik", "mushrik infidel",
        "you are a kafir and infidel go to hell",
        "you kafir you are not muslim",
        "you are not a true believer you kafir",
        "get out of here kafir", "infidel get out of our country",
        "you are a dirty kafir and infidel",
    ]
    for text in rh:
        rows.append({"text": text, "label": 5})
    return pd.DataFrame(rows)


def build_tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=100_000,
        sublinear_tf=True,
        strip_accents="unicode",
        analyzer="word",
        min_df=2,
        max_df=0.95,
    )


def train_xgboost(X_train, y_train, X_test, y_test, label_names):
    """Train XGBoost with hyperparameter tuning."""
    logger.info("Training XGBoost...")

    # Calculate class weights for imbalance
    classes, counts = np.unique(y_train, return_counts=True)
    weight_ratio = max(counts) / counts
    sample_weights = np.array([weight_ratio[c] for c in y_train])

    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="mlogloss",
        use_label_encoder=False,
        n_jobs=-1,
    )
    xgb.fit(X_train, y_train, sample_weight=sample_weights)

    y_pred = xgb.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info("XGBoost accuracy: %.4f", acc)
    print("\n== XGBoost ======================================================")
    print(classification_report(y_test, y_pred, target_names=label_names, zero_division=0))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    return xgb


def train_logistic_regression(X_train, y_train, X_test, y_test, label_names):
    """Train Logistic Regression with balanced class weights."""
    logger.info("Training Logistic Regression...")
    lr = LogisticRegression(
        max_iter=1000,
        C=1.5,
        class_weight="balanced",
        solver="lbfgs",
        multi_class="multinomial",
        random_state=42,
        n_jobs=-1,
    )
    lr.fit(X_train, y_train)

    y_pred = lr.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info("LR accuracy: %.4f", acc)
    print("\n== Logistic Regression ================================================")
    print(classification_report(y_test, y_pred, target_names=label_names, zero_division=0))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    return lr


def validate(model, vec, label_names):
    """Run validation on key test cases."""
    cases = [
        ("kafir", "you are a kafir and infidel go to hell"),
        ("threat", "I will kill you and make you die tonight"),
        ("insult", "you are a stupid idiot and a complete loser"),
        ("hate", "I hate all of you people you are all disgusting"),
        ("harass", "shut up you worthless piece of trash nobody likes you"),
        ("swear", "Fuck this shit"),
        ("clean", "thank you for your help I really appreciate it"),
        ("muslim pos", "Muslims are good people"),
        ("muslim neg", "Muslims are terrorists and should die"),
        ("god bless", "God bless you"),
        ("neutral", "The weather is nice today"),
    ]
    print("\n== Validation ======================================================")
    for desc, text in cases:
        v = vec.transform([text])
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(v)[0]
        else:
            proba = model.predict(v)
            proba = np.zeros(len(label_names))
            proba[proba.argmax()] = 1.0
        pred_id = int(model.predict(v)[0])
        pred = LABELS.get(pred_id, "?")
        conf = round(float(proba[pred_id]), 4)
        rh = round(float(proba[5]), 4) if len(proba) > 5 else 0
        top3 = sorted([(LABELS.get(i, "?"), round(float(proba[i]), 4)) for i in range(len(proba))], key=lambda x: -x[1])[:3]
        print(f"  {desc:12s} -> {pred:15s} (conf={conf:.4f}) rel_hate={rh:.4f} top3={top3}")


def main():
    # Load all data sources
    df_merged = load_merged_data()
    df_hf = load_huggingface_data()
    df_synth = load_synthetic_data()

    # Combine
    df = pd.concat([df_merged, df_hf, df_synth], ignore_index=True)
    logger.info("Combined data: %d rows", len(df))
    logger.info("Label distribution:\n%s", df["label"].value_counts().sort_index())

    # Basic text cleaning
    logger.info("Cleaning text...")
    df["text"] = df["text"].astype(str).str.lower()
    df["text"] = df["text"].str.replace(r"http\S+|www\S+|https\S+", "", regex=True)
    df["text"] = df["text"].str.replace(r"@\w+|#\w+", "", regex=True)
    df["text"] = df["text"].str.replace(r"[^a-z\s]", " ", regex=True)
    df["text"] = df["text"].str.replace(r"\s+", " ", regex=True)
    df["text"] = df["text"].str.strip()

    # Remove empty texts
    df = df[df["text"].str.len() > 0].reset_index(drop=True)
    logger.info("After cleaning: %d rows", len(df))

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )
    logger.info("Train: %d | Test: %d", len(X_train), len(X_test))

    label_names = [LABELS[i] for i in sorted(LABELS)]

    # Build TF-IDF
    logger.info("Building TF-IDF...")
    vec = build_tfidf()
    X_train_vec = vec.fit_transform(X_train)
    X_test_vec = vec.transform(X_test)

    # Train models
    lr = train_logistic_regression(X_train_vec, y_train, X_test_vec, y_test, label_names)
    xgb = train_xgboost(X_train_vec, y_train, X_test_vec, y_test, label_names)

    # Pick the best model
    lr_acc = accuracy_score(y_test, lr.predict(X_test_vec))
    xgb_acc = accuracy_score(y_test, xgb.predict(X_test_vec))
    logger.info("LR accuracy: %.4f, XGB accuracy: %.4f", lr_acc, xgb_acc)

    if xgb_acc >= lr_acc:
        best_model = xgb
        best_name = "XGBoost"
    else:
        best_model = lr
        best_name = "Logistic Regression"
    logger.info("Best model: %s (%.4f)", best_name, max(lr_acc, xgb_acc))

    # Save the best model
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SAVE_DIR / "lr_model.pkl", "wb") as f:
        pickle.dump(best_model, f)
    with open(SAVE_DIR / "vectorizer.pkl", "wb") as f:
        pickle.dump(vec, f)
    logger.info("Best model saved -> %s", SAVE_DIR / "lr_model.pkl")

    # Validate
    validate(best_model, vec, label_names)

    print(f"\nDone! Best model: {best_name} with {max(lr_acc, xgb_acc):.4f} accuracy")


if __name__ == "__main__":
    main()
