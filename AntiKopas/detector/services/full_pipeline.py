
"""
ANTIKOPAS - ACADEMIC V2
STEP 3: ANTI-FALSE-POSITIVE VALIDATION

Fitur:
- Section-aware smart chunking
- Pembersihan artefak PDF
- MiniLM untuk pencarian kandidat
- Pemeriksaan konsistensi topik per pasangan
- Academic Cross Encoder V2
- Maksimal 20 sumber terpilih
- Bukti source_excerpt dan evidence_terms

Output kompatibel dengan:
- antikopas_service.py
- similarity_index.py
- views.py
"""

import math
import re
import unicodedata

from collections import Counter, defaultdict
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder,
    util,
)

from .document_analyzer import chunk_text
from .openalex import search_literature


# ==================================================
# 1. KONFIGURASI
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

CROSS_ENCODER_MODEL = (
    BASE_DIR
    / "models"
    / "antikopas-cross-encoder-academic-v2"
)

OPENALEX_PER_PAGE = 25
MAX_CANDIDATES = 50
MAX_MATCHED_SOURCES = 20

MAX_SOURCE_PAIRS_PER_CHUNK = 6
MAX_MATCHES_PER_CHUNK = 2

MAX_TOKENS_PER_PASSAGE = 170
MIN_TOKENS_PER_PASSAGE = 60
MIN_EVIDENCE_TOKENS = 40

CROSS_MAX_LENGTH = 512
BATCH_SIZE = 16

MIN_MINILM_SCORE = 0.65
CROSS_THRESHOLD = 2.1285

MIN_SOURCE_MATCHED_CHUNKS = 2
MIN_SOURCE_COVERAGE = 0.05

REQUIRE_DOI = True

# Validasi bukti bersifat konservatif.
MIN_SHARED_KEYWORDS = 3

# Tidak ada angka yang dipaksa harus positif.


# ==================================================
# 2. LOAD MODEL
# ==================================================

if not CROSS_ENCODER_MODEL.is_dir():
    raise FileNotFoundError(
        "Model Academic V2 tidak ditemukan: "
        + str(CROSS_ENCODER_MODEL)
    )

