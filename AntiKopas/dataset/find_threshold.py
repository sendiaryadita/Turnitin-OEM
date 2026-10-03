import sys
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from sentence_transformers import CrossEncoder


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


MODEL_PATH = "models/antikopas-cross-encoder"
TEST_PATH = "dataset/test.csv"


print("=" * 60)
print("CROSS ENCODER THRESHOLD SEARCH")
print("=" * 60)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(TEST_PATH)

print("\nTotal data:", len(df))

texts_a = df["text_a"].tolist()
texts_b = df["text_b"].tolist()
labels = df["label"].astype(int).tolist()


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading model...")

model = CrossEncoder(
    MODEL_PATH,
    num_labels=1,
    max_length=512
)


# ============================================================
# PREDICTION
# ============================================================

pairs = list(zip(texts_a, texts_b))

print("Predicting...")

scores = model.predict(
    pairs,
    show_progress_bar=True
)


# ============================================================
# SEARCH THRESHOLD
# ============================================================

results = []

thresholds = np.arange(
    -5.0,
    10.01,
    0.1
)


for threshold in thresholds:

    predictions = [
        1 if score >= threshold else 0
        for score in scores
    ]

    accuracy = accuracy_score(
        labels,
        predictions
    )

    precision = precision_score(
        labels,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        labels,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        labels,
        predictions,
        zero_division=0
    )

    results.append({
        "threshold": threshold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    })


# ============================================================
# SORT BY F1
# ============================================================

results.sort(
    key=lambda x: x["f1"],
    reverse=True
)


print("\n" + "=" * 60)
print("TOP THRESHOLDS")
print("=" * 60)


for result in results[:10]:

    print(
        f"Threshold: {result['threshold']:.2f} | "
        f"Accuracy: {result['accuracy']:.4f} | "
        f"Precision: {result['precision']:.4f} | "
        f"Recall: {result['recall']:.4f} | "
        f"F1: {result['f1']:.4f}"
    )


best = results[0]


print("\n" + "=" * 60)
print("BEST THRESHOLD")
print("=" * 60)

print(
    f"Threshold : {best['threshold']:.2f}"
)

print(
    f"Accuracy  : {best['accuracy']:.4f}"
)

print(
    f"Precision : {best['precision']:.4f}"
)

print(
    f"Recall    : {best['recall']:.4f}"
)

print(
    f"F1        : {best['f1']:.4f}"
)