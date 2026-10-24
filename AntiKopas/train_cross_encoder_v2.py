
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

# ====================================
# KONFIGURASI
# ====================================

OLD_MODEL = Path("models/antikopas-cross-encoder")
NEW_MODEL = Path("models/antikopas-cross-encoder-v2")

TRAIN_FILE = Path("dataset/paws_train_v2.csv")
VAL_FILE = Path("dataset/paws_validation_v2.csv")

# ====================================
# LOAD DATASET
# ====================================

def load_data(path):
    if not path.is_file():
        raise FileNotFoundError(f"Dataset tidak ada: {path}")

    df = pd.read_csv(path)

    required = {"text_a", "text_b", "label"}
    if not required.issubset(df.columns):
        raise ValueError(f"Kolom dataset salah: {path}")

    df = df[["text_a", "text_b", "label"]].dropna()
    df["label"] = df["label"].astype(float)

    if not df["label"].isin([0.0, 1.0]).all():
        raise ValueError("Label harus 0 atau 1")

    return Dataset.from_pandas(df, preserve_index=False)


def main():
    print("=== TRAINING CROSS ENCODER V2 ===")

    if not OLD_MODEL.is_dir():
        raise FileNotFoundError(
            f"Model lama tidak ditemukan: {OLD_MODEL}"
        )

    train_data = load_data(TRAIN_FILE)
    val_data = load_data(VAL_FILE)

    print(f"Training data   : {len(train_data)}")
    print(f"Validation data : {len(val_data)}")

    # ====================================
    # LOAD MODEL HASIL TRAINING PERTAMA
    # ====================================

    print("\nMemuat model Cross Encoder lama...")

    model = CrossEncoder(
        str(OLD_MODEL),
        num_labels=1,
        max_length=256,
    )

    # ====================================
    # TRAINING CONFIG
    # ====================================

    args = CrossEncoderTrainingArguments(
        output_dir="models/v2-training-temp",

        num_train_epochs=1,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,

        learning_rate=1e-5,
        warmup_steps=25,
        weight_decay=0.01,

        eval_strategy="epoch",
        save_strategy="no",

        logging_steps=25,
        report_to="none",

        fp16=False,
        seed=42,
    )

    loss = BinaryCrossEntropyLoss(model=model)

    trainer = CrossEncoderTrainer(
        model=model,
        args=args,
        train_dataset=train_data,
        eval_dataset=val_data,
        loss=loss,
    )

    # ====================================
    # MULAI TRAINING
    # ====================================

    print("\nMemulai fine-tuning V2...")
    print(
        "Device:",
        "GPU" if torch.cuda.is_available() else "CPU"
    )

    trainer.train()

    print("\nEvaluasi validation...")
    metrics = trainer.evaluate()
    print(metrics)

    # ====================================
    # SIMPAN MODEL BARU
    # ====================================

    NEW_MODEL.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(NEW_MODEL))

    print("\n===================================")
    print("TRAINING V2 SELESAI!")
    print(f"Model tersimpan: {NEW_MODEL}")
    print("===================================")


if __name__ == "__main__":
    main()
