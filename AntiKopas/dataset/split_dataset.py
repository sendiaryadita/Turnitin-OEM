import csv
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "training_dataset.csv"

TRAIN_FILE = BASE_DIR / "train.csv"
VAL_FILE = BASE_DIR / "validation.csv"
TEST_FILE = BASE_DIR / "test.csv"


RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# =========================================================
# LOAD DATA
# =========================================================

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as file:

    reader = csv.DictReader(file)

    rows = list(reader)


print("=" * 60)
print("DATASET SPLIT")
print("=" * 60)

print(f"Total data : {len(rows)}")


# =========================================================
# SHUFFLE
# =========================================================

random.shuffle(rows)


# =========================================================
# SPLIT
# =========================================================

total = len(rows)

train_end = int(total * 0.8)
val_end = int(total * 0.9)


train_rows = rows[:train_end]

validation_rows = rows[
    train_end:val_end
]

test_rows = rows[
    val_end:
]


# =========================================================
# SAVE FUNCTION
# =========================================================

def save_csv(path, data):

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "text_a",
                "text_b",
                "label"
            ]
        )

        writer.writeheader()
        writer.writerows(data)


save_csv(TRAIN_FILE, train_rows)
save_csv(VAL_FILE, validation_rows)
save_csv(TEST_FILE, test_rows)


# =========================================================
# SUMMARY
# =========================================================

def count_labels(data):

    label_1 = sum(
        1 for row in data
        if row["label"] == "1"
    )

    label_0 = sum(
        1 for row in data
        if row["label"] == "0"
    )

    return label_1, label_0


for name, data in [
    ("TRAIN", train_rows),
    ("VALIDATION", validation_rows),
    ("TEST", test_rows)
]:

    label_1, label_0 = count_labels(data)

    print(
        f"\n{name}"
    )

    print(
        f"Total  : {len(data)}"
    )

    print(
        f"Label 1: {label_1}"
    )

    print(
        f"Label 0: {label_0}"
    )


print("\nDataset berhasil di-split.")