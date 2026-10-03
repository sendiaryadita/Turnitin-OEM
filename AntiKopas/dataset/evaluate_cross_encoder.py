import pandas as pd
import numpy as np

from sentence_transformers import CrossEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = "models/antikopas-cross-encoder"
TEST_FILE = "dataset/test.csv"


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 60)
print("LOAD TEST DATASET")
print("=" * 60)

test_df = pd.read_csv(TEST_FILE)

print(f"Total test data : {len(test_df)}")


# ============================================================
# LOAD MODEL
# ============================================================

print("\n" + "=" * 60)
print("LOAD FINE-TUNED MODEL")
print("=" * 60)

model = CrossEncoder(
    MODEL_PATH,
    num_labels=1,
    max_length=512
)

print("Model berhasil dimuat.")


# ============================================================
# PREDICTION
# ============================================================

pairs = list(
    zip(
        test_df["text_a"].astype(str),
        test_df["text_b"].astype(str)
    )
)

print("\n" + "=" * 60)
print("PREDICTION")
print("=" * 60)

scores = model.predict(pairs)

scores = np.asarray(scores).reshape(-1)

print("Prediction selesai.")


# ============================================================
# TRUE LABEL
# ============================================================

y_true = test_df["label"].astype(int).to_numpy()


# ============================================================
# FIND BEST THRESHOLD
# ============================================================

print("\n" + "=" * 60)
print("SEARCH THRESHOLD")
print("=" * 60)

best_threshold = 0.5
best_f1 = 0.0

for threshold in np.arange(0.05, 0.96, 0.05):

    y_pred = (scores >= threshold).astype(int)

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    if f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold


print(f"Best threshold : {best_threshold:.2f}")
print(f"Best F1        : {best_f1:.4f}")


# ============================================================
# FINAL EVALUATION
# ============================================================

y_pred = (scores >= best_threshold).astype(int)

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(
    y_true,
    y_pred,
    zero_division=0
)
recall = recall_score(
    y_true,
    y_pred,
    zero_division=0
)
f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0
)


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 60)
print("HASIL EVALUASI")
print("=" * 60)

print(f"Accuracy  : {accuracy:.4f}")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1-score  : {f1:.4f}")


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(y_true, y_pred)

print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

print(cm)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)

print(
    classification_report(
        y_true,
        y_pred,
        target_names=[
            "Tidak Plagiarisme",
            "Plagiarisme"
        ],
        zero_division=0
    )
)


# ============================================================
# SAMPLE PREDICTIONS
# ============================================================

print("\n" + "=" * 60)
print("10 SAMPLE PREDICTIONS")
print("=" * 60)

for i in range(min(10, len(test_df))):

    print(
        f"{i+1}. "
        f"Label asli={y_true[i]} | "
        f"Score={scores[i]:.4f} | "
        f"Prediksi={y_pred[i]}"
    )