"""Train on merged_dataset_v3.csv + real cyberbullying_tweets dataset."""
import pandas as pd, time, pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

df1 = pd.read_csv('data/merged_dataset_v3.csv')
df2 = pd.read_csv('data/cyberbullying_tweets.csv')
df2 = df2.rename(columns={'tweet_text': 'text'})
type_map = {
    'not_cyberbullying': 0, 'religion': 5, 'ethnicity': 3,
    'gender': 2, 'age': 2,
}
df2['label'] = df2['cyberbullying_type'].str.lower().map(type_map).fillna(1)
df2 = df2[['text', 'label']]

df = pd.concat([df1, df2], ignore_index=True)
dist = df['label'].value_counts().sort_index()
print(f'Total: {len(df)} rows')
print(f'Dist: {dist.to_dict()}')

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

# Validate key cases
print('\n=== Validation ===')
cases = [
    ('kafir', "you are a kafir and infidel go to hell"),
    ('threat', "I will kill you and make you die tonight"),
    ('insult', "you are a stupid idiot and a complete loser"),
    ('hate', "I hate all of you people you are all disgusting"),
    ('harass', "shut up you worthless piece of trash nobody likes you"),
    ('swear', "Fuck this shit"),
    ('clean', "thank you for your help I really appreciate it"),
    ('muslim pos', "Muslims are good people"),
    ('muslim neg', "Muslims are terrorists and should die"),
    ('jews hate', "You are so fucked up, and you Jews are fungus to society"),
]
for desc, text in cases:
    v = vec.transform([text])
    proba = lr.predict_proba(v)[0]
    pred_id = int(lr.predict(v)[0])
    pred = label_names[pred_id] if pred_id < len(label_names) else '?'
    conf = round(float(proba[pred_id]), 4)
    rh = round(float(proba[5]), 4) if len(proba) > 5 else 0
    print(f'  {desc:12s} -> {pred:15s} (conf={conf:.4f}) rel_hate={rh:.4f}')

# Save
SAVE_DIR = Path('backend/models/saved_models')
SAVE_DIR.mkdir(parents=True, exist_ok=True)
with open(SAVE_DIR / 'lr_model.pkl', 'wb') as f:
    pickle.dump(lr, f)
with open(SAVE_DIR / 'vectorizer.pkl', 'wb') as f:
    pickle.dump(vec, f)
print(f'\nSaved. Accuracy: {acc:.4f}')
