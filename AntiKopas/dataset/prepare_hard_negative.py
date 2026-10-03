import os
import random
import pandas as pd
from sentence_transformers import SentenceTransformer, util


# =========================
# CONFIG
# =========================

INPUT_FILE = "dataset/training_dataset.csv"
OUTPUT_FILE = "dataset/hard_negative_dataset.csv"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


# =========================
# LOAD DATA
# =========================

print("=" * 60)
print("HARD NEGATIVE MINING")
print("=" * 60)

df = pd.read_csv(INPUT_FILE)

print(f"Total dataset awal : {len(df)}")
print(f"Label 1            : {(df['label'] == 1).sum()}")
print(f"Label 0            : {(df['label'] == 0).sum()}")


# =========================
# LOAD MODEL
# =========================

print("\nLoading MiniLM...")

model = SentenceTransformer(MODEL_NAME)


# =========================
# AMBIL DATA POSITIF
# =========================

positive_df = df[df["label"] == 1].copy()

print(f"Data positif : {len(positive_df)}")


# =========================
# SEMUA TEXT B
# =========================

negative_df = df[df["label"] == 0].copy()

all_text_b = negative_df["text_b"].astype(str).tolist()

embeddings_b = model.encode(
    all_text_b,
    convert_to_tensor=True,
    show_progress_bar=True
)


# =========================
# HARD NEGATIVE MINING
# =========================

hard_negatives = []

print("\nMencari hard negative...")


for row_index, row in positive_df.iterrows():

    text_a = str(row["text_a"])
    original_text_b = str(row["text_b"])

    # Embedding text A
    embedding_a = model.encode(
        text_a,
        convert_to_tensor=True
    )

    # Hitung similarity terhadap semua text B
    scores = util.cos_sim(
        embedding_a,
        embeddings_b
    )[0]

    # Ranking berdasarkan similarity tertinggi
    ranked_indices = scores.argsort(
        descending=True
    )

selected = None

for candidate_index in ranked_indices:

    candidate_index = int(candidate_index)

    candidate_text_b = all_text_b[candidate_index]

    # Jangan pilih text B asli dari pasangan positif
    if candidate_text_b == original_text_b:
        continue

    # Ambil kandidat yang cukup mirip secara topik
    similarity = float(
        scores[candidate_index]
    )

    if (
        similarity >= 0.50
        and len(text_a) >= 100
        and len(candidate_text_b) >= 100
    ):

        selected = {
            "text_a": text_a,
            "text_b": candidate_text_b,
            "label": 0,
            "minilm_similarity": similarity
        }

        break

if selected:
    hard_negatives.append(selected)

# =========================
# HASIL HARD NEGATIVE
# =========================

hard_negative_df = pd.DataFrame(
    hard_negatives
)

print("\nHard negative ditemukan :", len(hard_negative_df))


if len(hard_negative_df) == 0:

    print(
        "Tidak ditemukan hard negative."
    )

    raise SystemExit


# =========================
# DATASET FINAL
# =========================

# Dataset original
original = df[
    ["text_a", "text_b", "label"]
].copy()

# Hard negative
hard_negative_clean = hard_negative_df[
    ["text_a", "text_b", "label"]
].copy()


# Gabungkan
final_df = pd.concat(
    [
        original,
        hard_negative_clean
    ],
    ignore_index=True
)


# Acak
final_df = final_df.sample(
    frac=1,
    random_state=RANDOM_SEED
).reset_index(drop=True)


# =========================
# SAVE
# =========================

final_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================
# SUMMARY
# =========================

print("\n" + "=" * 60)
print("HASIL")
print("=" * 60)

print(f"Dataset awal       : {len(original)}")
print(f"Hard negative      : {len(hard_negative_clean)}")
print(f"Dataset final      : {len(final_df)}")

print(
    f"Label 1            : {(final_df['label'] == 1).sum()}"
)

print(
    f"Label 0            : {(final_df['label'] == 0).sum()}"
)

print(
    f"\nFile disimpan      : {OUTPUT_FILE}"
)