print("[AntiKopas] Loading MiniLM...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("[AntiKopas] Loading Academic V2...")

cross_encoder = CrossEncoder(
    str(CROSS_ENCODER_MODEL),
    num_labels=1,
    max_length=CROSS_MAX_LENGTH,
)

print("[AntiKopas] Model aktif: Academic V2")


# ==================================================
# 3. NORMALISASI
# ==================================================

STOPWORDS = {
    "pengaruh", "penggunaan", "pemanfaatan",
    "terhadap", "dalam", "pada", "untuk",
    "dengan", "yang", "dan", "atau",
    "dari", "sebagai", "melalui", "suatu",
    "studi", "kajian", "analisis", "peran",
    "hubungan", "dampak", "hasil",
    "penelitian", "implementasi", "penerapan",
    "strategi", "tinjauan", "literatur",
    "sistematis", "systematic", "literature",
    "review", "study", "effect", "impact",
    "influence", "of", "the", "and",
    "for", "with", "from", "on", "in",
    "to", "a", "an", "based", "approach",
    "era", "tahun", "model", "berbasis",
    "meningkatkan", "efektivitas",
    "dapat", "akan", "telah", "adalah",
    "menjadi", "memiliki", "memberikan",
    "menunjukkan", "menyatakan",
    "tersebut", "sehingga", "bahwa",
    "serta", "antara", "oleh",
    "lebih", "juga", "tidak",
    "sebuah", "beberapa", "sejumlah",
    "secara", "umum", "khusus",
    "melakukan", "dilakukan",
    "digunakan", "menggunakan",
    "membantu", "mendukung",
    "memberi", "membuat",
    "menurut", "melihat",
    "seperti", "karena", "mereka",
    "hasilnya", "berbagai",
    "teknologi", "kecerdasan",
    "buatan", "pendidikan",
    "pembelajaran", "belajar",
    "academic", "education",
    "learning", "students",
    "student", "research",
    "results", "technology",
}


def normalize_title(value):
    return " ".join(
        re.findall(
            r"\w+",
            str(value or "").casefold(),
        )
    )


def normalize_doi(value):
    text = str(value or "").strip().casefold()

    text = re.sub(
        r"^(?:https?://(?:dx\.)?doi\.org/"
        r"|doi\s*:\s*)",
        "",
        text,
    )

    return text.rstrip(".,;)]}")


def topic_terms(value):
    text = normalize_title(value)

    text = re.sub(
        r"\bartificial intelligence\b"
        r"|\bkecerdasan buatan\b"
        r"|\bchat\s*gpt\b"
        r"|\bchatbot\b"
        r"|\bgenerative ai\b",
        " ai ",
        text,
    )

    text = re.sub(
        r"\bpembelajaran\b"
        r"|\bpendidikan\b"
        r"|\blearning\b"
        r"|\beducation\b",
        " belajar ",
        text,
    )

    text = re.sub(
        r"\bmotivation\b",
        " motivasi ",
        text,
    )

    text = re.sub(
        r"\bcompetenc(?:e|y)\b",
        " kompetensi ",
        text,
    )

    return {
        word
        for word in text.split()
        if len(word) >= 2
        and word not in STOPWORDS
    }


# ==================================================
# 4. FILTER TOPIK SUMBER
# ==================================================

def relevant_to_topic(
    document_title,
    source_title,
    source_abstract,
):
    target = topic_terms(document_title)

    source_terms = topic_terms(
        source_title
    )

    abstract_terms = topic_terms(
        source_abstract
    )

    if not target or not source_terms:
        return False

    if "ai" in target and "ai" not in source_terms:
        return False

    if "mahasiswa" in target:
        school_terms = {
            "siswa", "murid", "guru",
            "smp", "sma", "smk", "sd",
        }

        if (
            source_terms & school_terms
            and "mahasiswa" not in source_terms
        ):
            return False

    other_topics = target - {"ai"}

    if "ai" in target:
        return (
            len(other_topics & source_terms) >= 1
            or len(other_topics & abstract_terms) >= 2
        )

    return (
        len(target & source_terms) >= 2
        or (
            len(target & source_terms) >= 1
            and len(target & abstract_terms) >= 2
        )
    )


def is_self_match(
    source,
    document_title,
    document_doi,
):
    source_doi = normalize_doi(
        source.get("doi")
    )

    if document_doi and source_doi == document_doi:
        return True

    uploaded_title = normalize_title(
        document_title
    )

    source_title = normalize_title(
        source.get("title")
    )

    if not uploaded_title or not source_title:
        return False

    similarity = SequenceMatcher(
        None,
        uploaded_title,
        source_title,
    ).ratio()

    return similarity >= 0.96


# ==================================================
# 5. PREPROCESSING
# ==================================================

def clean_text_artifacts(text):
    text = unicodedata.normalize(
        "NFKC",
        str(text or ""),
    )

    text = text.replace("\u00ad", "")

    text = re.sub(
        r"(?<=\w)-\s*\n\s*(?=\w)",
        "",
        text,
    )

    # Footer dokumen sintetis testing.
    text = re.sub(
        r"(?i)\bdokumen\s+sintetis\s*"
        r"[-–]\s*hanya\s+untuk\s+testing"
        r"(?:\s+halaman\s+\d+)?\b",
        " ",
        text,
    )

    # Metadata dokumen sintetis.
    text = re.sub(
        r"(?i)\bdokumen\s+sintetis\s+untuk\s+"
        r"pengujian\s+sistem\s+antikopas"
        r"\s+academic\s+v2\b",
        " ",
        text,
    )

    text = re.sub(
        r"(?i)\bcatatan\s*:\s*dokumen\s+ini\s+"
        r"dibuat\s+secara\s+sintetis\s+untuk\s+"
        r"mengevaluasi\s+seleksi\s+semantik\s+"
        r"antikopas\.\s*bukan\s+artikel\s+"
        r"ilmiah\s+yang\s+dipublikasikan\.",
        " ",
        text,
    )

    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
        " ",
        text,
    )

    return text.strip()


def remove_references(text):
    text = clean_text_artifacts(text)

    patterns = [
        r"(?im)^\s*(?:\d+[.)]\s*)?"
        r"(?:daftar\s+pustaka|daftar\s+rujukan|"
        r"references|bibliography)\s*$",

        r"(?i)(?:[.!?]\s+|\n\s*)"
        r"(?:daftar\s+pustaka|daftar\s+rujukan|"
        r"references|bibliography)\s+"
        r"(?=\[\d+\]|[A-Z][a-z]+\s*,)",
    ]

    positions = []

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            if match.start() >= len(text) * 0.35:
                positions.append(match.start())

    if positions:
        print(
            "[Preprocessing] Daftar pustaka dibuang"
        )
        return text[:min(positions)].strip()

    return text


def extract_document_doi(text):
    match = re.search(
        r"10\.\d{4,9}/[^\s\"'<>]+",
        str(text or "")[:3000],
        re.IGNORECASE,
    )

    if not match:
        return ""

    return normalize_doi(
        match.group(0)
    )


# ==================================================
# 6. DETEKSI HEADING
# ==================================================

NUMBERED_HEADING_RE = re.compile(
    r"(?<!\w)"
    r"\d{1,2}(?:\.\d{1,2})*\.\s+"
    r"[A-ZÀ-Þ][A-ZÀ-Þ0-9/():&,\-]*"
    r"(?:\s+[A-ZÀ-Þ][A-ZÀ-Þ0-9/():&,\-]*){0,12}"
    r"(?=\s+[A-ZÀ-Þ][a-zà-ÿ]"
    r"|\s+AI\s+[a-zà-ÿ]"
    r"|$)"
)

