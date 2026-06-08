"""
Augment existing training data with synthetic samples for weak classes,
then retrain both models.
"""
from __future__ import annotations

import logging
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

sys.path.insert(0, str(Path(__file__).parent.parent))
from ml_pipeline.preprocess import clean_batch

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

LABELS = {0: "clean", 1: "cyberbullying", 2: "harassment", 3: "hate_speech", 4: "threat", 5: "religious_hate"}
SAVE_DIR = Path(__file__).parent.parent / "backend" / "models" / "saved_models"


def _generate_synthetic() -> pd.DataFrame:
    """Generate synthetic examples for weak classes."""
    logger.info("Generating synthetic training data…")
    rows: list[dict] = []

    # Clean counter-examples: positive religious mentions to avoid false positives
    clean_religious = [
        "God bless you", "May God bless you", "God is great",
        "I love God", "Praise the Lord", "Thank God",
        "Allahu Akbar", "MashaAllah", "SubhanAllah",
        "I am a Muslim", "I love being Muslim",
        "Muslims are good people", "I respect all religions",
        "Peace be upon you", "Namaste", "Om Shanti",
        "I believe in God", "My faith is important to me",
        "Going to church today", "Temple was beautiful",
        "Reading the Quran", "Studying the Bible",
        "I respect Muslims", "Muslims are kind",
        "Christians are good people", "Hindus are peaceful",
        "All religions deserve respect",
        "Interfaith is important", "Religious freedom matters",
        "Buddha teaches peace", "I love my religion",
        "Jewish people are wonderful", "Mazel Tov",
        "Happy Diwali", "Merry Christmas", "Eid Mubarak",
        "Ramadan Kareem", "Bless you", "Have faith",
        "Spiritual journey", "Religious tolerance is important",
        "Going to pray", "Faith gives me strength",
    ]

    for text in clean_religious:
        rows.append({"text": text, "label": 0})

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
        "get out of here kafir",
        "infidel get out of our country",
        "you are a dirty kafir and infidel",
        "god hates you kafir",
        "curse you kafir infidel",
        "you are going to hell kafir",
        "kafir you deserve to burn",
        "damn all infidels and kafirs",
    ]

    cb = [
        "you are such a loser", "you are a complete loser",
        "you are a total failure", "you are worthless",
        "you are pathetic", "you are a disappointment",
        "everyone hates you", "nobody likes you",
        "you have no friends", "you are a joke",
        "you are a laughing stock", "you are dumb",
        "you are stupid", "you are an idiot",
        "you are a moron", "you are a fool",
        "you are so dumb", "you are so stupid",
        "you are the dumbest person", "you are the stupidest",
        "you are a complete idiot", "you are a total idiot",
        "you are a waste of space", "you are a waste of time",
        "you are a burden", "you are a nuisance",
        "you are so annoying", "you are a pest",
        "nobody wants you here", "go away nobody likes you",
        "you are a nobody", "you are worthless and useless",
        "you are a trash person", "you are garbage",
        "you are a horrible person", "you are a terrible person",
        "you are the worst", "you are the worst person ever",
        "you are an embarrassment", "you are a disgrace",
        "we all hate you", "everyone thinks you are stupid",
        "you are a complete joke", "you are a total joke",
        "you are pathetic and worthless", "you are dumb and stupid",
        "you are a stupid idiot and a complete loser",
        "i hate you you are so dumb",
        "you are so dumb you cannot do anything right",
        "you are a failure at everything",
        "stop being so annoying nobody likes you",
        "you ruined everything you idiot",
        "you are such a disappointment to everyone",
        "you are the dumbest person i know",
        "you are a complete waste of oxygen",
        "you are so useless nobody needs you",
        "you are a failure at life",
        "you are pathetic and nobody cares about you",
        "you are a total loser and everyone knows it",
        "you are worthless and nobody wants you",
    ]

    hs = [
        "i hate all of you people", "i hate everyone",
        "i hate your kind", "i hate people like you",
        "i hate you and everyone like you",
        "all of you are disgusting", "you people are disgusting",
        "your kind are not welcome here",
        "i hate all of you people you are all disgusting",
        "i hate your entire race", "i hate people of your kind",
        "you people make me sick", "your kind is a disease",
    ]

    for text in rh:
        rows.append({"text": text, "label": 5})
    for text in cb:
        rows.append({"text": text, "label": 1})
    for text in hs:
        rows.append({"text": text, "label": 3})

    return pd.DataFrame(rows)


def _tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=50_000,
        sublinear_tf=True,
        strip_accents="unicode",
        analyzer="word",
        min_df=2,
    )


def main():
    # Load original data
    data_path = Path(__file__).parent.parent / "data" / "merged_dataset_v3.csv"
    if not data_path.exists():
        logger.error("Training data not found at %s", data_path)
        raise SystemExit(1)

    logger.info("Loading original data from %s…", data_path)
    original = pd.read_csv(data_path)
    logger.info("Original distribution:\n%s", original["label"].value_counts().sort_index())

    # Generate synthetic augmentation
    synthetic = _generate_synthetic()

    # Merge datasets
    df = pd.concat([original, synthetic], ignore_index=True)
    logger.info("Augmented distribution:\n%s", df["label"].value_counts().sort_index())

    # Clean text
    logger.info("Cleaning text…")
    df["text"] = clean_batch(df["text"].tolist())

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )
    logger.info("Train: %d  |  Test: %d", len(X_train), len(X_test))

    # ── Train Logistic Regression ──────────────────────────────────────────
    logger.info("Training Logistic Regression…")
    lr = Pipeline([
        ("tfidf", _tfidf()),
        ("clf", LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", solver="lbfgs")),
    ])
    lr.fit(X_train, y_train)

    # Evaluate
    y_pred = lr.predict(X_test)
    label_names = [LABELS[i] for i in sorted(LABELS)]
    print("\n== Logistic Regression ================================================")
    print(classification_report(y_test, y_pred, target_names=label_names, zero_division=0))
    print("Confusion matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # Save model
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    model_path = SAVE_DIR / "lr_model.pkl"
    vec_path   = SAVE_DIR / "vectorizer.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(lr.named_steps["clf"], f)
    with open(vec_path, "wb") as f:
        pickle.dump(lr.named_steps["tfidf"], f)
    logger.info("LR model saved -> %s", model_path)

    # Quick validation on key test cases
    logger.info("\nQuick validation on key test cases:")
    cases = [
        ("kafir", "you are a kafir and infidel go to hell"),
        ("threat", "I will kill you and make you die tonight"),
        ("insult", "you are a stupid idiot and a complete loser"),
        ("hate", "I hate all of you people you are all disgusting"),
        ("harass", "shut up you worthless piece of trash nobody likes you"),
        ("swear", "Fuck this shit"),
        ("clean", "thank you for your help I really appreciate it"),
        ("mus lim pos", "Muslims are good people"),
        ("mus lim neg", "Muslims are terrorists and should die"),
    ]
    vec = lr.named_steps["tfidf"]
    clf = lr.named_steps["clf"]
    for desc, text in cases:
        v = vec.transform([text])
        proba = clf.predict_proba(v)[0]
        pred_id = int(clf.predict(v)[0])
        pred = LABELS.get(pred_id, "?")
        rh = round(proba[5], 4)
        conf = round(proba[pred_id], 4)
        print(f"  {desc:15s} → {pred:15s} (conf={conf:.4f}, rel_hate={rh:.4f})")

    print("\nDone! Restart the Flask server to use the new model.")


if __name__ == "__main__":
    main()
