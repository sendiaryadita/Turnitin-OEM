
from pathlib import Path
import pandas as pd

DATA_DIR = Path("dataset/paws/data")
OUTPUT_DIR = Path("dataset")
OUTPUT_DIR.mkdir(exist_ok=True)

# Ambil sampel seimbang untuk percobaan training V2
splits = {
    "train": 1000,       # 1000 label 0 + 1000 label 1
    "validation": 200,  # 200 label 0 + 200 label 1
    "test": 200          # 200 label 0 + 200 label 1
}

for split, per_label in splits.items():
    path = DATA_DIR / f"{split}.csv"

    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")

    df = pd.read_csv(path)

    required = {"sentence1", "sentence2", "label"}
    if not required.issubset(df.columns):
        raise ValueError(
            f"Kolom tidak sesuai pada {path}: {list(df.columns)}"
        )

    df = df[["sentence1", "sentence2", "label"]].copy()

    df = df.dropna()
    df["sentence1"] = df["sentence1"].astype(str).str.strip()
    df["sentence2"] = df["sentence2"].astype(str).str.strip()
    df["label"] = pd.to_numeric(df["label"], errors="coerce")

    df = df[
        (df["sentence1"] != "") &
        (df["sentence2"] != "") &
        (df["label"].isin([0, 1]))
    ]

    df = df.drop_duplicates(
        subset=["sentence1", "sentence2"]
    )

    samples = []

    for label in [0, 1]:
        group = df[df["label"] == label]
        n = min(per_label, len(group))
        samples.append(group.sample(n=n, random_state=42))

    result = pd.concat(samples, ignore_index=True)
    result = result.sample(frac=1, random_state=42)

    result = result.rename(columns={
        "sentence1": "text_a",
        "sentence2": "text_b"
    })

    result["label"] = result["label"].astype(int)

    output = OUTPUT_DIR / f"paws_{split}_v2.csv"

    result[["text_a", "text_b", "label"]].to_csv(
        output, index=False, encoding="utf-8-sig"
    )

    print(f"{split}: {len(result)} pasangan -> {output}")
    print(result["label"].value_counts().to_dict())

print("\nDataset PAWS V2 berhasil disiapkan!")
