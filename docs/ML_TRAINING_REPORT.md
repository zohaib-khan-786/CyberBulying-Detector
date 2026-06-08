# CyberGuard — Machine Learning Training Report

## Complete Technical Documentation of AI Model Development

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Definition](#2-problem-definition)
3. [Dataset Collection & Sources](#3-dataset-collection--sources)
4. [Data Preprocessing Pipeline](#4-data-preprocessing-pipeline)
5. [Feature Extraction — TF-IDF](#5-feature-extraction--tfidf)
6. [Model Selection & Justification](#6-model-selection--justification)
7. [Training Configuration](#7-training-configuration)
8. [Evaluation Results](#8-evaluation-results)
9. [Confusion Matrix Analysis](#9-confusion-matrix-analysis)
10. [Class Imbalance Handling](#10-class-imbalance-handling)
11. [Model Architecture in Production](#11-model-architecture-in-production)
12. [Limitations & Future Work](#12-limitations--future-work)
13. [References](#13-references)

---

## 1. Executive Summary

CyberGuard is an AI-powered cyberbullying detection system that classifies text into six categories: **clean**, **cyberbullying**, **harassment**, **hate_speech**, **threat**, and **religious_hate**. The system uses a classical Machine Learning approach combining **TF-IDF vectorization** with **Logistic Regression** as the production model and **Complement Naive Bayes** as a fast baseline.

The final model was trained on **68,472 balanced samples** sourced from **10 different Kaggle datasets** totaling **476,563 raw samples** (after deduplication). The Logistic Regression model achieved an overall accuracy of **74%** with a macro F1-score of **0.69** on the balanced test set.

---

## 2. Problem Definition

### 2.1 Classification Schema

The system classifies text into six categories:

| Label ID | Category | Description |
|----------|----------|-------------|
| 0 | `clean` | Non-toxic, neutral, or positive content |
| 1 | `cyberbullying` | Insults, name-calling, personal attacks, obscene language |
| 2 | `harassment` | Stalking, intimidation, repeated unwanted contact, threats of following |
| 3 | `hate_speech` | Discrimination against groups based on race, gender, ethnicity, age |
| 4 | `threat` | Direct threats of physical violence or harm |
| 5 | `religious_hate` | Attacks on religious groups, blasphemy, religious discrimination |

### 2.2 Why These Six Categories?

These categories were defined based on the project requirements and align with established taxonomies in cyberbullying research:

- **Clean vs. Toxic**: The fundamental binary distinction
- **Cyberbullying vs. Harassment**: Cyberbullying is typically public insults; harassment involves persistent, targeted behavior
- **Hate Speech**: Targets entire groups rather than individuals
- **Threat**: Requires immediate moderation action due to potential real-world harm
- **Religious Hate**: Specifically required for the Pakistani context where blasphemy and religious sensitivity are critical concerns

---

## 3. Dataset Collection & Sources

### 3.1 Datasets Used

Ten publicly available datasets from Kaggle were combined to create a comprehensive training corpus:

| # | Dataset Name | Kaggle Source | Original Size | Primary Use |
|---|---|---|---|---|
| 1 | Jigsaw Toxic Comment | `julian3833/jigsaw-toxic-comment-classification-challenge` | 159,571 rows | threat, hate, harassment, cyberbullying |
| 2 | Cyberbullying Classification | `andrewmvd/cyberbullying-classification` | 47,692 rows | religion, hate_speech, cyberbullying |
| 3 | Hate Speech & Offensive Language | `mrmorj/hate-speech-and-offensive-language-dataset` | 24,783 rows | hate_speech, cyberbullying |
| 4 | Toxic Tweets (FinalBalancedDataset) | `ashwiniyer176/toxic-tweets-dataset` | 56,745 rows | cyberbullying |
| 5 | Combined Hate Speech Dataset | `mahmoudabusaqer/combined-hate-speech-dataset` | 48,049 rows | hate_speech |
| 6 | Aggression Parsed Dataset | `saurabhshahane/cyberbullying-dataset` | 115,864 rows | harassment |
| 7 | Attack Parsed Dataset | `saurabhshahane/cyberbullying-dataset` | 115,864 rows | harassment |
| 8 | Twitter Racism | `sayankr007/multi-lingual-cyberbully-detection-15-languages` | 13,471 rows | hate_speech |
| 9 | Twitter Sexism | `sayankr007/multi-lingual-cyberbully-detection-15-languages` | 14,881 rows | hate_speech |
| 10 | Toxicity Parsed | `saurabhshahane/cyberbullying-dataset` | 159,686 rows | cyberbullying |

### 3.2 Dataset Descriptions

#### Jigsaw Toxic Comment Classification Challenge
- **Origin**: Wikipedia talk page edits, labeled by human reviewers
- **Columns**: `id`, `comment_text`, `malignant`, `highly_malignant`, `rude`, `threat`, `abuse`, `loathe`
- **Why chosen**: Industry-standard benchmark for toxic comment classification. Contains explicit `threat` column (478 samples) which is rare in other datasets. The `loathe` column maps well to hate_speech, and `highly_malignant` captures harassment patterns.

#### Cyberbullying Classification Dataset
- **Origin**: Twitter tweets labeled by category of cyberbullying
- **Columns**: `tweet_text`, `cyberbullying_type`
- **Categories**: `not_cyberbullying`, `age`, `ethnicity`, `gender`, `religion`, `other_cyberbullying`
- **Why chosen**: The ONLY publicly available dataset with an explicit `religion` category, which is critical for the religious_hate class required by the project.

#### Hate Speech & Offensive Language Dataset
- **Origin**: Twitter tweets, labeled via CrowdFlower crowdsourcing
- **Columns**: `tweet`, `class` (0=hate_speech, 1=offensive, 2=neither)
- **Why chosen**: Provides clean hate_speech samples (class 0) with 1,430 labeled examples. The distinction between hate_speech and offensive language helps the model learn the difference between group-targeted hate and individual insults.

#### Toxic Tweets Dataset (FinalBalancedDataset)
- **Origin**: Twitter, balanced binary toxicity classification
- **Columns**: `Toxicity`, `tweet`
- **Why chosen**: 56,745 balanced samples (32,592 clean, 24,153 toxic) provide a strong foundation for the cyberbullying class without the imbalance issues of other datasets.

#### Combined Hate Speech Dataset
- **Origin**: Aggregation of multiple hate speech datasets
- **Columns**: `text`, `class` (0=not_hate, 1=hate)
- **Why chosen**: 48,049 samples provide additional hate_speech diversity, combining sources from multiple platforms.

#### Aggression & Attack Parsed Datasets
- **Origin**: Wikipedia talk pages, labeled for aggression and attack behavior
- **Columns**: `index`, `Text`, `ed_label_0`, `ed_label_1`, `oh_label`
- **Why chosen**: These datasets contain 14,782 and 13,590 positive samples respectively for harassment-type behavior (aggression, personal attacks). This was critical for boosting the harassment class from 1,201 to 15,300 samples.

#### Twitter Racism & Sexism Datasets
- **Origin**: Twitter, annotated for racist and sexist content
- **Columns**: `index`, `id`, `Text`, `Annotation`, `oh_label`
- **Why chosen**: Provide 1,970 racism and 3,377 sexism samples that map directly to the hate_speech category, adding diversity to group-targeted hate content.

#### Toxicity Parsed Dataset
- **Origin**: Wikipedia talk pages, labeled for general toxicity
- **Columns**: `index`, `Text`, `ed_label_0`, `ed_label_1`, `oh_label`
- **Why chosen**: 15,362 positive toxicity samples provide additional cyberbullying training data from a different domain (Wikipedia vs. Twitter).

### 3.3 Label Mapping Strategy

Each dataset had different label formats. The following mapping was applied:

#### Jigsaw Dataset Mapping
```
threat == 1          → 4 (threat)
loathe == 1          → 3 (hate_speech)
highly_malignant == 1 → 2 (harassment)
malignant == 1 OR rude == 1 OR abuse == 1 → 1 (cyberbullying)
all zeros            → 0 (clean)
```
**Priority order**: threat > hate_speech > harassment > cyberbullying > clean

#### Cyberbullying Tweets Mapping
```
religion             → 5 (religious_hate)
ethnicity, gender, age → 3 (hate_speech)
other_cyberbullying  → 1 (cyberbullying)
not_cyberbullying    → 0 (clean)
```

#### Hate Speech & Offensive Mapping
```
class 0 (hate_speech) → 3 (hate_speech)
class 1 (offensive)   → 1 (cyberbullying)
class 2 (neither)     → 0 (clean)
```

#### Aggression/Attack/Toxicity Parsed Mapping
```
oh_label == 1 → 2 (harassment)  [for aggression/attack]
oh_label == 1 → 1 (cyberbullying) [for toxicity]
oh_label == 0 → 0 (clean)
```

### 3.4 Final Dataset Statistics

After merging all 10 datasets and deduplication:

| Metric | Value |
|--------|-------|
| Total raw rows | 756,603 |
| After deduplication | 477,116 |
| After removing short texts (<10 chars) | 476,563 |
| Final balanced training set | 68,472 |

#### Class Distribution (Balanced)

| Class | Samples | Percentage |
|-------|---------|------------|
| clean | 15,000 | 21.9% |
| cyberbullying | 15,000 | 21.9% |
| harassment | 15,000 | 21.9% |
| hate_speech | 15,000 | 21.9% |
| threat | 478 | 0.7% |
| religious_hate | 7,994 | 11.7% |

**Note**: Threat has only 478 samples because this is the maximum available across all 10 datasets. The Jigsaw dataset is the only source with labeled threat data.

---

## 4. Data Preprocessing Pipeline

### 4.1 Text Cleaning Steps

The preprocessing pipeline (`ml_pipeline/preprocess.py`) applies 12 sequential cleaning steps:

| Step | Operation | Purpose | Example |
|------|-----------|---------|---------|
| 1 | Unicode normalization (NFKC) | Normalize unicode characters | "café" → "cafe" |
| 2 | Lowercasing | Case normalization | "HATE" → "hate" |
| 3 | URL removal | Remove links | "visit http://..." → "visit " |
| 4 | Mention removal | Remove @mentions | "@user hello" → "hello" |
| 5 | Hashtag handling | Keep text, remove # | "#hate" → "hate" |
| 6 | HTML tag removal | Strip HTML markup | "&amp;" → "&" |
| 7 | Contraction expansion | Expand contractions | "don't" → "do not" |
| 8 | Slang expansion | Expand internet slang | "kys" → "kill yourself" |
| 9 | Repeated character reduction | Normalize elongation | "stuppppid" → "stupid" |
| 10 | Punctuation removal | Remove special chars | "hate!!!" → "hate" |
| 11 | Number removal | Remove digits | "hate123" → "hate" |
| 12 | Whitespace normalization | Clean spacing | "hate  you" → "hate you" |

### 4.2 Contraction & Slang Expansion

The pipeline includes a lookup table for common contractions and cyberbullying-specific slang:

**Contractions**: "don't" → "do not", "won't" → "will not", "can't" → "cannot", etc.

**Cyberbullying Slang** (critical for social media text):
- "kys" → "kill yourself"
- "stfu" → "shut up"
- "gtfo" → "get out"
- "smh" → "shaking my head"
- "tbh" → "to be honest"
- "idc" → "i do not care"
- "imo" → "in my opinion"
- "fwiw" → "for what it is worth"

### 4.3 Why These Specific Steps?

1. **Unicode normalization**: Social media text contains special characters, emojis, and non-ASCII text
2. **Contraction expansion**: "don't" and "do not" should be treated as the same token
3. **Slang expansion**: "kys" is a strong cyberbullying indicator but would be missed without expansion
4. **Repeated character reduction**: Users elongate words for emphasis ("sooooo stupid")
5. **Hashtag handling**: Hashtags contain meaningful text but the # symbol adds noise

---

## 5. Feature Extraction — TF-IDF

### 5.1 What is TF-IDF?

**TF-IDF (Term Frequency-Inverse Document Frequency)** converts text into numerical vectors. It measures how important a word is to a document relative to the entire corpus.

- **TF (Term Frequency)**: How often a word appears in a document
- **IDF (Inverse Document Frequency)**: How rare a word is across all documents
- **TF-IDF = TF × IDF**: Words that are frequent in a document but rare overall get high scores

### 5.2 TF-IDF Configuration

```python
TfidfVectorizer(
    ngram_range=(1, 2),      # Unigrams + bigrams
    max_features=50,000,      # Top 50K features
    sublinear_tf=True,        # Apply log normalization
    strip_accents="unicode",  # Remove accents
    analyzer="word",          # Word-level analysis
    min_df=2,                 # Minimum document frequency
)
```

### 5.3 Why This Configuration?

| Parameter | Value | Justification |
|-----------|-------|---------------|
| `ngram_range=(1,2)` | Unigrams + Bigrams | Captures "not good" as a single feature instead of "not" and "good" separately. Bigrams are critical for negation detection in cyberbullying. |
| `max_features=50,000` | 50K features | Balances vocabulary coverage with computational efficiency. 50K captures most meaningful terms without excessive dimensionality. |
| `sublinear_tf=True` | Log normalization | Applies `1 + log(tf)` instead of raw frequency. Prevents very frequent words from dominating. A word appearing 100 times is not 100x more important than one appearing once. |
| `min_df=2` | Minimum 2 occurrences | Removes hapax legomena (words appearing only once). Reduces noise from typos and misspellings. |

### 5.4 Why TF-IDF Over Word Embeddings?

**TF-IDF was chosen over word2vec, GloVe, or BERT embeddings because:**

1. **Interpretability**: TF-IDF features are directly interpretable (each feature is a word/n-gram)
2. **Speed**: TF-IDF vectorization is orders of magnitude faster than embedding computation
3. **No GPU required**: Embedding models (BERT, RoBERTa) require GPU for reasonable inference speed
4. **Proven baseline**: TF-IDF + Logistic Regression is a well-established baseline for text classification
5. **Low latency**: Critical for real-time webhook processing where each comment must be classified in milliseconds

---

## 6. Model Selection & Justification

### 6.1 Primary Model: Logistic Regression

**Why Logistic Regression?**

1. **Interpretability**: Coefficients show which words contribute to each class prediction
2. **Speed**: Training takes seconds; inference takes microseconds
3. **Multinomial variant**: Natively handles multi-class classification
4. **Class weighting**: Built-in `class_weight="balanced"` handles imbalanced data
5. **Well-understood**: Extensive theoretical foundation and proven performance on text classification
6. **Linear decision boundary**: Works well with TF-IDF features which are already in a high-dimensional space

**Configuration:**
```python
LogisticRegression(
    max_iter=1000,           # Maximum iterations for convergence
    C=1.0,                   # Regularization strength (inverse)
    class_weight="balanced", # Auto-adjust weights for imbalanced classes
    solver="lbfgs",          # Limited-memory BFGS optimizer
    multi_class="auto",      # Auto-select OvR or multinomial
)
```

**Parameter Justification:**

| Parameter | Value | Why |
|-----------|-------|-----|
| `max_iter=1000` | 1000 iterations | Ensures convergence even with 50K features and 68K samples |
| `C=1.0` | Default regularization | Moderate regularization prevents overfitting without underfitting |
| `class_weight="balanced"` | Automatic weighting | Adjusts weights inversely proportional to class frequencies. Critical for handling the threat class (478 samples vs. 15,000 for other classes) |
| `solver="lbfgs"` | L-BFGS optimizer | Memory-efficient quasi-Newton method, works well for multiclass problems |

### 6.2 Baseline Model: Complement Naive Bayes

**Why Complement Naive Bayes?**

1. **Fast training**: Training is O(n) — linear in the number of samples
2. **Fast inference**: Prediction requires only a few multiplication operations
3. **ComplementNB vs. MultinomialNB**: ComplementNB uses the complement of each class to estimate parameters, making it better for imbalanced datasets
4. **No hyperparameter tuning needed**: Works well with default parameters
5. **Probabilistic output**: Provides well-calibrated probability estimates

**Configuration:**
```python
ComplementNB(alpha=0.5)
```

**Why alpha=0.5?**
- `alpha` is the Laplace smoothing parameter
- `alpha=1.0` (default) adds too much smoothing for this dataset
- `alpha=0.5` provides lighter smoothing, allowing the model to better distinguish between similar classes
- Lower alpha values risk zero-probability for unseen features

### 6.3 Models Considered but Not Used

| Model | Reason for Rejection |
|-------|---------------------|
| **SVM (Support Vector Machine)** | Slower training on 68K samples; marginal improvement over LR not worth the cost |
| **Random Forest** | Higher memory usage; less interpretable than LR for text classification |
| **XGBoost/LightGBM** | Requires extensive hyperparameter tuning; overkill for a TF-IDF feature space |
| **BERT/RoBERTa** | Requires GPU; inference latency too high for real-time webhook processing; model size >400MB |
| **LSTM/GRU** | Requires GPU training; longer development time; marginal improvement over LR+TF-IDF |
| **CNN for text** | Requires GPU; more complex pipeline; not justified for a 6-class problem |

---

## 7. Training Configuration

### 7.1 Train/Test Split

```python
train_test_split(
    test_size=0.2,        # 20% test, 80% train
    random_state=42,      # Reproducibility seed
    stratify=df["label"]  # Maintain class distribution in both sets
)
```

**Why 80/20 split?**
- Standard split ratio in machine learning
- 20% test provides ~13,695 samples for reliable evaluation
- Stratification ensures each class is proportionally represented

**Why stratified split?**
- Without stratification, the threat class (478 samples) might have very few or zero test samples
- Stratification guarantees proportional representation of all classes

### 7.2 Training Process

```
Step 1: Load CSV data
Step 2: Apply text preprocessing (12 cleaning steps)
Step 3: Train/test split (80/20, stratified)
Step 4: Build TF-IDF + Logistic Regression pipeline
Step 5: Fit pipeline on training data
Step 6: Evaluate on test data
Step 7: Save model and vectorizer as .pkl files
Step 8: Build TF-IDF + ComplementNB pipeline
Step 9: Fit pipeline on training data
Step 10: Evaluate on test data
Step 11: Save Naive Bayes model
```

### 7.3 Hardware & Training Time

- **Training environment**: CPU-only (Intel/AMD x86_64)
- **Training time**: ~30 seconds for Logistic Regression, ~15 seconds for Naive Bayes
- **Memory usage**: ~2GB peak during TF-IDF vectorization of 68K samples

---

## 8. Evaluation Results

### 8.1 Logistic Regression (Production Model)

```
                precision    recall  f1-score   support

         clean       0.75      0.84      0.79      3000
 cyberbullying       0.71      0.57      0.63      3000
    harassment       0.63      0.70      0.67      3000
   hate_speech       0.87      0.76      0.81      3000
        threat       0.24      0.50      0.32        96
religious_hate       0.85      0.94      0.89      1599

      accuracy                           0.74     13695
     macro avg       0.67      0.72      0.69     13695
  weighted avg       0.75      0.74      0.74     13695
```

### 8.2 Complement Naive Bayes (Baseline)

```
                precision    recall  f1-score   support

         clean       0.68      0.81      0.74      3000
 cyberbullying       0.77      0.48      0.59      3000
    harassment       0.62      0.66      0.64      3000
   hate_speech       0.79      0.76      0.78      3000
        threat       0.06      0.01      0.02        96
religious_hate       0.72      0.98      0.83      1599

      accuracy                           0.71     13695
     macro avg       0.61      0.62      0.60     13695
  weighted avg       0.71      0.71      0.70     13695
```

### 8.3 Model Comparison

| Metric | Logistic Regression | Complement NB | Winner |
|--------|-------------------|---------------|--------|
| Overall Accuracy | 74% | 71% | LR |
| Macro F1 | 0.69 | 0.60 | LR |
| Weighted F1 | 0.74 | 0.70 | LR |
| Clean F1 | 0.79 | 0.74 | LR |
| Cyberbullying F1 | 0.63 | 0.59 | LR |
| Harassment F1 | 0.67 | 0.64 | LR |
| Hate Speech F1 | 0.81 | 0.78 | LR |
| Threat F1 | 0.32 | 0.02 | LR |
| Religious Hate F1 | 0.89 | 0.83 | LR |
| Training Time | ~30s | ~15s | NB |
| Inference Latency | ~1ms | ~0.5ms | NB |

**Logistic Regression wins on all accuracy metrics. Naive Bayes wins on speed.**

---

## 9. Confusion Matrix Analysis

### 9.1 Logistic Regression Confusion Matrix

```
              clean  cyber  harass  hate  threat  religion
clean         2527    162    207     69     10       25
cyberbullying  342   1721    753    143     16       25
harassment     340    323   2101     83    121       32
hate_speech    131    206    195   2272      8      188
threat           3      2     41      0     48        2
religion        26      9     13     47      0     1504
```

### 9.2 Key Observations

1. **Clean ↔ Cyberbullying confusion** (162 + 342 = 504 errors): Mild insults sometimes appear clean; sarcastic "clean" text sometimes appears toxic
2. **Cyberbullying → Harassment confusion** (753 errors): The biggest error source. Cyberbullying and harassment overlap significantly — both involve personal attacks
3. **Harassment → Cyberbullying confusion** (323 errors): Confirms the boundary between these classes is fuzzy
4. **Hate Speech → Religious Hate confusion** (188 errors): Religious hate is a subset of hate speech; some religious attacks are also general hate
5. **Threat → Harassment confusion** (41 errors): Threats and harassment share intimidating language patterns

---

## 10. Class Imbalance Handling

### 10.1 The Imbalance Problem

The raw merged dataset (476,563 rows) was severely imbalanced:

| Class | Raw Count | Percentage |
|-------|-----------|------------|
| clean | 376,506 | 79.0% |
| cyberbullying | 41,918 | 8.8% |
| hate_speech | 34,367 | 7.2% |
| harassment | 15,300 | 3.2% |
| religious_hate | 7,994 | 1.7% |
| threat | 478 | 0.1% |

### 10.2 Balancing Strategy

A hybrid approach was used:

1. **Undersampling majority classes**: Clean (376K → 15K), Cyberbullying (42K → 15K), Hate Speech (34K → 15K)
2. **Keeping minority classes as-is**: Harassment (15K), Religious Hate (8K), Threat (478)
3. **Class weighting in the model**: `class_weight="balanced"` automatically adjusts weights inversely proportional to class frequencies

### 10.3 Why Not SMOTE/Oversampling?

- **SMOTE** (Synthetic Minority Over-sampling Technique) generates synthetic samples by interpolating between existing samples
- For text data, SMOTE operates on TF-IDF vectors, producing "synthetic" text that may not be grammatically valid
- Undersampling + class weighting was preferred because it preserves the quality of all training samples

---

## 11. Model Architecture in Production

### 11.1 Inference Pipeline

```
User Input Text
      ↓
Text Preprocessing (12 steps)
      ↓
TF-IDF Vectorization (50K features)
      ↓
Logistic Regression Prediction
      ↓
PredictionResult {
    label: "cyberbullying",
    label_id: 1,
    confidence: 0.87,
    scores: {clean: 0.05, cyberbullying: 0.87, ...},
    is_harmful: true,
    severity: "high",
    color: "#f97316"
}
```

### 11.2 Severity Classification

Predictions are mapped to severity levels:

| Severity | Condition | Color |
|----------|-----------|-------|
| `none` | label == "clean" | Green (#22c55e) |
| `low` | confidence < 0.5 | Yellow (#fbbf24) |
| `medium` | confidence 0.5-0.7 | Orange (#f97316) |
| `high` | confidence 0.7-0.85 | Red (#ef4444) |
| `critical` | confidence > 0.85 OR label is threat/hate_speech | Dark Red (#dc2626) |

### 11.3 Saved Model Files

```
backend/models/saved_models/
├── lr_model.pkl        (2.4 MB) — Logistic Regression classifier
├── nb_model.pkl        (5.2 MB) — Complement Naive Bayes classifier
└── vectorizer.pkl      (1.9 MB) — TF-IDF vectorizer (shared)
```

---

## 12. Limitations & Future Work

### 12.1 Current Limitations

1. **Threat class underperformance** (F1=0.32): Only 478 samples available across all public datasets
2. **English-only**: The model only processes English text. No multilingual support in the sklearn pipeline
3. **No context awareness**: Each comment is classified independently; the model cannot see conversation context
4. **Sarcasm detection**: Sarcastic comments ("Oh great, another brilliant idea") may be misclassified
5. **Evolving language**: New slang and coded language emerge constantly; the model requires periodic retraining

### 12.2 Future Improvements

1. **Transformer-based model**: Fine-tune BERT or RoBERTa for higher accuracy (requires GPU)
2. **Active learning**: Use human moderator feedback to continuously improve the model
3. **Multilingual support**: Integrate language detection + language-specific models (RobBERT for Dutch, etc.)
4. **Data augmentation**: Use back-translation or paraphrase generation to expand the threat class
5. **Ensemble methods**: Combine LR predictions with transformer predictions for higher confidence

---

## 13. References

1. Wulczyn, E., Thain, N., & Dixon, L. (2017). "Ex Machina: Personal Attacks Seen at Scale." *Proceedings of the 26th International Conference on World Wide Web*.

2. Davidson, T., Warmsley, D., Macy, M., & Weber, I. (2017). "Automated Hate Speech Detection and the Problem of Offensive Language." *Proceedings of the International AAAI Conference on Web and Social Media*.

3. Founta, A. M., et al. (2018). "Large Scale Crowdsourcing and Characterization of Twitter Abusive Behavior." *Proceedings of the International AAAI Conference on Web and Social Media*.

4. Zampieri, M., et al. (2019). "SemEval-2019 Task 6: Identifying and Categorizing Offensive Language in Social Media (OffensEval)." *Proceedings of SemEval*.

5. Basile, V., et al. (2019). "SemEval-2019 Task 5: Multilingual Detection of Hate Speech Against Immigrants and Women in Twitter." *Proceedings of SemEval*.

6. Salminen, J., et al. (2018). "Anatomy of Online Hate: Developing a Taxonomy and Machine Learning Models for Identifying and Classifying Hate in Online News Media." *Proceedings of the International AAAI Conference on Web and Social Media*.

7. Chatzakou, D., et al. (2017). "Mean Birds: Detecting Aggression and Bullying on Twitter." *Proceedings of the ACM Web Science Conference*.

8. Kumar, R., & Ojha, A. K. (2020). "Benchmarking Aggression Identification in Social Media." *Proceedings of the Second Workshop on Trolling, Aggression and Cyberbullying*.

9. Rennie, J. D., et al. (2003). "Tackling the Poor Assumptions of Naive Bayes Text Classifiers." *Proceedings of the 20th International Conference on Machine Learning*.

10. Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press.
