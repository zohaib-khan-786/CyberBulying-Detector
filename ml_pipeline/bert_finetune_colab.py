# ──────────────────────────────────────────────────────────────────────
# BERT Fine-tuning for Cyberbullying Detection (6 classes)
# Run this in Google Colab with T4 GPU runtime
# ──────────────────────────────────────────────────────────────────────

# 1. Install dependencies
!pip install -q transformers datasets pandas scikit-learn torch accelerate

import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    Trainer, TrainingArguments, EarlyStoppingCallback
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# 2. Upload your dataset
# Run this cell, then click "Choose Files" and select merged_dataset_v3.csv
from google.colab import files
uploaded = files.upload()
filename = list(uploaded.keys())[0]
df = pd.read_csv(filename)

LABELS = {0: "clean", 1: "cyberbullying", 2: "harassment", 3: "hate_speech", 4: "threat", 5: "religious_hate"}
label_names = [LABELS[i] for i in sorted(LABELS)]
num_labels = len(label_names)

print(f"Rows: {len(df)}")
print(f"Distribution:\n{df['label'].value_counts().sort_index()}")

# 3. Balance the dataset (cap each class)
MAX_PER_CLASS = 8000
balanced = []
for label_id in sorted(df['label'].unique()):
    subset = df[df['label'] == label_id]
    if len(subset) > MAX_PER_CLASS:
        subset = subset.sample(n=MAX_PER_CLASS, random_state=42)
    elif len(subset) < 500 and label_id != 0:
        n_needed = min(2000, MAX_PER_CLASS)
        dupes = subset.sample(n=n_needed - len(subset), replace=True, random_state=42)
        subset = pd.concat([subset, dupes])
    balanced.append(subset)
df = pd.concat(balanced, ignore_index=True)
print(f"Balanced: {len(df)} rows")
print(df['label'].value_counts().sort_index())

# 4. Split
X_train, X_test, y_train, y_test = train_test_split(
    df['text'].astype(str).tolist(), df['label'].tolist(),
    test_size=0.2, random_state=42, stratify=df['label']
)
print(f"Train: {len(X_train)}, Test: {len(X_test)}")

# 5. Tokenize
MODEL_NAME = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

class ToxicDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
    def __len__(self):
        return len(self.texts)
    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True, padding='max_length',
            max_length=self.max_len, return_tensors='pt'
        )
        return {
            'input_ids': enc['input_ids'].squeeze(0),
            'attention_mask': enc['attention_mask'].squeeze(0),
            'labels': torch.tensor(self.labels[idx], dtype=torch.long)
        }

train_ds = ToxicDataset(X_train, y_train, tokenizer)
test_ds = ToxicDataset(X_test, y_test, tokenizer)

# 6. Load model
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=num_labels
)

# 7. Training config
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=6,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    warmup_steps=200,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=50,
    eval_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True,
    metric_for_best_model='eval_f1_macro',
    greater_is_better=True,
    save_total_limit=2,
    fp16=True,  # enables mixed precision (faster on T4)
)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    acc = accuracy_score(labels, preds)
    f1_macro = f1_score(labels, preds, average='macro')
    return {'eval_accuracy': acc, 'eval_f1_macro': f1_macro}

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=test_ds,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
)

# 8. TRAIN (this takes ~30-60 min on T4 GPU)
print("Starting training...")
trainer.train()

# 9. Evaluate
print("\n=== Evaluation ===")
results = trainer.evaluate()
preds = trainer.predict(test_ds)
y_pred = np.argmax(preds.predictions, axis=1)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred, target_names=label_names, zero_division=0))

# 10. Save model
model.save_pretrained('cyberbullying_bert')
tokenizer.save_pretrained('cyberbullying_bert')
!zip -r cyberbullying_bert.zip cyberbullying_bert

# 11. Download the model
files.download('cyberbullying_bert.zip')

print("\n✅ Done! Download the model and place it in backend/models/saved_models/")
