
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

# =====================================
# PATH
# =====================================

DATA_DIR = Path("dataset/academic_v2")

MODEL_V1 = Path("models/antikopas-cross-encoder")
MODEL_V2 = Path("models/antikopas-cross-encoder-academic-v2")

TRAIN_FILE = DATA_DIR / "academic_train_v2.csv"
VAL_FILE = DATA_DIR / "academic_validation_v2.csv"
TEST_FILE = DATA_DIR / "academic_test_v2.csv"


# =====================================
# VALIDASI DATA
# =====================================

def read_data(path):
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")

    df = pd.read_csv(path)

    required = {"text_a", "text_b", "label"}

    if not required.issubset(df.columns):
        raise ValueError(
            f"Kolom tidak sesuai: {list(df.columns)}"
        )

    df = df[["text_a", "text_b", "label"]].copy()

    if df.isnull().any().any():
        raise ValueError(f"Ada data kosong: {path}")

    df["text_a"] = df["text_a"].astype(str).str.strip()
    df["text_b"] = df["text_b"].astype(str).str.strip()
    df["label"] = pd.to_numeric(
        df["label"], errors="raise"
    )

    if (df["text_a"].eq("") | df["text_b"].eq("")).any():
        raise ValueError(f"Ada teks kosong: {path}")

    if not df["label"].isin([0, 1]).all():
        raise ValueError(f"Label bukan 0/1: {path}")

    if df.duplicated(["text_a", "text_b"]).any():
        raise ValueError(f"Ada pasangan duplikat: {path}")

    df["label"] = df["label"].astype(float)

    print(f"\n{path.name}: {len(df)} pasangan")
    print(df["label"].value_counts().to_dict())

    return df


def make_dataset(df):
    return Dataset.from_pandas(
        df.reset_index(drop=True),
        preserve_index=False,
    )


def pair_keys(df):
    # Pasangan A-B dianggap sama dengan B-A
    return {
        tuple(sorted((a.casefold(), b.casefold())))
        for a, b in zip(df["text_a"], df["text_b"])
    }


# =====================================
# MAIN
# =====================================

def main():
    print("=== ANTIKOPAS ACADEMIC V2 ===")

    train_df = read_data(TRAIN_FILE)
    val_df = read_data(VAL_FILE)
    test_df = read_data(TEST_FILE)

    train_keys = pair_keys(train_df)
    val_keys = pair_keys(val_df)
    test_keys = pair_keys(test_df)

    if (
        train_keys & val_keys
        or train_keys & test_keys
        or val_keys & test_keys
    ):
        raise ValueError(
            "Ditemukan pasangan yang sama "
            "di train/validation/test!"
        )

    print("\nTidak ada duplikasi pasangan antarsplit.")
    print(
        "Catatan: pemisahan berdasarkan topik/skenario "
        "tetap perlu diperiksa manual."
    )

    if not MODEL_V1.exists():
        raise FileNotFoundError(
            f"Model V1 tidak ditemukan: {MODEL_V1}"
        )

    if MODEL_V2.exists():
        raise FileExistsError(
            f"Folder model V2 sudah ada: {MODEL_V2}. "
            "Jangan timpa model tanpa disengaja."
        )

    train_data = make_dataset(train_df)
    val_data = make_dataset(val_df)

    print("\nMemuat Cross Encoder V1...")

    model = CrossEncoder(
        str(MODEL_V1),
        num_labels=1,
        max_length=256,
    )

    args = CrossEncoderTrainingArguments(
        output_dir="models/academic-v2-training-temp",
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

    trainer = CrossEncoderTrainer(
        model=model,
        args=args,
        train_dataset=train_data,
        eval_dataset=val_data,
        loss=BinaryCrossEntropyLoss(model),
    )

    device = "GPU" if torch.cuda.is_available() else "CPU"
    print(f"\nTraining menggunakan: {device}")

    trainer.train()

    print("\nEvaluasi validation:")
    print(trainer.evaluate())

    # Simpan V2, V1 tidak berubah
    MODEL_V2.mkdir(parents=True, exist_ok=False)
    model.save_pretrained(str(MODEL_V2))

    print("\n================================")
    print("TRAINING V2 BERHASIL!")
    print(f"Model: {MODEL_V2}")
    print("================================")


if __name__ == "__main__":
    main()
