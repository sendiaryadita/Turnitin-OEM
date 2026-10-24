
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

TEST_FILE = Path("dataset/academic_real_test.csv")

MODELS = {
    "Cross Encoder V1": {
        "path": "models/antikopas-cross-encoder",
        "threshold": 6.9515,
    },
    "Cross Encoder Academic V2": {
        "path": "models/antikopas-cross-encoder-academic-v2",
        "threshold": 2.1285,
    },
}

# ==========================================
# MEMBACA DATA
# ==========================================

def load_test_data():
    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {TEST_FILE}"
        )

    df = pd.read_csv(TEST_FILE)

    required = {"text_a", "text_b", "label"}

    if not required.issubset(df.columns):
        raise ValueError(
            f"Kolom wajib: {required}"
        )

    df = df.dropna(
        subset=["text_a", "text_b", "label"]
    ).copy()

    df["text_a"] = df["text_a"].astype(str).str.strip()
    df["text_b"] = df["text_b"].astype(str).str.strip()

    df["label"] = pd.to_numeric(
        df["label"], errors="raise"
    ).astype(int)

    if not df["label"].isin([0, 1]).all():
        raise ValueError("Label wajib 0 atau 1")

    if (
        df["text_a"].eq("").any()
        or df["text_b"].eq("").any()
    ):
        raise ValueError("Ada teks kosong")

    if df.duplicated(
        subset=["text_a", "text_b"]
    ).any():
        raise ValueError("Ada pasangan duplikat")

    if df["label"].nunique() < 2:
        raise ValueError(
            "Dataset harus punya label 0 dan 1"
        )

    return df.reset_index(drop=True)


# ==========================================
# PENGUJIAN MODEL
# ==========================================

def test_model(name, config, df):
    print(f"\n===== {name} =====")

    model = CrossEncoder(
        config["path"],
        num_labels=1,
        max_length=256,
    )

    pairs = list(zip(
        df["text_a"].tolist(),
        df["text_b"].tolist(),
    ))

    scores = model.predict(
        pairs,
        batch_size=16,
        show_progress_bar=True,
        activation_fct=torch.nn.Identity(),
    )

    scores = np.asarray(
        scores, dtype=float
    ).reshape(-1)

    threshold = config["threshold"]

    predictions = (
        scores >= threshold
    ).astype(int)

    actual = df["label"].to_numpy()

    tn, fp, fn, tp = confusion_matrix(
        actual,
        predictions,
        labels=[0, 1]
    ).ravel()

    result = {
        "model": name,
        "threshold": threshold,
        "accuracy": accuracy_score(
            actual, predictions
        ),
        "precision": precision_score(
            actual, predictions,
            zero_division=0
        ),
        "recall": recall_score(
            actual, predictions,
            zero_division=0
        ),
        "f1_score": f1_score(
            actual, predictions,
            zero_division=0
        ),
        "false_positive": int(fp),
        "false_negative": int(fn),
    }

    detail = df.copy()
    detail["model"] = name
    detail["raw_score"] = scores
    detail["threshold"] = threshold
    detail["prediction"] = predictions
    detail["correct"] = (
        predictions == actual
    )

    return result, detail


# ==========================================
# MAIN
# ==========================================

def main():
    print("=== UJI JURNAL ASLI ANTIKOPAS ===")

    df = load_test_data()

    print(f"Jumlah pasangan: {len(df)}")
    print("Distribusi label:")
    print(df["label"].value_counts())

    results = []
    details = []

    for name, config in MODELS.items():
        result, detail = test_model(
            name, config, df
        )

        results.append(result)
        details.append(detail)

    summary = pd.DataFrame(results)

    summary.to_csv(
        "hasil_uji_jurnal_asli.csv",
        index=False,
        encoding="utf-8-sig",
    )

    pd.concat(
        details, ignore_index=True
    ).to_csv(
        "detail_uji_jurnal_asli.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n===== HASIL PERBANDINGAN =====")
    print(summary.to_string(index=False))

    print("\nPengujian selesai!")
    print("Hasil: hasil_uji_jurnal_asli.csv")
    print("Detail: detail_uji_jurnal_asli.csv")


if __name__ == "__main__":
    main()
