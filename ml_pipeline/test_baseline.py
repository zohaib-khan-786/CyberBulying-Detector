"""Test advanced feature engineering and models for 89% target."""
import pandas as pd, time, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.sparse import hstack, csr_matrix

df = pd.read_csv('data/merged_dataset_v3.csv')
print(f'Rows: {len(df)}')

# Split
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label']
)

# 1) Word n-grams (1-3)
vec_word = TfidfVectorizer(ngram_range=(1,3), max_features=40000, sublinear_tf=True, min_df=2, max_df=0.90)
Xw_train = vec_word.fit_transform(X_train)
Xw_test = vec_word.transform(X_test)
print(f'Word features: {Xw_train.shape}')

# 2) Character n-grams (captures misspellings, word fragments, suffixes)
vec_char = TfidfVectorizer(ngram_range=(2,5), max_features=20000, sublinear_tf=True, min_df=2, analyzer='char', max_df=0.90)
Xc_train = vec_char.fit_transform(X_train)
Xc_test = vec_char.transform(X_test)
print(f'Char features: {Xc_train.shape}')

# Combine features
X_train_combined = hstack([Xw_train, Xc_train])
X_test_combined = hstack([Xw_test, Xc_test])
print(f'Combined features: {X_train_combined.shape}')

# ── Logistic Regression ──
t0 = time.time()
lr = LogisticRegression(max_iter=2000, C=0.5, class_weight='balanced', solver='saga', n_jobs=-1, random_state=42)
lr.fit(X_train_combined, y_train)
pred_lr = lr.predict(X_test_combined)
acc_lr = accuracy_score(y_test, pred_lr)
print(f'LR (word+char): {acc_lr:.4f} [{time.time()-t0:.1f}s]')

# ── LinearSVC ──
t0 = time.time()
svm = LinearSVC(max_iter=3000, C=0.1, class_weight='balanced', dual='auto', random_state=42)
svm.fit(X_train_combined, y_train)
pred_svm = svm.predict(X_test_combined)
acc_svm = accuracy_score(y_test, pred_svm)
print(f'SVM (word+char): {acc_svm:.4f} [{time.time()-t0:.1f}s]')

# Best model
if acc_svm > acc_lr:
    best = svm
    best_acc = acc_svm
    best_name = 'SVM'
else:
    best = lr
    best_acc = acc_lr
    best_name = 'LR'

print(f'\nBest: {best_name} ({best_acc:.4f})')
label_names = ['clean','cyberbullying','harassment','hate_speech','threat','religious_hate']
print(classification_report(y_test, best.predict(X_test_combined), target_names=label_names, zero_division=0))
