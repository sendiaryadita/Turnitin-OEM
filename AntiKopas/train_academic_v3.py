
from pathlib import Path

import pandas as pd
import torch
from datasets import Dataset

from sentence_transformers.cross_encoder import (
    CrossEncoder,
    CrossEncoderTrainer,
    CrossEncoderTrainingArguments,
)
from sentence_transformers.cross_encoder.losses import (
    BinaryCrossEntropyLoss,
)


# ==========================================
# KONFIGURASI ANTIKOPAS ACADEMIC V3
# ==========================================

# Model hasil training V2 sebagai dasar
MODEL_LAMA = Path(
    "models/antikopas-cross-encoder-academic-v2"
)

# Model V3 yang akan disimpan
MODEL_BARU = Path(
    "models/antikopas-cross-encoder-academic-v3"
)

# Dataset training V3: 3112 pasangan
TRAIN_FILE = Path(
    "dataset/academic_v3/train.csv"
)

# Validation dan test tetap terpisah
VAL_FILE = Path(
    "dataset/academic_v2/academic_validation_v2.csv"
)

TEST_FILE = Path(
    "dataset/academic_v2/academic_test_v2.csv"
)

# Folder sementara untuk trainer
TRAINING_OUTPUT = (
    "models/academic-v3-training-temp"
)


# ==========================================
# MEMBACA DAN VALIDASI DATA
# ==========================================

def read_data(path):
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset tidak ditemukan: {path}"
        )

    df = pd.read_csv(path)

    required = {"text_a", "text_b", "label"}

    if not required.issubset(df.columns):
        raise ValueError(
            f"Kolom dataset salah: {path}\n"
            f"Kolom tersedia: {list(df.columns)}"
        )

    # Hanya pakai kolom untuk training
    df = df[
        ["text_a", "text_b", "label"]
    ].copy()

    if df.isnull().any().any():
        raise ValueError(
            f"Ada data kosong pada: {path}"
        )

    df["text_a"] = (
        df["text_a"].astype(str).str.strip()
    )

    df["text_b"] = (
        df["text_b"].astype(str).str.strip()
    )

    df["label"] = pd.to_numeric(
        df["label"],
        errors="raise",
    )

    if (
        df["text_a"].eq("").any()
        or df["text_b"].eq("").any()
    ):
        raise ValueError(
            f"Ada teks kosong pada: {path}"
        )

    if not df["label"].isin([0, 1]).all():
        raise ValueError(
            f"Label harus 0 atau 1: {path}"
        )

    df["label"] = df["label"].astype(float)

    print(f"\nDataset: {path.name}")
    print(f"Jumlah pasangan: {len(df)}")
    print("Distribusi label:")
    print(df["label"].value_counts())

    return df.reset_index(drop=True)


# ==========================================
# CEK DUPLIKASI ANTAR DATASET
# ==========================================

def get_pair_keys(df):
    keys = []

    for a, b in zip(df["text_a"], df["text_b"]):
        pair = tuple(sorted([
            a.strip().casefold(),
            b.strip().casefold(),
        ]))
        keys.append(pair)

    return keys


def validate_splits(train_df, val_df, test_df):
    train_keys = get_pair_keys(train_df)
    val_keys = get_pair_keys(val_df)
    test_keys = get_pair_keys(test_df)

    for name, keys in [
        ("train", train_keys),
        ("validation", val_keys),
        ("test", test_keys),
    ]:
        if len(keys) != len(set(keys)):
            raise ValueError(
                f"Ada pasangan duplikat dalam {name}"
            )

    train_set = set(train_keys)
    val_set = set(val_keys)
    test_set = set(test_keys)

    if train_set & val_set:
        raise ValueError(
            "Ada pasangan sama di train dan validation"
        )

    if train_set & test_set:
        raise ValueError(
            "Ada pasangan sama di train dan test"
        )

    if val_set & test_set:
        raise ValueError(
            "Ada pasangan sama di validation dan test"
        )

    print("\nValidasi duplikasi pasangan: AMAN")
    print(
        "Catatan: kemiripan skenario dan pola "
        "bahasa antarsplit belum diperiksa."
    )


# ==========================================
# KONVERSI KE HUGGING FACE DATASET
# ==========================================

def make_dataset(df):
    return Dataset.from_pandas(
        df,
        preserve_index=False,
    )


# ==========================================
# MAIN TRAINING
# ==========================================

def main():

    print("=" * 50)
    print("ANTIKOPAS - CROSS ENCODER ACADEMIC V3")
    print("=" * 50)

    # 1. Membaca data
    train_df = read_data(TRAIN_FILE)
    val_df = read_data(VAL_FILE)
    test_df = read_data(TEST_FILE)

    # 2. Validasi
    validate_splits(
        train_df,
        val_df,
        test_df,
    )

    # 3. Memastikan model lama tersedia
    if not MODEL_LAMA.is_dir():
        raise FileNotFoundError(
            f"Model V2 tidak ditemukan: {MODEL_LAMA}"
        )

    # Mencegah model lama/eksperimen tertimpa
    if MODEL_BARU.exists():
        raise FileExistsError(
            f"Folder model V3 sudah ada: {MODEL_BARU}\n"
            "Gunakan nama folder lain jika ingin "
            "membuat eksperimen baru."
        )

    # 4. Menyiapkan dataset
    train_dataset = make_dataset(train_df)
    val_dataset = make_dataset(val_df)

    # 5. Load model V2
    print("\nMemuat Cross Encoder Academic V2...")

    model = CrossEncoder(
        str(MODEL_LAMA),
        num_labels=1,
        max_length=256,
    )

    device = (
        "GPU" if torch.cuda.is_available()
        else "CPU"
    )

    print(f"Perangkat training: {device}")

    # 6. Konfigurasi training
    args = CrossEncoderTrainingArguments(
        output_dir=TRAINING_OUTPUT,

        num_train_epochs=1,

        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,

        learning_rate=1e-5,
        warmup_steps=20,
        weight_decay=0.01,

        eval_strategy="epoch",
        save_strategy="no",

        logging_steps=25,
        report_to="none",

        fp16=False,
        seed=42,
    )

    # 7. Loss untuk label 0/1
    loss = BinaryCrossEntropyLoss(
        model=model
    )

    # 8. Menyiapkan trainer
    trainer = CrossEncoderTrainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        loss=loss,
    )

    # 9. Training
    print("\n" + "=" * 50)
    print("MEMULAI TRAINING ACADEMIC V3")
    print("=" * 50)

    trainer.train()

    # 10. Evaluasi validation
    print("\nEvaluasi validation...")

    metrics = trainer.evaluate()

    print("\nHASIL EVALUASI:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    # 11. Simpan model V3
    print("\nMenyimpan model V3...")

    MODEL_BARU.mkdir(
        parents=True,
        exist_ok=False,
    )

    model.save_pretrained(
        str(MODEL_BARU)
    )

    print("\n" + "=" * 50)
    print("TRAINING CROSS ENCODER V3 SELESAI!")
    print(f"Model tersimpan: {MODEL_BARU}")
    print("=" * 50)

    print("\nLangkah selanjutnya:")
    print("1. Evaluasi V3 menggunakan data independen")
    print("2. Bandingkan V2 dan V3")
    print("3. Jangan ubah model Django dulu")


if __name__ == "__main__":
    main()
