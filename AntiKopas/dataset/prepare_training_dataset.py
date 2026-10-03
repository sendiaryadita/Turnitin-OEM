from pathlib import Path
import xml.etree.ElementTree as ET
import csv
import random


# =========================================================
# PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR / "korpus-plagiarisme-indonesia"

SOURCE_DIR = DATASET_DIR / "source-documents"
SUSPICIOUS_DIR = DATASET_DIR / "suspicious-documents"

OUTPUT_FILE = BASE_DIR / "training_dataset.csv"


# =========================================================
# SETTINGS
# =========================================================

MAX_CHARS = 900
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# =========================================================
# READ TEXT
# =========================================================

def read_text(path):
    return path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):
    return " ".join(
        text.replace("\n", " ").split()
    )


# =========================================================
# SPLIT TEXT
# =========================================================

def split_text(text, max_chars=MAX_CHARS):

    text = clean_text(text)

    words = text.split()

    chunks = []
    current = []

    current_length = 0

    for word in words:

        additional_length = len(word) + 1

        if (
            current
            and current_length + additional_length
            > max_chars
        ):

            chunks.append(
                " ".join(current)
            )

            current = []
            current_length = 0

        current.append(word)
        current_length += additional_length

    if current:
        chunks.append(
            " ".join(current)
        )

    return chunks


# =========================================================
# POSITIVE PAIRS
# =========================================================

positive_pairs = []

xml_files = sorted(
    SUSPICIOUS_DIR.glob("*.xml")
)

print(
    f"XML ditemukan: {len(xml_files)}"
)


for xml_file in xml_files:

    suspicious_file = (
        SUSPICIOUS_DIR /
        f"{xml_file.stem}.txt"
    )

    if not suspicious_file.exists():
        continue

    suspicious_text = read_text(
        suspicious_file
    )

    tree = ET.parse(xml_file)
    root = tree.getroot()

    for feature in root.findall("feature"):

        if feature.get("name") != "plagiarism":
            continue

        try:

            this_offset = int(
                feature.get("this_offset")
            )

            this_length = int(
                feature.get("this_length")
            )

            source_reference = feature.get(
                "source_reference"
            )

            source_offset = int(
                feature.get("source_offset")
            )

            source_length = int(
                feature.get("source_length")
            )

        except (TypeError, ValueError):

            continue

        source_file = (
            SOURCE_DIR /
            source_reference
        )

        if not source_file.exists():
            continue

        source_text = read_text(
            source_file
        )

        suspicious_segment = suspicious_text[
            this_offset:
            this_offset + this_length
        ]

        source_segment = source_text[
            source_offset:
            source_offset + source_length
        ]

        suspicious_chunks = split_text(
            suspicious_segment
        )

        source_chunks = split_text(
            source_segment
        )

        # Pasangkan chunk berdasarkan urutan
        pair_count = min(
            len(suspicious_chunks),
            len(source_chunks)
        )

        for i in range(pair_count):

            text_a = suspicious_chunks[i]
            text_b = source_chunks[i]

            if (
                len(text_a) < 20
                or len(text_b) < 20
            ):
                continue

            positive_pairs.append(
                (
                    text_a,
                    text_b,
                    1
                )
            )


# Hilangkan duplikat

positive_pairs = list(
    dict.fromkeys(
        positive_pairs
    )
)


print(
    f"Positive pairs: "
    f"{len(positive_pairs)}"
)


# =========================================================
# SOURCE DOCUMENTS
# =========================================================

source_files = sorted(
    SOURCE_DIR.glob("*.txt")
)

source_documents = {}

for source_file in source_files:

    source_documents[
        source_file.name
    ] = clean_text(
        read_text(source_file)
    )


# =========================================================
# NEGATIVE PAIRS
# =========================================================

negative_pairs = []

for text_a, _, _ in positive_pairs:

    random_source = random.choice(
        source_files
    )

    text_b = source_documents[
        random_source.name
    ]

    chunks = split_text(text_b)

    if not chunks:
        continue

    random_chunk = random.choice(
        chunks
    )

    if len(random_chunk) < 20:
        continue

    negative_pairs.append(
        (
            text_a,
            random_chunk,
            0
        )
    )


# Samakan jumlah

random.shuffle(negative_pairs)

negative_pairs = negative_pairs[
    :len(positive_pairs)
]


# =========================================================
# COMBINE
# =========================================================

dataset = (
    positive_pairs +
    negative_pairs
)

random.shuffle(dataset)


# =========================================================
# SAVE
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.writer(file)

    writer.writerow(
        [
            "text_a",
            "text_b",
            "label"
        ]
    )

    writer.writerows(dataset)


# =========================================================
# SUMMARY
# =========================================================

label_1 = sum(
    1
    for row in dataset
    if row[2] == 1
)

label_0 = sum(
    1
    for row in dataset
    if row[2] == 0
)


print("\n" + "=" * 60)
print("TRAINING DATASET SELESAI")
print("=" * 60)

print(
    f"Total pasangan : {len(dataset)}"
)

print(
    f"Label 1        : {label_1}"
)

print(
    f"Label 0        : {label_0}"
)

print(
    f"Output         : {OUTPUT_FILE}"
)