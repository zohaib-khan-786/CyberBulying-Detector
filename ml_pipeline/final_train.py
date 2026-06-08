"""Final optimized training - merged_dataset_v3 only, best possible LR."""
import pandas as pd, time, pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

df = pd.read_csv('data/merged_dataset_v3.csv')
print(f'Rows: {len(df)}')

X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label']
)

vec = TfidfVectorizer(
    ngram_range=(1, 2), max_features=35000, sublinear_tf=True,
    strip_accents='unicode', analyzer='word', min_df=2, max_df=0.85,
)
Xv = vec.fit_transform(X_train)
Xt = vec.transform(X_test)
print(f'TF-IDF: {Xv.shape}')

t0 = time.time()
lr = LogisticRegression(max_iter=2000, C=1.5, class_weight='balanced', solver='lbfgs', n_jobs=-1, random_state=42)
lr.fit(Xv, y_train)
pred = lr.predict(Xt)
acc = accuracy_score(y_test, pred)
print(f'Accuracy: {acc:.4f} [{time.time()-t0:.1f}s]')

label_names = ['clean','cyberbullying','harassment','hate_speech','threat','religious_hate']
print(classification_report(y_test, pred, target_names=label_names, zero_division=0))

# Save
SAVE_DIR = Path('backend/models/saved_models')
SAVE_DIR.mkdir(parents=True, exist_ok=True)
with open(SAVE_DIR / 'lr_model.pkl', 'wb') as f:
    pickle.dump(lr, f)
with open(SAVE_DIR / 'vectorizer.pkl', 'wb') as f:
    pickle.dump(vec, f)
print(f'Saved to {SAVE_DIR}')
print(f'Final accuracy: {acc:.4f}')
