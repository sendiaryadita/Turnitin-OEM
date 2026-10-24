
"""
AntiKopas - Pembaruan Pipeline AI Multidomain

Menghasilkan full_pipeline.py lengkap berdasarkan
file lokal yang sudah ada.

Tidak mengubah:
- Cloudflare BGE-M3
- Academic CrossEncoder V2
- Threshold model
- PDF full-text retrieval
- Struktur output utama
- Rumus Similarity Index

Menghapus:
- Filter topik manual
- Daftar konsep manual
- Persyaratan keyword berdasarkan konsep terdaftar

Keamanan:
- Backup otomatis
- Validasi struktur
- Validasi syntax
- Tes fungsi
- Penulisan file setelah semua pemeriksaan lolos
"""

import ast
import re
import shutil
import unicodedata

from datetime import datetime
from pathlib import Path


# ==================================================
# LOKASI FILE
# ==================================================

ROOT = Path(__file__).resolve().parent

TARGET = (
    ROOT
    / "detector"
    / "services"
    / "full_pipeline.py"
)


# ==================================================
# FUNGSI PEMBANTU
# ==================================================

def replace_between(
    source,
    start_marker,
    end_marker,
    replacement,
):
    start = source.find(start_marker)

    if start == -1:
        raise RuntimeError(
            "Penanda awal tidak ditemukan:\n"
            + start_marker
        )

    end = source.find(
        end_marker,
        start + len(start_marker),
    )

    if end == -1:
        raise RuntimeError(
            "Penanda akhir tidak ditemukan:\n"
            + end_marker
        )

    if end <= start:
        raise RuntimeError(
            "Urutan penanda kode tidak valid."
        )

    return (
        source[:start]
        + replacement
        + source[end:]
    )


def replace_once(
    source,
    old,
    new,
):
    count = source.count(old)

    if count != 1:
        raise RuntimeError(
            "Struktur kode berubah.\n"
            f"Penanda ditemukan {count} kali.\n"
            f"Penanda: {old[:100]}"
        )

    return source.replace(old, new, 1)


# ==================================================
# VALIDASI PASANGAN BERBASIS AI
# ==================================================

NEW_VALIDATOR = '''# ==================================================
# 8. VALIDASI KANDIDAT UNTUK ACADEMIC V2
# ==================================================

def validate_pair_evidence(
    uploaded_chunk,
    source_excerpt,
):
    """
    Mempersiapkan pasangan untuk Academic V2.

    Tidak menggunakan daftar topik manual.

    BGE-M3 memilih kandidat berdasarkan semantik.
    Academic V2 menentukan kecocokan final.

    accepted=True hanya berarti pasangan boleh
    diperiksa oleh CrossEncoder, bukan sudah cocok.
    """

    uploaded_text = str(
        uploaded_chunk or ""
    ).strip()

    source_text = str(
        source_excerpt or ""
    ).strip()

    if not uploaded_text or not source_text:
        return {
            "accepted": False,
            "reason": "empty_passage",
            "shared_concepts": [],
            "shared_keywords": [],
        }

    # Kesamaan kata untuk audit laporan saja.
    # Tidak digunakan untuk menerima atau menolak.
    uploaded_words = set(
        re.findall(
            r"[^\\\\W\\\\d_]{4,}",
            uploaded_text.casefold(),
            flags=re.UNICODE,
        )
    )

    source_words = set(
        re.findall(
            r"[^\\\\W\\\\d_]{4,}",
            source_text.casefold(),
            flags=re.UNICODE,
        )
    )

    shared_terms = sorted(
        uploaded_words & source_words
    )

    return {
        "accepted": True,
        "reason": "semantic_candidate",
        "shared_concepts": [],
        "shared_keywords": shared_terms[:15],
    }


'''


# ==================================================
# PEMBARUAN FILE
# ==================================================

