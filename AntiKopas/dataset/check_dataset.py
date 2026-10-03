import csv
from pathlib import Path


DATASET_FILE = Path(__file__).parent / "similarity_dataset.csv"


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


print("=" * 60)
print("DATASET CHECK")
print("=" * 60)

print(f"Total data : {len(rows)}")


label_1 = sum(
    1 for row in rows
    if row["label"] == "1"
)

label_0 = sum(
    1 for row in rows
    if row["label"] == "0"
)

print(f"Label 1    : {label_1}")
print(f"Label 0    : {label_0}")


# Panjang text
lengths_a = [
    len(row["text_a"])
    for row in rows
]

lengths_b = [
    len(row["text_b"])
    for row in rows
]


print("\nPanjang Text A")
print(f"Minimum : {min(lengths_a)}")
print(f"Maximum : {max(lengths_a)}")
print(
    f"Rata-rata : "
    f"{sum(lengths_a) / len(lengths_a):.0f}"
)


print("\nPanjang Text B")
print(f"Minimum : {min(lengths_b)}")
print(f"Maximum : {max(lengths_b)}")
print(
    f"Rata-rata : "
    f"{sum(lengths_b) / len(lengths_b):.0f}"
)


# Data terpanjang
longest = sorted(
    rows,
    key=lambda row: len(row["text_a"]) + len(row["text_b"]),
    reverse=True
)


print("\n" + "=" * 60)
print("5 PASANGAN TERPANJANG")
print("=" * 60)


for i, row in enumerate(longest[:5], start=1):

    print(f"\n{i}. Label: {row['label']}")

    print(
        f"Text A : "
        f"{len(row['text_a'])} karakter"
    )

    print(
        f"Text B : "
        f"{len(row['text_b'])} karakter"
    )