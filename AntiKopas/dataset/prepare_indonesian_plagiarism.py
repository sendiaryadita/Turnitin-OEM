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

OUTPUT_FILE = BASE_DIR / "similarity_dataset.csv"


# =========================================================
# SETTINGS
# =========================================================

RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# =========================================================
# BACA FILE
# =========================================================

def read_text(path):
    return path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


# =========================================================
# GENERATE POSITIVE PAIRS
# =========================================================

positive_pairs = []

xml_files = sorted(
    SUSPICIOUS_DIR.glob("*.xml")
)

print(f"XML ditemukan: {len(xml_files)}")


for xml_file in xml_files:

    suspicious_filename = xml_file.stem + ".txt"

    suspicious_path = (
        SUSPICIOUS_DIR / suspicious_filename
    )

    if not suspicious_path.exists():
        print(
            f"WARNING: {suspicious_filename} tidak ditemukan"
        )
        continue

    suspicious_text = read_text(
        suspicious_path
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

        source_path = (
            SOURCE_DIR / source_reference
        )

        if not source_path.exists():
            print(
                f"WARNING: source tidak ditemukan: "
                f"{source_reference}"
            )
            continue

        source_text = read_text(
            source_path
        )

        suspicious_segment = suspicious_text[
            this_offset:
            this_offset + this_length
        ]

        source_segment = source_text[
            source_offset:
            source_offset + source_length
        ]

        if not suspicious_segment.strip():
            continue

        if not source_segment.strip():
            continue

        positive_pairs.append(
            (
                suspicious_segment.strip(),
                source_segment.strip(),
                1
            )
        )


# =========================================================
# HILANGKAN DUPLIKAT
# =========================================================

positive_pairs = list(
    dict.fromkeys(positive_pairs)
)


print(
    f"Positive pairs: "
    f"{len(positive_pairs)}"
)


# =========================================================
# GENERATE NEGATIVE PAIRS
# =========================================================

source_files = sorted(
    SOURCE_DIR.glob("*.txt")
)

source_documents = {}

for source_file in source_files:

    source_documents[
        source_file.name
    ] = read_text(source_file)


negative_pairs = []


for suspicious_text, _, _ in positive_pairs:

    # Ambil source random
    random_source_name = random.choice(
        source_files
    ).name

    random_source_text = source_documents[
        random_source_name
    ]

    if not random_source_text.strip():
        continue

    negative_pairs.append(
        (
            suspicious_text,
            random_source_text[:2000].strip(),
            0
        )
    )


# =========================================================
# SAMAKAN JUMLAH POSITIF & NEGATIF
# =========================================================

random.shuffle(negative_pairs)

negative_pairs = negative_pairs[
    :len(positive_pairs)
]


print(
    f"Negative pairs: "
    f"{len(negative_pairs)}"
)


# =========================================================
# GABUNGKAN
# =========================================================

dataset = (
    positive_pairs +
    negative_pairs
)


random.shuffle(dataset)


# =========================================================
# SIMPAN CSV
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

positive_count = sum(
    1
    for row in dataset
    if row[2] == 1
)

negative_count = sum(
    1
    for row in dataset
    if row[2] == 0
)


print("\n" + "=" * 60)
print("DATASET SELESAI")
print("=" * 60)

print(
    f"Total pasangan : {len(dataset)}"
)

print(
    f"Label 1        : {positive_count}"
)

print(
    f"Label 0        : {negative_count}"
)

print(
    f"Output         : {OUTPUT_FILE}"
)