PLAIN_HEADING_RE = re.compile(
    r"(?<!\w)"
    r"(?:ABSTRAK|ABSTRACT|PENDAHULUAN|"
    r"TINJAUAN\s+PUSTAKA|"
    r"METODE\s+PENELITIAN|"
    r"HASIL\s+DAN\s+PEMBAHASAN|"
    r"PEMBAHASAN|"
    r"KESIMPULAN\s+DAN\s+SARAN|"
    r"KESIMPULAN)"
    r"(?=\s+[A-ZÀ-Þ][a-zà-ÿ]"
    r"|\s+AI\s+[a-zà-ÿ]"
    r"|$)"
)


def split_document_sections(text):
    text = " ".join(
        clean_text_artifacts(text).split()
    )

    if not text:
        return [], 0

    matches = list(
        NUMBERED_HEADING_RE.finditer(text)
    )

    matches.extend(
        PLAIN_HEADING_RE.finditer(text)
    )

    matches.sort(
        key=lambda match: (
            match.start(),
            -match.end(),
        )
    )

    valid_matches = []
    previous_end = -1

    for match in matches:
        if match.start() < previous_end:
            continue

        valid_matches.append(match)
        previous_end = match.end()

    sections = []
    cursor = 0

    for match in valid_matches:
        before = text[cursor:match.start()].strip()

        if before:
            sections.append(before)

        cursor = match.end()

    remaining = text[cursor:].strip()

    if remaining:
        sections.append(remaining)

    return sections, len(valid_matches)


# ==================================================
# 7. SMART CHUNKING
# ==================================================

@lru_cache(maxsize=8192)
def count_tokens(text):
    return len(
        cross_encoder.tokenizer.encode(
            str(text or ""),
            add_special_tokens=False,
            truncation=False,
        )
    )


