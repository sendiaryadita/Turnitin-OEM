
import json
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

# ==========================================
# KONFIGURASI
# ==========================================

MODEL_PATH = "models/antikopas-cross-encoder-academic-v2"

VAL_PATH = "dataset/academic_v2/academic_validation_v2.csv"
TEST_PATH = "dataset/academic_v2/academic_test_v2.csv"

OLD_THRESHOLD = 2.1285

# Target precision minimum saat validasi
MIN_PRECISION = 0.85


# ==========================================
# LOAD DATASET
# ==========================================

def load_data(path):
    df = pd.read_csv(path)

    required = {"text_a", "text_b", "label"}
    if not required.issubset(df.columns):
        raise ValueError(f"Kolom tidak sesuai: {path}")

    df = df.dropna(
        subset=["text_a", "text_b", "label"]
    ).copy()

    df["label"] = pd.to_numeric(
        df["label"], errors="raise"
    )

    if not df["label"].isin([0, 1]).all():
        raise ValueError("Label harus 0 atau 1")

    return df


# ==========================================
# PREDIKSI RAW SCORE
# ==========================================

def get_scores(model, df):
    pairs = list(zip(
        df["text_a"].astype(str),
        df["text_b"].astype(str)
    ))

    scores = model.predict(
        pairs,
        batch_size=16,
        show_progress_bar=True,
        activation_fct=torch.nn.Identity(),
    )

    return np.asarray(scores, dtype=float).reshape(-1)


# ==========================================
# HITUNG METRIK
# ==========================================

def metrics(y_true, scores, threshold):
    y_pred = (scores >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    ).ravel()

    return {
        "threshold": float(threshold),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(
            y_true, y_pred, zero_division=0
        ),
        "recall": recall_score(
            y_true, y_pred, zero_division=0
        ),
        "f1": f1_score(
            y_true, y_pred, zero_division=0
        ),
        "false_positive": int(fp),
        "false_negative": int(fn),
    }


def show_result(title, result):
    print(f"\n=== {title} ===")
    print(f"Threshold      : {result['threshold']:.4f}")
    print(f"Accuracy       : {result['accuracy']:.4f}")
    print(f"Precision      : {result['precision']:.4f}")
    print(f"Recall         : {result['recall']:.4f}")
    print(f"F1 Score       : {result['f1']:.4f}")
    print(f"False Positive : {result['false_positive']}")
    print(f"False Negative : {result['false_negative']}")


# ==========================================
# MAIN
# ==========================================

def main():
    print("=== OPTIMASI THRESHOLD ANTIKOPAS V2 ===")

    if not Path(MODEL_PATH).is_dir():
        raise FileNotFoundError(MODEL_PATH)

    val_df = load_data(VAL_PATH)
    test_df = load_data(TEST_PATH)

    print("Memuat Cross Encoder Academic V2...")

    model = CrossEncoder(
        MODEL_PATH,
        num_labels=1,
        max_length=256,
    )

    # Tahap 1: optimasi hanya pada validation
    print("\nMemproses validation...")
    val_scores = get_scores(model, val_df)

    y_val = val_df["label"].to_numpy(dtype=int)

    old_val = metrics(
        y_val, val_scores, OLD_THRESHOLD
    )

    candidates = np.unique(val_scores)

    results = [
        metrics(y_val, val_scores, threshold)
        for threshold in candidates
    ]

    # Pertahankan precision minimal 85%
    eligible = [
        r for r in results
        if r["precision"] >= MIN_PRECISION
    ]

    if eligible:
        # Prioritas recall, lalu F1, lalu precision
        best = max(
            eligible,
            key=lambda r: (
                r["recall"],
                r["f1"],
                r["precision"],
            )
        )
        print("\nTarget precision validasi terpenuhi.")
    else:
        # Cadangan: pilih F1 validasi tertinggi
        best = max(
            results,
            key=lambda r: r["f1"]
        )
        print("\nTarget precision tidak tercapai.")
        print("Menggunakan F1 validasi terbaik.")

    new_threshold = best["threshold"]

    show_result("VALIDATION - THRESHOLD LAMA", old_val)
    show_result("VALIDATION - THRESHOLD BARU", best)

    # Tahap 2: uji sekali pada test
    # Test tidak dipakai untuk memilih threshold
    print("\nMemproses test...")
    test_scores = get_scores(model, test_df)

    y_test = test_df["label"].to_numpy(dtype=int)

    old_test = metrics(
        y_test, test_scores, OLD_THRESHOLD
    )

    new_test = metrics(
        y_test, test_scores, new_threshold
    )

    show_result("TEST - THRESHOLD LAMA", old_test)
    show_result("TEST - THRESHOLD BARU", new_test)

    # Simpan hasil untuk ditinjau, belum diterapkan
    summary = pd.DataFrame([
        {"evaluasi": "validation_lama", **old_val},
        {"evaluasi": "validation_baru", **best},
        {"evaluasi": "test_lama", **old_test},
        {"evaluasi": "test_baru", **new_test},
    ])

    summary.to_csv(
        "hasil_optimasi_threshold_v2.csv",
        index=False
    )

    config = {
        "model": MODEL_PATH,
        "candidate_threshold": new_threshold,
        "selection_split": "validation",
        "minimum_validation_precision": MIN_PRECISION,
        "status": "belum_diterapkan",
    }

    with open(
        "threshold_v2_candidate.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(config, f, indent=2)

    print("\n================================")
    print("OPTIMASI SELESAI!")
    print("hasil_optimasi_threshold_v2.csv")
    print("threshold_v2_candidate.json")
    print("================================")


if __name__ == "__main__":
    main()
