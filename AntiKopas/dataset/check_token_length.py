from pathlib import Path
import csv

from sentence_transformers import CrossEncoder


DATASET_FILE = (
    Path(__file__).parent /
    "training_dataset.csv"
)

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"


print("Loading tokenizer...")

model = CrossEncoder(MODEL_NAME)

tokenizer = model.tokenizer

print("Tokenizer berhasil dimuat!\n")


rows = []

with open(
    DATASET_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        rows.append(row)


token_lengths = []


for row in rows:

    text_a = row["text_a"]
    text_b = row["text_b"]

    tokens_a = tokenizer.encode(
        text_a,
        add_special_tokens=True
    )

    tokens_b = tokenizer.encode(
        text_b,
        add_special_tokens=True
    )

    token_lengths.append({
        "label": row["label"],
        "text_a": len(tokens_a),
        "text_b": len(tokens_b)
    })


print("=" * 60)
print("TOKEN LENGTH CHECK")
print("=" * 60)

print(f"Total pasangan : {len(token_lengths)}")

print(
    f"Max token A   : "
    f"{max(x['text_a'] for x in token_lengths)}"
)

print(
    f"Max token B   : "
    f"{max(x['text_b'] for x in token_lengths)}"
)

print(
    f"Rata-rata A   : "
    f"{sum(x['text_a'] for x in token_lengths) / len(token_lengths):.1f}"
)

print(
    f"Rata-rata B   : "
    f"{sum(x['text_b'] for x in token_lengths) / len(token_lengths):.1f}"
)


# Tampilkan 10 pasangan terpanjang

longest = sorted(
    token_lengths,
    key=lambda x: x["text_a"] + x["text_b"],
    reverse=True
)


print("\n" + "=" * 60)
print("10 PASANGAN TERPANJANG")
print("=" * 60)

for i, item in enumerate(longest[:10], start=1):

    print(
        f"{i}. "
        f"Label={item['label']} | "
        f"A={item['text_a']} tokens | "
        f"B={item['text_b']} tokens"
    )