def main():
    print("=" * 58)
    print("ANTIKOPAS - PEMBARUAN AI MULTIDOMAIN")
    print("=" * 58)

    if not TARGET.is_file():
        raise RuntimeError(
            f"File tidak ditemukan:\n{TARGET}\n"
            "Simpan perbaiki_ai.py di folder AntiKopas."
        )

    original = TARGET.read_text(
        encoding="utf-8"
    )

    # Pastikan kode yang digunakan memang
    # pipeline baru yang sudah mendukung full text.
    required_features = (
        "def analyze_with_openalex(",
        "metadata_only=True",
        "upgrade_source_to_fulltext(",
        "MAX_FULLTEXT_PDF_ATTEMPTS",
        "cross_encoder.predict(",
        "MIN_EMBEDDING_SCORE = 0.65",
        "CROSS_THRESHOLD = 2.1285",
    )

    for feature in required_features:
        if feature not in original:
            raise RuntimeError(
                "Fitur penting tidak ditemukan:\n"
                + feature
                + "\nFile tidak diubah."
            )

    # Jika sudah pernah diperbarui, jangan
    # menjalankan perubahan yang sama lagi.
    if (
        "semantic_candidate" in original
        and "CONCEPT_PATTERNS = {" not in original
        and "if not relevant_to_topic(" not in original
    ):
        print("[INFO] Pipeline sudah menggunakan validasi AI.")
        print("[INFO] Tidak ada file yang diubah.")
        return

    updated = original

    # ----------------------------------------------
    # 1. HAPUS STOPWORDS KHUSUS FILTER MANUAL
    # ----------------------------------------------

    updated = replace_between(
        updated,
        "STOPWORDS = {",
        "def normalize_title(",
        "",
    )

    print("[OK] Daftar kata filter manual dihapus")

    # ----------------------------------------------
    # 2. HAPUS PEMERIKSAAN TOPIK BERBASIS KATA
    # ----------------------------------------------

    updated = replace_between(
        updated,
        "def topic_terms(",
        "def is_self_match(",
        "",
    )

    print("[OK] Filter topik manual dihapus")

    # ----------------------------------------------
    # 3. GANTI VALIDASI KONSEP DENGAN VALIDASI AI
    # ----------------------------------------------

    updated = replace_between(
        updated,
        (
            "# ==================================================\n"
            "# 8. VALIDASI KONSEP PER PASANGAN"
        ),
        (
            "# ==================================================\n"
            "# 9. QUERY OPENALEX"
        ),
        NEW_VALIDATOR,
    )

    print("[OK] Daftar konsep manual dihapus")
    print("[OK] Kandidat akan diteruskan ke Academic V2")

    # ----------------------------------------------
    # 4. HAPUS GERBANG TOPIK PADA OPENALEX
    # ----------------------------------------------

    old_topic_filter = '''            if not relevant_to_topic(
                document_title,
                title,
                abstract,
            ):
                stats["off_topic"] += 1
                continue

'''

    updated = replace_once(
        updated,
        old_topic_filter,
        "",
    )

    print("[OK] Jurnal tidak disaring berdasarkan daftar topik")

    # ----------------------------------------------
    # 5. PERBARUI LABEL DIAGNOSTIK
    # ----------------------------------------------

    updated = updated.replace(
        '                "off_topic",\n',
        "",
    )

    updated = updated.replace(
        '"[OpenAlex] Lolos filter topik:"',
        '"[OpenAlex] Lolos seleksi metadata:"',
    )

    updated = updated.replace(
        "# G. PILIH PASANGAN + VALIDASI KONSEP",
        "# G. PILIH PASANGAN BGE-M3 UNTUK ACADEMIC V2",
    )

    updated = updated.replace(
        "yang lolos validasi konsep.",
        "yang lolos seleksi BGE-M3.",
    )

    updated = updated.replace(
        "# Validasi bukti bersifat konservatif.\n"
        "MIN_SHARED_KEYWORDS = 3\n",
        "",
    )

    # ----------------------------------------------
    # 6. TAMBAHKAN PROVENANCE FULL TEXT
    # ----------------------------------------------

    old_excerpt = '''            "source_excerpt": source_text,
'''

    new_excerpt = '''            "source_excerpt": source_text,

            # Asal teks bukti untuk laporan.
            "text_scope": source.get(
                "text_scope", "abstract"
            ),
            "fulltext_status": source.get(
                "fulltext_status", "abstract_only"
            ),
            "fulltext_url": source.get(
                "fulltext_url"
            ),
            "fulltext_pages": source.get(
                "fulltext_pages", 0
            ),
'''

    updated = replace_once(
        updated,
        old_excerpt,
        new_excerpt,
    )

    print("[OK] Metadata sumber bukti ditambahkan")

    # ----------------------------------------------
    # 7. PERIKSA KODE LAMA SUDAH TIDAK AKTIF
    # ----------------------------------------------

    forbidden = (
        "CONCEPT_PATTERNS = {",
        "COMPILED_CONCEPTS = {",
        "DOMAIN_CONCEPTS = {",
        "def topic_terms(",
        "def relevant_to_topic(",
        "if not relevant_to_topic(",
        "MIN_SHARED_KEYWORDS = 3",
    )

    for item in forbidden:
        if item in updated:
            raise RuntimeError(
                "Filter manual masih ditemukan:\n"
                + item
                + "\nFile tidak diubah."
            )

    # ----------------------------------------------
    # 8. VALIDASI SYNTAX SELURUH PIPELINE
    # ----------------------------------------------

    tree = ast.parse(
        updated,
        filename=str(TARGET),
    )

    compile(
        tree,
        str(TARGET),
        "exec",
    )

    print("[OK] Syntax seluruh pipeline valid")

    # ----------------------------------------------
    # 9. UJI VALIDATOR TANPA MEMUAT MODEL
    # ----------------------------------------------

    validator_nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "validate_pair_evidence"
    ]

    if len(validator_nodes) != 1:
        raise RuntimeError(
            "Validator harus tersedia tepat satu kali."
        )

    isolated_module = ast.Module(
        body=validator_nodes,
        type_ignores=[],
    )

    namespace = {
        "re": re,
        "unicodedata": unicodedata,
    }

    exec(
        compile(
            isolated_module,
            "<test-validator>",
            "exec",
        ),
        namespace,
    )

    validator = namespace[
        "validate_pair_evidence"
    ]

    # Tidak boleh menolak bidang ilmu hanya
    # karena tidak ada di daftar konsep.
    samples = [
        (
            "Pengelolaan bank sampah plastik",
            "Pemanfaatan bank sampah untuk daur ulang",
        ),
        (
            "Pembahasan peraturan hukum pidana",
            "Kajian pertanggungjawaban hukum",
        ),
        (
            "Pengaruh kebijakan moneter terhadap inflasi",
            "Analisis harga dan pertumbuhan ekonomi",
        ),
        (
            "Penerapan kecerdasan buatan",
            "Penggunaan artificial intelligence",
        ),
    ]

    for left, right in samples:
        result = validator(left, right)

        if not result["accepted"]:
            raise RuntimeError(
                "Tes multidomain gagal."
            )

        if result["reason"] != "semantic_candidate":
            raise RuntimeError(
                "Status validator tidak sesuai."
            )

    empty_result = validator("", "")

    if empty_result["accepted"]:
        raise RuntimeError(
            "Teks kosong tidak boleh diterima."
        )

    print("[OK] Tes lintas topik berhasil")
    print("[OK] Teks kosong tetap ditolak")

    # ----------------------------------------------
    # 10. PASTIKAN THRESHOLD TETAP SAMA
    # ----------------------------------------------

    for setting in (
        "MIN_EMBEDDING_SCORE = 0.65",
        "CROSS_THRESHOLD = 2.1285",
        "MAX_FULLTEXT_PDF_ATTEMPTS = 2",
    ):
        if setting not in updated:
            raise RuntimeError(
                "Konfigurasi model berubah:\n"
                + setting
            )

    print("[OK] Threshold dan batas PDF dipertahankan")

    # ----------------------------------------------
    # 11. BUAT BACKUP DI LUAR REPOSITORY
    # ----------------------------------------------

    backup_dir = (
        Path.home()
        / "AntiKopas_Backups"
    )

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        backup_dir
        / f"full_pipeline_{timestamp}.py"
    )

    shutil.copy2(
        TARGET,
        backup_path,
    )

    print("[OK] Backup:", backup_path)

    # ----------------------------------------------
    # 12. SIMPAN FILE FINAL
    # ----------------------------------------------

    temporary_path = TARGET.with_suffix(
        ".py.new"
    )

    temporary_path.write_text(
        updated,
        encoding="utf-8",
    )

    # Pemeriksaan ulang file yang akan ditulis.
    final_content = temporary_path.read_text(
        encoding="utf-8"
    )

    compile(
        final_content,
        str(TARGET),
        "exec",
    )

    temporary_path.replace(TARGET)

    print("[OK] File lengkap diperbarui:")
    print(TARGET)

    print()
    print("=" * 58)
    print("BERHASIL - VALIDASI TOPIK MANUAL DIHAPUS")
    print("BGE-M3 DAN ACADEMIC V2 TETAP DIGUNAKAN")
    print("=" * 58)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("[GAGAL]", error)
        print(
            "Jika tidak muncul pesan BERHASIL, "
            "jangan gunakan hasil perubahan."
        )
        raise