def split_sentences(text):
    text = " ".join(
        str(text or "").split()
    )

    if not text:
        return []

    parts = re.split(
        r"(?<=[.!?])\s+(?=[A-ZÀ-Þ0-9])",
        text,
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def split_long_sentence(sentence, max_tokens):
    words = sentence.split()

    result = []
    current = []

    for word in words:
        candidate = " ".join(
            current + [word]
        )

        if count_tokens(candidate) <= max_tokens:
            current.append(word)
            continue

        if current:
            result.append(
                " ".join(current)
            )
            current = []

        if count_tokens(word) > max_tokens:
            raise ValueError(
                "Kata tunggal terlalu panjang: "
                + word[:50]
            )

        current = [word]

    if current:
        result.append(
            " ".join(current)
        )

    return result


def rebalance_passages(
    passages,
    min_tokens,
    max_tokens,
):
    passages = list(passages)

    if len(passages) < 2:
        return passages

    index = len(passages) - 1

    while index > 0:
        current = passages[index]
        previous = passages[index - 1]

        if count_tokens(current) >= min_tokens:
            index -= 1
            continue

        combined = previous + " " + current

        if count_tokens(combined) <= max_tokens:
            passages[index - 1] = combined
            passages.pop(index)
            index -= 1
            continue

        candidates = []

        sentence_parts = split_sentences(previous)

        for split_at in range(
            1,
            len(sentence_parts),
        ):
            left = " ".join(
                sentence_parts[:split_at]
            )

            right = " ".join(
                sentence_parts[split_at:]
                + [current]
            )

            left_tokens = count_tokens(left)
            right_tokens = count_tokens(right)

            if (
                min_tokens <= left_tokens <= max_tokens
                and min_tokens <= right_tokens <= max_tokens
            ):
                candidates.append((
                    abs(left_tokens - right_tokens),
                    left,
                    right,
                ))

        if not candidates:
            words = combined.split()

            for split_at in range(
                1,
                len(words),
            ):
                left = " ".join(
                    words[:split_at]
                )

                right = " ".join(
                    words[split_at:]
                )

                left_tokens = count_tokens(left)
                right_tokens = count_tokens(right)

                if (
                    min_tokens <= left_tokens <= max_tokens
                    and min_tokens <= right_tokens <= max_tokens
                ):
                    candidates.append((
                        abs(left_tokens - right_tokens),
                        left,
                        right,
                    ))

        if candidates:
            _, left, right = min(
                candidates,
                key=lambda item: item[0],
            )

            passages[index - 1] = left
            passages[index] = right

        index -= 1

    return passages


def split_short_passages(
    text,
    max_tokens=MAX_TOKENS_PER_PASSAGE,
    min_tokens=MIN_TOKENS_PER_PASSAGE,
):
    text = " ".join(
        clean_text_artifacts(text).split()
    )

    if not text:
        return []

    units = []

    for sentence in split_sentences(text):
        if count_tokens(sentence) <= max_tokens:
            units.append(sentence)
        else:
            units.extend(
                split_long_sentence(
                    sentence,
                    max_tokens,
                )
            )

    passages = []
    current = []

    for unit in units:
        candidate = " ".join(
            current + [unit]
        )

        if count_tokens(candidate) <= max_tokens:
            current.append(unit)
            continue

        if current:
            passages.append(
                " ".join(current)
            )

        current = [unit]

    if current:
        passages.append(
            " ".join(current)
        )

    passages = rebalance_passages(
        passages,
        min_tokens,
        max_tokens,
    )

    for passage in passages:
        if count_tokens(passage) > max_tokens:
            raise RuntimeError(
                "Chunk melebihi batas token."
            )

    return passages


def build_document_chunks(text):
    sections, heading_count = (
        split_document_sections(text)
    )

    chunks = []

    for section in sections:
        chunks.extend(
            split_short_passages(section)
        )

    return (
        chunks,
        heading_count,
        len(sections),
    )


# ==================================================
# 8. VALIDASI KONSEP PER PASANGAN
# ==================================================

# Ini bukan classifier tambahan yang terlatih.
# Ini guardrail berbasis istilah/konsep untuk
# membantu menolak pasangan tidak konsisten.

CONCEPT_PATTERNS = {
    "ai": [
        r"\bai\b",
        r"\bartificial intelligence\b",
        r"\bkecerdasan buatan\b",
        r"\bchatgpt\b",
        r"\bchat\s+gpt\b",
        r"\bchatbot\b",
        r"\bgenerative ai\b",
    ],
    "chatgpt": [
        r"\bchatgpt\b",
        r"\bchat\s+gpt\b",
    ],
    "academic": [
        r"\bmahasiswa\b",
        r"\bperguruan tinggi\b",
        r"\bperkuliahan\b",
        r"\bkuliah\b",
        r"\bkampus\b",
        r"\buniversitas\b",
        r"\bcollege students?\b",
        r"\buniversity students?\b",
    ],
    "learning": [
        r"\bbelajar\b",
        r"\bpembelajaran\b",
        r"\bpendidikan\b",
        r"\bpengajaran\b",
        r"\blearning\b",
        r"\beducation\b",
        r"\bteaching\b",
    ],
    "motivation": [
        r"\bmotivasi\b",
        r"\bmotivation\b",
        r"\bintrinsik\b",
        r"\bintrinsic\b",
        r"\bsemangat belajar\b",
        r"\bdorongan belajar\b",
    ],
    "critical": [
        r"\bberpikir kritis\b",
        r"\bpemikiran kritis\b",
        r"\bberfikir kritis\b",
        r"\bcritical thinking\b",
        r"\bkemampuan analitis\b",
        r"\bketerampilan analitis\b",
    ],
    "dependence": [
        r"\bketergantungan\b",
        r"\bbergantung\b",
        r"\bover.reliance\b",
        r"\bdependenc\w*\b",
    ],
    "ethics": [
        r"\betika\b",
        r"\betis\b",
        r"\bprivasi\b",
        r"\bintegritas akademik\b",
        r"\bplagiarisme\b",
        r"\bplagiarism\b",
        r"\bacademic integrity\b",
    ],
    "literacy": [
        r"\bliterasi\b",
        r"\bliteracy\b",
        r"\bdigital literacy\b",
    ],
    "feedback": [
        r"\bum[p]?an balik\b",
        r"\bfeedback\b",
        r"\brespon langsung\b",
    ],
    "autonomy": [
        r"\bkemandirian\b",
        r"\bmandiri\b",
        r"\bautonomy\b",
        r"\bself.directed\b",
        r"\bself.regulat\w*\b",
    ],
    "competency": [
        r"\bkompetensi\b",
        r"\bkompeten\b",
        r"\bcompetenc\w*\b",
        r"\bketerampilan\b",
        r"\bkemampuan\b",
    ],
    "writing": [
        r"\bmenulis\b",
        r"\bpenulisan\b",
        r"\btulisan\b",
        r"\bwriting\b",
        r"\bwacana\b",
    ],
    "programming": [
        r"\bpemrograman\b",
        r"\bprogramming\b",
        r"\bcoding\b",
        r"\bmatlab\b",
        r"\bsource code\b",
    ],
    "agriculture": [
        r"\birigasi\b",
        r"\bpadi\b",
        r"\bgabah\b",
        r"\bpertanian\b",
        r"\btanaman\b",
        r"\bpanen\b",
        r"\bberas\b",
        r"\bperkebunan\b",
        r"\bpupuk\b",
        r"\bhasil tani\b",
        r"\bcrop\b",
        r"\birrigation\b",
    ],
    "marine": [
        r"\blamun\b",
        r"\bpesisir\b",
        r"\bsedimen\b",
        r"\blaut\b",
        r"\bperairan\b",
        r"\bbentik\b",
        r"\bkekeruhan\b",
        r"\bmarine\b",
        r"\bseagrass\b",
    ],
}

COMPILED_CONCEPTS = {
    concept: [
        re.compile(pattern, re.IGNORECASE)
        for pattern in patterns
    ]
    for concept, patterns in CONCEPT_PATTERNS.items()
}

# Konsep umum tidak cukup sendirian
# untuk membuktikan kecocokan.
GENERAL_CONCEPTS = {
    "ai",
    "academic",
    "learning",
}

# Domain yang sangat spesifik.
DOMAIN_CONCEPTS = {
    "agriculture",
    "marine",
}


@lru_cache(maxsize=8192)
def evidence_concepts(text):
    text = unicodedata.normalize(
        "NFKC",
        str(text or ""),
    ).casefold()

    found = set()

    for concept, patterns in (
        COMPILED_CONCEPTS.items()
    ):
        if any(
            pattern.search(text)
            for pattern in patterns
        ):
            found.add(concept)

    return frozenset(found)


@lru_cache(maxsize=8192)
def evidence_keywords(text):
    text = unicodedata.normalize(
        "NFKC",
        str(text or ""),
    ).casefold()

    text = re.sub(
        r"\bartificial intelligence\b"
        r"|\bkecerdasan buatan\b",
        " ai ",
        text,
    )

    text = re.sub(
        r"\bchat\s+gpt\b",
        " chatgpt ",
        text,
    )

    words = re.findall(
        r"[a-zà-ÿ]{4,}",
        text,
    )

    return frozenset({
        word
        for word in words
        if word not in STOPWORDS
    })


def validate_pair_evidence(
    uploaded_chunk,
    source_excerpt,
):
    """
    Menghasilkan keputusan dan alasan.

    Keputusan ini hanya pemeriksaan awal
    konsistensi isi, bukan putusan plagiarisme.
    """

    chunk_concepts = set(
        evidence_concepts(uploaded_chunk)
    )

    source_concepts = set(
        evidence_concepts(source_excerpt)
    )

    chunk_keywords = set(
        evidence_keywords(uploaded_chunk)
    )

    source_keywords = set(
        evidence_keywords(source_excerpt)
    )

    shared_concepts = (
        chunk_concepts & source_concepts
    )

    shared_keywords = (
        chunk_keywords & source_keywords
    )

    # Guardrail untuk perbedaan domain yang jelas.
    for domain in DOMAIN_CONCEPTS:
        if (
            domain in chunk_concepts
            and domain not in source_concepts
        ):
            return {
                "accepted": False,
                "reason": "domain_conflict",
                "shared_concepts": sorted(
                    shared_concepts
                ),
                "shared_keywords": sorted(
                    shared_keywords
                ),
            }

        if (
            domain in source_concepts
            and domain not in chunk_concepts
        ):
            return {
                "accepted": False,
                "reason": "domain_conflict",
                "shared_concepts": sorted(
                    shared_concepts
                ),
                "shared_keywords": sorted(
                    shared_keywords
                ),
            }

    informative = (
        shared_concepts - GENERAL_CONCEPTS
    )

    # Dua konsep beririsan dan setidaknya
    # satu di antaranya spesifik.
    concept_supported = (
        len(shared_concepts) >= 2
        and len(informative) >= 1
    )

    # Atau istilah bermakna yang beririsan
    # cukup banyak, dengan minimal
    # satu kesamaan konsep.
    keyword_supported = (
        len(shared_concepts) >= 1
        and len(shared_keywords)
        >= MIN_SHARED_KEYWORDS
    )

    accepted = (
        concept_supported
        or keyword_supported
    )

    return {
        "accepted": accepted,
        "reason": (
            "supported"
            if accepted
            else "insufficient_evidence"
        ),
        "shared_concepts": sorted(
            shared_concepts
        ),
        "shared_keywords": sorted(
            shared_keywords
        ),
    }


# ==================================================
# 9. QUERY OPENALEX
# ==================================================

def create_search_queries(
    document_title,
    chunks,
):
    queries = []

    if document_title:
        queries.append(
            " ".join(
                str(document_title).split()[:16]
            )
        )

    if chunks:
        positions = [
            0,
            len(chunks) // 3,
            (2 * len(chunks)) // 3,
        ]

        for index in dict.fromkeys(positions):
            query = " ".join(
                chunks[index].split()[:12]
            )

            if query:
                queries.append(query)

    unique = []
    seen = set()

    for query in queries:
        key = query.strip().casefold()

        if key and key not in seen:
            seen.add(key)
            unique.append(query)

    return unique


# ==================================================
# 10. AMBIL SUMBER
# ==================================================

def collect_sources(
    document_title,
    chunks,
    document_doi,
):
    sources = []

    seen_titles = set()
    seen_dois = set()
    seen_ids = set()

    stats = Counter()

    queries = create_search_queries(
        document_title,
        chunks,
    )

    for query in queries:
        results = search_literature(
            query,
            per_page=OPENALEX_PER_PAGE,
        ) or []

        stats["fetched"] += len(results)

        for item in results:
            if not isinstance(item, dict):
                continue

            title = str(
                item.get("title") or ""
            ).strip()

            abstract = str(
                item.get("text") or ""
            ).strip()

            doi = normalize_doi(
                item.get("doi")
            )

            source_key = str(
                item.get("source_id")
                or item.get("openalex_id")
                or ""
            ).strip().casefold()

            title_key = normalize_title(title)

            if (
                not title
                or len(abstract.split()) < 20
            ):
                stats["no_abstract"] += 1
                continue

            if REQUIRE_DOI and not doi:
                stats["no_doi"] += 1
                continue

            work_type = str(
                item.get("type") or ""
            ).strip().casefold()

            if (
                work_type
                and work_type != "article"
            ):
                stats["not_article"] += 1
                continue

            if not relevant_to_topic(
                document_title,
                title,
                abstract,
            ):
                stats["off_topic"] += 1
                continue

            if is_self_match(
                item,
                document_title,
                document_doi,
            ):
                stats["self_match"] += 1
                continue

            if (
                title_key in seen_titles
                or (doi and doi in seen_dois)
                or (
                    source_key
                    and source_key in seen_ids
                )
            ):
                stats["duplicate"] += 1
                continue

            seen_titles.add(title_key)

            if doi:
                seen_dois.add(doi)

            if source_key:
                seen_ids.add(source_key)

            sources.append(item)

    print(
        "[OpenAlex] Kandidat ditemukan:",
        stats["fetched"],
    )

    print(
        "[OpenAlex] Alasan penolakan:",
        {
            key: stats[key]
            for key in (
                "no_abstract",
                "no_doi",
                "not_article",
                "off_topic",
                "self_match",
                "duplicate",
            )
        },
    )

    print(
        "[OpenAlex] Lolos filter topik:",
        len(sources),
    )

    if stats["fetched"] == 0:
        raise RuntimeError(
            "OpenAlex tidak mengembalikan hasil. "
            "Cek koneksi atau API."
        )

    return sources


# ==================================================
# 11. HASIL KOSONG
# ==================================================

def empty_results(chunks):
    return [
        {
            "chunk_index": index,
            "chunk_text": chunk,
            "matches": [],
        }
        for index, chunk in enumerate(
            chunks,
            start=1,
        )
    ]


# ==================================================
# 12. PIPELINE UTAMA
# ==================================================

def analyze_with_openalex(
    document_text,
    document_title=None,
):
    print()
    print("====================================")
    print("ANTIKOPAS - ACADEMIC V2 STEP 3")
    print("====================================")

    if not str(document_text or "").strip():
        raise ValueError("Dokumen kosong.")

    if not str(document_title or "").strip():
        raise ValueError(
            "Judul dokumen wajib diisi."
        )

    # A. PREPROCESSING

    clean_text = remove_references(
        document_text
    )

    original_chunks = [
        str(chunk).strip()
        for chunk in chunk_text(clean_text)
        if str(chunk).strip()
    ]

    if not original_chunks:
        raise ValueError(
            "Tidak ada teks yang dapat dianalisis."
        )

    # B. SECTION-AWARE SMART CHUNKING

    (
        chunks,
        heading_count,
        section_count,
    ) = build_document_chunks(clean_text)

    if not chunks:
        raise ValueError(
            "Tidak ada smart chunk yang valid."
        )

    total_chunks = len(chunks)

    chunk_token_counts = [
        count_tokens(chunk)
        for chunk in chunks
    ]

    short_chunk_indices = [
        index
        for index, token_count in enumerate(
            chunk_token_counts,
            start=1,
        )
        if token_count < MIN_EVIDENCE_TOKENS
    ]

    print(
        "[Document] Chunk awal:",
        len(original_chunks),
    )

    print(
        "[Preprocessing] Heading terdeteksi:",
        heading_count,
    )

    print(
        "[Document] Total section:",
        section_count,
    )

    print(
        "[Document] Smart chunks:",
        total_chunks,
    )

    print(
        "[Document] Token maksimum:",
        max(chunk_token_counts),
    )

    print(
        "[Document] Chunk terlalu pendek:",
        len(short_chunk_indices),
    )

    print(
        "[Document] Indeks chunk pendek:",
        short_chunk_indices,
    )

    # C. OPENALEX

    literature = collect_sources(
        document_title,
        original_chunks,
        extract_document_doi(clean_text),
    )

    if not literature:
        return empty_results(chunks)

    # D. POTONG ABSTRAK SUMBER

    source_passages = []
    passage_source_indices = []

    for source_index, source in enumerate(
        literature
    ):
        passages = split_short_passages(
            source.get("text", "")
        )

        for passage in passages:
            source_passages.append(passage)
            passage_source_indices.append(
                source_index
            )

    if not source_passages:
        return empty_results(chunks)

    print(
        "[Source] Potongan abstrak:",
        len(source_passages),
    )

    # E. EMBEDDING MINI LM

    chunk_embeddings = embedding_model.encode(
        chunks,
        batch_size=BATCH_SIZE,
        convert_to_tensor=True,
        show_progress_bar=False,
    )

    source_embeddings = embedding_model.encode(
        source_passages,
        batch_size=BATCH_SIZE,
        convert_to_tensor=True,
        show_progress_bar=False,
    )

    similarity_matrix = util.cos_sim(
        chunk_embeddings,
        source_embeddings,
    )

    # F. RANKING SUMBER

    best_source_scores = [
        float("-inf")
        for _ in literature
    ]

    for passage_index, source_index in enumerate(
        passage_source_indices
    ):
        score = float(
            similarity_matrix[
                :,
                passage_index,
            ].max()
        )

        best_source_scores[source_index] = max(
            best_source_scores[source_index],
            score,
        )

    ordered_indices = sorted(
        range(len(literature)),
        key=lambda index: best_source_scores[index],
        reverse=True,
    )

    selected_sources = set(
        ordered_indices[:MAX_CANDIDATES]
    )

    print(
        "[MiniLM] Kandidat diperiksa:",
        len(selected_sources),
    )

    # G. PILIH PASANGAN + VALIDASI KONSEP

    pairs = []
    locations = []

    max_pair_tokens = 0
    skipped_short = 0

    rejected_domain = 0
    rejected_evidence = 0
    validated_pairs = 0

    rejection_examples = []

    for chunk_index, chunk in enumerate(chunks):
        if (
            chunk_token_counts[chunk_index]
            < MIN_EVIDENCE_TOKENS
        ):
            skipped_short += 1
            continue

        strongest_sources = {}

        for passage_index, source_index in enumerate(
            passage_source_indices
        ):
            if source_index not in selected_sources:
                continue

            mini_score = float(
                similarity_matrix[
                    chunk_index,
                    passage_index,
                ]
            )

            if not math.isfinite(mini_score):
                continue

            if mini_score < MIN_MINILM_SCORE:
                continue

            existing = strongest_sources.get(
                source_index
            )

            if (
                existing is None
                or mini_score > existing[0]
            ):
                strongest_sources[source_index] = (
                    mini_score,
                    passage_index,
                )

        top_sources = sorted(
            strongest_sources.items(),
            key=lambda item: item[1][0],
            reverse=True,
        )[:MAX_SOURCE_PAIRS_PER_CHUNK]

        for source_index, data in top_sources:
            mini_score, passage_index = data

            source_text = source_passages[
                passage_index
            ]

            validation = validate_pair_evidence(
                chunk,
                source_text,
            )

            if not validation["accepted"]:
                if (
                    validation["reason"]
                    == "domain_conflict"
                ):
                    rejected_domain += 1
                else:
                    rejected_evidence += 1

                if len(rejection_examples) < 5:
                    rejection_examples.append({
                        "chunk_index": chunk_index + 1,
                        "source_title": literature[
                            source_index
                        ].get("title"),
                        "reason": validation["reason"],
                    })

                continue

            pair_encoding = cross_encoder.tokenizer(
                chunk,
                source_text,
                add_special_tokens=True,
                truncation=False,
            )

            token_count = len(
                pair_encoding["input_ids"]
            )

            max_pair_tokens = max(
                max_pair_tokens,
                token_count,
            )

            if token_count > CROSS_MAX_LENGTH:
                raise RuntimeError(
                    "Input Cross Encoder terlalu panjang: "
                    f"{token_count} token."
                )

            validated_pairs += 1

            pairs.append((
                chunk,
                source_text,
            ))

            locations.append((
                chunk_index,
                source_index,
                mini_score,
                source_text,
                validation,
            ))

    print(
        "[Validation] Pasangan valid:",
        validated_pairs,
    )

    print(
        "[Validation] Ditolak beda domain:",
        rejected_domain,
    )

    print(
        "[Validation] Ditolak bukti lemah:",
        rejected_evidence,
    )

    print(
        "[Validation] Contoh penolakan:",
        rejection_examples,
    )

    print(
        "[Diagnostic] Chunk pendek dilewati:",
        skipped_short,
    )

    print(
        "[Diagnostic] Token pasangan terpanjang:",
        max_pair_tokens,
    )

    print(
        "[Diagnostic] Pasangan >512 token: 0"
    )

    if not pairs:
        print(
            "[Diagnostic] Tidak ada pasangan "
            "yang lolos validasi konsep."
        )
        return empty_results(chunks)

    # H. CROSS ENCODER V2

    raw_scores = cross_encoder.predict(
        pairs,
        batch_size=BATCH_SIZE,
        show_progress_bar=False,
        activation_fn=torch.nn.Identity(),
    )

    scores = np.asarray(
        raw_scores,
        dtype=float,
    ).reshape(-1)

    if len(scores) != len(locations):
        raise RuntimeError(
            "Output Academic V2 tidak sesuai "
            "jumlah pasangan."
        )

    finite_scores = [
        float(score)
        for score in scores
        if math.isfinite(float(score))
    ]

    if finite_scores:
        print(
            "[Diagnostic] Skor Academic V2:",
            {
                "min": round(
                    min(finite_scores),
                    3,
                ),
                "median": round(
                    float(np.median(finite_scores)),
                    3,
                ),
                "p90": round(
                    float(
                        np.percentile(
                            finite_scores,
                            90,
                        )
                    ),
                    3,
                ),
                "max": round(
                    max(finite_scores),
                    3,
                ),
                "threshold": CROSS_THRESHOLD,
            },
        )

    # I. KUMPULKAN MATCHES

    matches_by_chunk = [
        []
        for _ in chunks
    ]

    passed_v2 = 0

    for location, raw_score in zip(
        locations,
        scores,
    ):
        (
            chunk_index,
            source_index,
            mini_score,
            source_text,
            validation,
        ) = location

        cross_score = float(raw_score)

        if not math.isfinite(cross_score):
            continue

        if cross_score < CROSS_THRESHOLD:
            continue

        passed_v2 += 1

        source = literature[source_index]

        matches_by_chunk[
            chunk_index
        ].append({
            "_source_index": source_index,
            "openalex_id": (
                source.get("source_id")
                or source.get("openalex_id")
            ),
            "title": source.get("title"),
            "year": source.get("year"),
            "doi": source.get("doi"),
            "url": source.get("url"),
            "minilm_score": mini_score,
            "cross_score": cross_score,
            "overlap_score": 0.0,
            "matched": True,

            # Bukti pasangan persis yang
            # diterima Cross Encoder.
            "source_excerpt": source_text,

            # Bukti pendukung untuk audit.
            "evidence_concepts": (
                validation["shared_concepts"]
            ),
            "evidence_terms": (
                validation["shared_keywords"][:15]
            ),
            "evidence_validation": (
                validation["reason"]
            ),
        })

    # J. MAKSIMAL 2 SOURCE PER CHUNK

    for matches in matches_by_chunk:
        matches.sort(
            key=lambda match: (
                match["cross_score"],
                match["minilm_score"],
            ),
            reverse=True,
        )

        del matches[MAX_MATCHES_PER_CHUNK:]

    # K. KECOCOKAN PER SUMBER

    source_stats = defaultdict(
        lambda: {
            "chunk_indices": set(),
            "cross_scores": [],
        }
    )

    for chunk_index, matches in enumerate(
        matches_by_chunk
    ):
        for match in matches:
            source_index = match[
                "_source_index"
            ]

            source_stats[
                source_index
            ]["chunk_indices"].add(
                chunk_index
            )

            source_stats[
                source_index
            ]["cross_scores"].append(
                match["cross_score"]
            )

    # L. SELEKSI SUMBER FINAL

    minimum_matches = min(
        total_chunks,
        max(
            MIN_SOURCE_MATCHED_CHUNKS,
            math.ceil(
                total_chunks * MIN_SOURCE_COVERAGE
            ),
        ),
    )

    qualified_sources = []

    for source_index, data in source_stats.items():
        matched_count = len(
            data["chunk_indices"]
        )

        if matched_count < minimum_matches:
            continue

        average_cross = float(
            np.mean(data["cross_scores"])
        )

        qualified_sources.append((
            source_index,
            matched_count,
            average_cross,
        ))

    qualified_sources.sort(
        key=lambda item: (
            item[1],
            item[2],
        ),
        reverse=True,
    )

    accepted_sources = {
        item[0]
        for item in qualified_sources[
            :MAX_MATCHED_SOURCES
        ]
    }

    # M. SUSUN OUTPUT FINAL

    document_results = []

    for chunk_index, chunk in enumerate(
        chunks,
        start=1,
    ):
        final_matches = []

        for match in matches_by_chunk[
            chunk_index - 1
        ]:
            if (
                match["_source_index"]
                not in accepted_sources
            ):
                continue

            clean_match = dict(match)

            clean_match.pop(
                "_source_index",
                None,
            )

            final_matches.append(clean_match)

        document_results.append({
            "chunk_index": chunk_index,
            "chunk_text": chunk,
            "matches": final_matches,
        })

    matched_chunks = sum(
        bool(chunk["matches"])
        for chunk in document_results
    )

    # N. LOG DIAGNOSTIK AKHIR

    print()
    print("====================================")
    print("ANTIKOPAS - HASIL STEP 3")
    print("====================================")

    print("Model: Academic V2")

    print(
        "Total chunks:",
        total_chunks,
    )

    print(
        "Chunk pendek dilewati:",
        skipped_short,
    )

    print(
        "Pasangan validasi bukti:",
        validated_pairs,
    )

    print(
        "Ditolak beda domain:",
        rejected_domain,
    )

    print(
        "Ditolak bukti lemah:",
        rejected_evidence,
    )

    print(
        "Pasangan lolos Academic V2:",
        passed_v2,
    )

    print(
        "Minimal chunk per sumber:",
        minimum_matches,
    )

    print(
        "Jurnal lolos seleksi:",
        len(accepted_sources),
    )

    print(
        "Chunk cocok:",
        matched_chunks,
    )

    print(
        "Maksimum sumber:",
        MAX_MATCHED_SOURCES,
    )

    if not accepted_sources:
        print(
            "[Diagnostic] Top skor V2 "
            "(belum tentu cocok):"
        )

        top_indices = np.argsort(
            scores
        )[::-1][:5]

        for index in top_indices:
            score = float(scores[int(index)])

            if not math.isfinite(score):
                continue

            (
                _,
                source_index,
                _,
                _,
                _,
            ) = locations[int(index)]

            title = literature[
                source_index
            ].get("title")

            print(
                f"  {score:.3f} - {title}"
            )

    print("====================================")
    print()

    return document_results
