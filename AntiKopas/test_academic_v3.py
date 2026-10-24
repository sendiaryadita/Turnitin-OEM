
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from sentence_transformers import CrossEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

# ======================================
# KONFIGURASI
# ======================================

VALIDATION_FILE = Path(
    "dataset/academic_v2/academic_validation_v2.csv"
)

# Sementara untuk uji diagnostik.
# Dataset ini sudah pernah dianalisis, jadi
# bukan test independen untuk kesimpulan final.
TEST_FILE = Path(
    "dataset/academic_real_test.csv"
)

MODELS = {
    "Academic V2": {
        "path": "models/antikopas-cross-encoder-academic-v2",
        "threshold": 2.1285,
    },
    "Academic V3": {
        "path": "models/antikopas-cross-encoder-academic-v3",
        "threshold": None,
    },
}


# ======================================
# BACA DATASET
# ======================================

def read_data(path):
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset tidak ditemukan: {path}"
        )

    df = pd.read_csv(path)

    columns = {"text_a", "text_b", "label"}

    if not columns.issubset(df.columns):
        raise ValueError(
            f"Kolom tidak lengkap pada {path}"
        )

    df = df.dropna(
        subset=["text_a", "text_b", "label"]
    ).copy()

    df["label"] = pd.to_numeric(
        df["label"], errors="raise"
    ).astype(int)

    if not df["label"].isin([0, 1]).all():
        raise ValueError("Label harus 0 atau 1")

    if df["label"].nunique() < 2:
        raise ValueError(
            "Dataset harus memiliki dua kelas"
        )

    return df.reset_index(drop=True)


# ======================================
# PREDIKSI RAW SCORE
# ======================================

def predict(model, df):
    pairs = list(zip(
        df["text_a"].astype(str),
        df["text_b"].astype(str),
    ))

    scores = model.predict(
        pairs,
        batch_size=16,
        show_progress_bar=True,
        activation_fn=torch.nn.Identity(),
    )

    scores = np.asarray(
        scores, dtype=float
    ).reshape(-1)

    if not np.isfinite(scores).all():
        raise ValueError("Skor model tidak valid")

    return scores


# ======================================
# PILIH THRESHOLD DARI VALIDATION
# ======================================

def find_threshold(y_true, scores):
    best_threshold = None
    best_f1 = -1

    for threshold in np.unique(scores):
        pred = (scores >= threshold).astype(int)

        f1 = f1_score(
            y_true,
            pred,
            zero_division=0,
        )

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = float(threshold)

    return best_threshold


# ======================================
# EVALUASI
# ======================================

def evaluate(name, config, val_df, test_df):
    print(f"\n=== {name} ===")

    path = config["path"]

    if not Path(path).is_dir():
        raise FileNotFoundError(path)

    model = CrossEncoder(
        path,
        num_labels=1,
        max_length=256,
    )

    threshold = config["threshold"]

    if threshold is None:
        print("Menentukan threshold dari validation...")

        val_scores = predict(model, val_df)

        threshold = find_threshold(
            val_df["label"].to_numpy(),
            val_scores,
        )

    print(f"Threshold: {threshold:.4f}")

    print("Menguji pasangan teks...")
    scores = predict(model, test_df)

    actual = test_df["label"].to_numpy()
    predicted = (scores >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        actual,
        predicted,
        labels=[0, 1],
    ).ravel()

    result = {
        "model": name,
        "threshold": round(threshold, 4),
        "accuracy": round(
            accuracy_score(actual, predicted), 4
        ),
        "precision": round(
            precision_score(
                actual, predicted, zero_division=0
            ), 4
        ),
        "recall": round(
            recall_score(
                actual, predicted, zero_division=0
            ), 4
        ),
        "f1_score": round(
            f1_score(
                actual, predicted, zero_division=0
            ), 4
        ),
        "false_positive": int(fp),
        "false_negative": int(fn),
    }

    detail = test_df.copy()
    detail["model"] = name
    detail["raw_score"] = scores
    detail["threshold"] = threshold
    detail["prediction"] = predicted
    detail["correct"] = actual == predicted

    print(result)

    return result, detail


# ======================================
# MAIN
# ======================================

def main():
    print("=== PERBANDINGAN ACADEMIC V2 VS V3 ===")

    validation = read_data(VALIDATION_FILE)
    test = read_data(TEST_FILE)

    print("Validation:", len(validation))
    print("Test:", len(test))

    results = []
    details = []

    for name, config in MODELS.items():
        result, detail = evaluate(
            name,
            config,
            validation,
            test,
        )

        results.append(result)
        details.append(detail)

    summary = pd.DataFrame(results)

    summary.to_csv(
        "hasil_perbandingan_v2_v3.csv",
        index=False,
        encoding="utf-8-sig",
    )

    pd.concat(
        details, ignore_index=True
    ).to_csv(
        "detail_perbandingan_v2_v3.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n===================================")
    print("HASIL PERBANDINGAN V2 VS V3")
    print("===================================")
    print(summary.to_string(index=False))

    print("\nPENGUJIAN SELESAI!")


if __name__ == "__main__":
    main()
