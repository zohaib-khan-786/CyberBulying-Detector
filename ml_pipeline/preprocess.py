"""
Text preprocessing for cyberbullying detection.

Usage
-----
from preprocess import clean_text, build_vectorizer

text_clean = clean_text("You are so stupid!!!")
X_vec = vectorizer.transform([text_clean])
"""

from __future__ import annotations

import re
import string
import unicodedata
from typing import List, Optional


# ── Lookup tables ──────────────────────────────────────────────────────────────

CONTRACTIONS = {
    "won't": "will not", "can't": "cannot", "i'm": "i am",
    "i've": "i have", "i'll": "i will", "i'd": "i would",
    "you're": "you are", "you've": "you have", "you'll": "you will",
    "he's": "he is", "she's": "she is", "it's": "it is",
    "we're": "we are", "they're": "they are", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
}

# Common online abbreviations
SLANG = {
    "lol":  "laughing out loud", "omg": "oh my god",
    "wtf":  "what the",         "idk": "i do not know",
    "imo":  "in my opinion",    "tbh": "to be honest",
    "ngl":  "not going to lie", "stfu": "shut up",
    "kys":  "kill yourself",    "gtfo": "get out",
}


# ── Core cleaning function ─────────────────────────────────────────────────────

def clean_text(
    text: str,
    *,
    expand_contractions: bool = True,
    expand_slang: bool = True,
    remove_urls: bool = True,
    remove_mentions: bool = True,
    remove_hashtags: bool = False,   # keep hashtag words
    remove_numbers: bool = False,
    lowercase: bool = True,
    remove_extra_spaces: bool = True,
) -> str:
    """
    Full cleaning pipeline.  Returns a cleaned string ready for vectorisation.
    """
    if not isinstance(text, str):
        text = str(text)

    # 1. Normalise unicode (e.g. fancy quotes → ASCII)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # 2. Lowercase early so all lookups work
    if lowercase:
        text = text.lower()

    # 3. URLs
    if remove_urls:
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # 4. @mentions
    if remove_mentions:
        text = re.sub(r"@\w+", " ", text)

    # 5. #hashtags — strip # but keep the word
    if remove_hashtags:
        text = re.sub(r"#\w+", " ", text)
    else:
        text = re.sub(r"#(\w+)", r"\1", text)

    # 6. HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # 7. Contractions
    if expand_contractions:
        for contraction, expansion in CONTRACTIONS.items():
            text = text.replace(contraction, expansion)

    # 8. Slang
    if expand_slang:
        words = text.split()
        words = [SLANG.get(w, w) for w in words]
        text = " ".join(words)

    # 9. Repeated characters (loooool → lool)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    # 10. Punctuation
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))

    # 11. Numbers
    if remove_numbers:
        text = re.sub(r"\d+", " ", text)

    # 12. Extra whitespace
    if remove_extra_spaces:
        text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_batch(texts: List[str], **kwargs) -> List[str]:
    """Vectorised cleaning for a list of strings."""
    return [clean_text(t, **kwargs) for t in texts]


# ── Feature helpers ────────────────────────────────────────────────────────────

def extract_meta_features(text: str) -> dict:
    """
    Hand-crafted features that complement bag-of-words.
    Returns a dict with numeric values.
    """
    return {
        "char_count":        len(text),
        "word_count":        len(text.split()),
        "cap_ratio":         sum(1 for c in text if c.isupper()) / max(len(text), 1),
        "exclamation_count": text.count("!"),
        "question_count":    text.count("?"),
        "url_count":         len(re.findall(r"https?://\S+", text)),
        "mention_count":     len(re.findall(r"@\w+", text)),
        "emoji_count":       len(re.findall(r"[\U0001F600-\U0001FFFF]", text)),
    }


# ── Quick sanity-check ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    samples = [
        "You are sooooo STUPID and ugly!!!",
        "kys loser, gtfo of here",
        "Have a great day!",
        "Check this out: https://spam.com @badactor #bullying",
    ]
    print("=== Preprocessing Demo ===\n")
    for s in samples:
        cleaned = clean_text(s)
        meta    = extract_meta_features(s)
        print(f"  Original : {s}")
        print(f"  Cleaned  : {cleaned}")
        print(f"  Meta     : {meta}")
        print()
