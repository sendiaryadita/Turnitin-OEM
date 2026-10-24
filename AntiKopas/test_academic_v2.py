
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

# =========================================
# KONFIGURASI
# =========================================

DATA_DIR = Path("dataset/academic_v2")

VAL_FILE = DATA_DIR / "academic_validation_v2.csv"
TEST_FILE = DATA_DIR / "academic_test_v2.csv"

MODELS = {
    "Cross Encoder V1": "models/antikopas-cross-encoder",
    "Cross Encoder Academic V2":
        "models/antikopas-cross-encoder-academic-v2",
}

OUTPUT_FILE = Path("hasil_uji_cross_encoder_v2.csv")
DETAIL_FILE = Path("detail_prediksi_academic_v2.csv")


# =========================================
# MEMBACA DATASET
# =========================================

def load_data(path):
    if not path.is_file():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {path}")

    df = pd.read_csv(path)

    required = {"text_a", "text_b", "label"}
    if not required.issubset(df.columns):
        raise ValueError(
            f"Kolom salah di {path}: {list(df.columns)}"
        )

    df = df.dropna(subset=["text_a", "text_b", "label"])
    df["label"] = pd.to_numeric(df["label"])

    if not df["label"].isin([0, 1]).all():
        raise ValueError("Label harus 0 atau 1")

    return df.reset_index(drop=True)


def predict_scores(model, df):
    pairs = list(zip(
        df["text_a"].astype(str).tolist(),
        df["text_b"].astype(str).tolist(),
    ))

    # Paksa output menjadi raw logit, bukan persen
    scores = model.predict(
        pairs,
        batch_size=16,
        show_progress_bar=True,
        activation_fct=torch.nn.Identity(),
    )

    scores = np.asarray(scores, dtype=float).reshape(-1)

    if not np.isfinite(scores).all():
        raise ValueError("Ditemukan skor model tidak valid")

    return scores


# =========================================
# PILIH THRESHOLD DARI VALIDATION
# =========================================

def find_best_threshold(y_true, scores):
    candidates = np.unique(scores)

    best_threshold = float(candidates[0])
    best_f1 = -1.0

    for threshold in candidates:
        predicted = (scores >= threshold).astype(int)

        score = f1_score(
            y_true,
            predicted,
            zero_division=0,
        )

        if score > best_f1:
            best_f1 = score
            best_threshold = float(threshold)

    return best_threshold, best_f1


# =========================================
# EVALUASI
# =========================================

def evaluate_model(name, model_path, val_df, test_df):
    print("\n" + "=" * 55)
    print(f"MODEL: {name}")
    print("=" * 55)

    if not Path(model_path).is_dir():
        raise FileNotFoundError(
            f"Folder model tidak ditemukan: {model_path}"
        )

    model = CrossEncoder(
        model_path,
        num_labels=1,
        max_length=256,
    )

    print("\nMencari threshold dari validation...")
    val_scores = predict_scores(model, val_df)

    threshold, val_f1 = find_best_threshold(
        val_df["label"].to_numpy(),
        val_scores,
    )

    print(f"Threshold terbaik : {threshold:.4f}")
    print(f"Validation F1     : {val_f1:.4f}")

    print("\nMenguji pada dataset test...")
    test_scores = predict_scores(model, test_df)

    y_true = test_df["label"].to_numpy(dtype=int)
    y_pred = (test_scores >= threshold).astype(int)

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(
        y_true, y_pred, zero_division=0
    )
    recall = recall_score(
        y_true, y_pred, zero_division=0
    )
    f1 = f1_score(
        y_true, y_pred, zero_division=0
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true, y_pred, labels=[0, 1]
    ).ravel()

    print(f"\nHASIL TEST {name}")
    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")

    print("\nConfusion Matrix")
    print(f"True Negative  : {tn}")
    print(f"False Positive : {fp}")
    print(f"False Negative : {fn}")
    print(f"True Positive  : {tp}")

    details = test_df.copy()
    details["model"] = name
    details["raw_score"] = test_scores
    details["threshold"] = threshold
    details["prediction"] = y_pred
    details["correct"] = y_true == y_pred

    result = {
        "model": name,
        "threshold": round(threshold, 4),
        "validation_f1": round(val_f1, 4),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive": int(fp),
        "false_negative": int(fn),
    }

    del model

    return result, details


# =========================================
# MAIN
# =========================================

def main():
    print("=== PENGUJIAN ANTIKOPAS V1 VS V2 ===")

    val_df = load_data(VAL_FILE)
    test_df = load_data(TEST_FILE)

    print(f"Validation : {len(val_df)} pasangan")
    print(f"Test       : {len(test_df)} pasangan")

    results = []
    all_details = []

    for name, path in MODELS.items():
        result, details = evaluate_model(
            name,
            path,
            val_df,
            test_df,
        )

        results.append(result)
        all_details.append(details)

    summary = pd.DataFrame(results)
    summary.to_csv(OUTPUT_FILE, index=False)

    detail_df = pd.concat(
        all_details,
        ignore_index=True,
    )
    detail_df.to_csv(DETAIL_FILE, index=False)

    print("\n" + "=" * 55)
    print("PERBANDINGAN HASIL")
    print("=" * 55)

    print(summary.to_string(index=False))

    print(f"\nRingkasan: {OUTPUT_FILE}")
    print(f"Detail   : {DETAIL_FILE}")
    print("\nPENGUJIAN SELESAI!")


if __name__ == "__main__":
    main()
