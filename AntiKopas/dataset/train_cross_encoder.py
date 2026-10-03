import os
import pandas as pd

from sentence_transformers import CrossEncoder
from sentence_transformers.cross_encoder import CrossEncoderTrainer, CrossEncoderTrainingArguments
from sentence_transformers.cross_encoder.losses import BinaryCrossEntropyLoss


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"

TRAIN_FILE = "dataset/train.csv"
VALIDATION_FILE = "dataset/validation.csv"

OUTPUT_DIR = "models/antikopas-cross-encoder"

EPOCHS = 3
BATCH_SIZE = 8
LEARNING_RATE = 2e-5


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 60)
print("LOAD DATASET")
print("=" * 60)

train_df = pd.read_csv(TRAIN_FILE)
val_df = pd.read_csv(VALIDATION_FILE)

print(f"Train      : {len(train_df)}")
print(f"Validation : {len(val_df)}")

print("\nKolom:")
print(train_df.columns.tolist())


# ============================================================
# CONVERT DATASET
# ============================================================

from datasets import Dataset

train_dataset = Dataset.from_pandas(
    train_df[["text_a", "text_b", "label"]],
    preserve_index=False
)

val_dataset = Dataset.from_pandas(
    val_df[["text_a", "text_b", "label"]],
    preserve_index=False
)


# ============================================================
# LOAD MODEL
# ============================================================

print("\n" + "=" * 60)
print("LOAD CROSS ENCODER")
print("=" * 60)

model = CrossEncoder(
    MODEL_NAME,
    num_labels=1,
    max_length=512
)

print("Model berhasil dimuat.")


# ============================================================
# LOSS
# ============================================================

loss = BinaryCrossEntropyLoss(model)


# ============================================================
# TRAINING ARGUMENTS
# ============================================================

training_args = CrossEncoderTrainingArguments(
    output_dir=OUTPUT_DIR,

    num_train_epochs=EPOCHS,

    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,

    learning_rate=LEARNING_RATE,

    warmup_ratio=0.1,

    fp16=False,

    eval_strategy="epoch",
    save_strategy="epoch",

    save_total_limit=2,

    logging_steps=10,

    load_best_model_at_end=True,

    metric_for_best_model="eval_loss",

    greater_is_better=False,

    report_to="none"
)


# ============================================================
# TRAINER
# ============================================================

trainer = CrossEncoderTrainer(
    model=model,
    args=training_args,

    train_dataset=train_dataset,
    eval_dataset=val_dataset,

    loss=loss,
)


# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 60)
print("MULAI TRAINING")
print("=" * 60)

trainer.train()


# ============================================================
# SAVE MODEL
# ============================================================

print("\n" + "=" * 60)
print("SAVE MODEL")
print("=" * 60)

model.save_pretrained(OUTPUT_DIR)

print(f"Model berhasil disimpan di:")
print(OUTPUT_DIR)