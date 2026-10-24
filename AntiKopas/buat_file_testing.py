
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    KeepTogether,
)


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "testing_documents"
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "ANTIKOPAS_DOKUMEN_UJI_SEMANTIK.pdf"
)


# ==========================================
# DATA DOKUMEN UJI
# ==========================================

TITLE = (
    "Kajian Pemanfaatan Kecerdasan Buatan "
    "dalam Mendukung Kompetensi Akademik "
    "dan Motivasi Belajar Mahasiswa"
)

SUBTITLE = (
    "Dokumen Sintetis untuk Pengujian "
    "Sistem AntiKopas Academic V2"
)

SECTIONS = [
    (
        "ABSTRAK",
        [
            (
                "Kemajuan kecerdasan buatan memberikan "
                "peluang baru dalam pelaksanaan "
                "pembelajaran di perguruan tinggi. "
                "Teknologi seperti ChatGPT dapat "
                "mendukung mahasiswa dalam memahami "
                "konsep akademik, memperoleh penjelasan "
                "tambahan, dan menyelesaikan kegiatan "
                "belajar secara lebih efisien. "
                "Pemanfaatan teknologi ini juga "
                "berpotensi meningkatkan keterlibatan "
                "serta motivasi belajar melalui "
                "interaksi yang lebih personal."
            ),
            (
                "Di sisi lain, penggunaan kecerdasan "
                "buatan secara berlebihan dapat "
                "menimbulkan ketergantungan terhadap "
                "jawaban otomatis. Apabila mahasiswa "
                "hanya menerima keluaran sistem tanpa "
                "memeriksa kebenarannya, proses "
                "berpikir kritis dan pengembangan "
                "kemampuan analitis dapat terhambat. "
                "Oleh karena itu, pemanfaatan AI "
                "perlu disertai literasi digital, "
                "pengawasan akademik, dan etika "
                "penggunaan teknologi."
            ),
        ],
    ),
    (
        "1. PENDAHULUAN",
        [
            (
                "Artificial Intelligence atau AI "
                "semakin banyak digunakan untuk "
                "membantu mahasiswa mengakses "
                "informasi dan menjalankan aktivitas "
                "akademik. Dalam kegiatan perkuliahan, "
                "mahasiswa dapat menggunakan asisten "
                "berbasis AI untuk memperoleh "
                "penjelasan materi, membuat rangkuman, "
                "dan mengembangkan gagasan. "
                "Kecepatan layanan tersebut dapat "
                "mengurangi hambatan dalam memahami "
                "konsep yang sebelumnya dianggap sulit."
            ),
            (
                "Penggunaan ChatGPT dalam konteks "
                "pendidikan juga dapat membantu "
                "mahasiswa menyusun strategi belajar "
                "yang lebih fleksibel. Bantuan "
                "berupa penjelasan bertahap, contoh "
                "pemecahan masalah, dan umpan balik "
                "langsung dapat meningkatkan rasa "
                "percaya diri. Mahasiswa menjadi "
                "lebih terdorong untuk mencoba kembali "
                "ketika belum memahami suatu materi."
            ),
        ],
    ),
    (
        "2. KOMPETENSI AKADEMIK MAHASISWA",
        [
            (
                "Kecerdasan buatan berpotensi "
                "mendukung peningkatan kompetensi "
                "akademik karena mahasiswa memperoleh "
                "akses terhadap berbagai bentuk "
                "penjelasan dan sumber belajar. "
                "Teknologi pembelajaran adaptif "
                "mampu memberikan materi yang "
                "disesuaikan dengan kebutuhan "
                "pengguna. Proses ini dapat membantu "
                "penguasaan konsep, pengembangan "
                "kemampuan memecahkan masalah, "
                "dan pembelajaran mandiri."
            ),
            (
                "Pada kegiatan penyusunan tugas "
                "kuliah, ChatGPT dapat digunakan "
                "untuk membantu membuat kerangka "
                "tulisan dan memberikan alternatif "
                "penjelasan. Walaupun demikian, "
                "mahasiswa tetap harus menilai "
                "keakuratan informasi serta "
                "mengembangkan argumen dengan "
                "pemikiran sendiri. AI sebaiknya "
                "diposisikan sebagai alat pendukung, "
                "bukan pengganti kemampuan "
                "intelektual mahasiswa."
            ),
        ],
    ),
    (
        "3. MOTIVASI BELAJAR MAHASISWA",
        [
            (
                "Motivasi belajar berkaitan dengan "
                "dorongan mahasiswa untuk terlibat "
                "secara aktif dalam kegiatan "
                "pembelajaran. Pemanfaatan AI "
                "dapat menciptakan pengalaman belajar "
                "yang lebih interaktif dan personal. "
                "Ketika mahasiswa memperoleh umpan "
                "balik dengan cepat, mereka dapat "
                "mengetahui kesalahan, memperbaiki "
                "pemahaman, dan merasa lebih yakin "
                "dalam menyelesaikan tugas akademik."
            ),
            (
                "Penggunaan chatbot sebagai pendamping "
                "belajar memungkinkan mahasiswa "
                "mengajukan pertanyaan tanpa harus "
                "menunggu jadwal tatap muka. "
                "Ketersediaan bantuan tersebut "
                "dapat mengurangi kecemasan ketika "
                "mempelajari materi yang kompleks. "
                "Akan tetapi, motivasi yang sehat "
                "tetap memerlukan kemandirian "
                "dan keterlibatan aktif mahasiswa."
            ),
        ],
    ),
    (
        "4. RISIKO DAN ETIKA PENGGUNAAN AI",
        [
            (
                "Kemudahan memperoleh jawaban dari "
                "AI juga menimbulkan tantangan "
                "terhadap integritas akademik. "
                "Sebagian mahasiswa dapat tergoda "
                "untuk menyerahkan jawaban otomatis "
                "tanpa memahami proses penyusunannya. "
                "Kebiasaan tersebut berpotensi "
                "melemahkan keterampilan analisis, "
                "kemampuan berpikir kritis, dan "
                "tanggung jawab terhadap hasil "
                "pekerjaan akademik."
            ),
            (
                "Institusi pendidikan perlu "
                "mengembangkan pedoman pemanfaatan "
                "teknologi yang memperhatikan "
                "privasi data, transparansi, "
                "serta etika penulisan. Mahasiswa "
                "perlu didorong untuk melakukan "
                "verifikasi informasi dan "
                "menyebutkan bantuan AI secara "
                "bertanggung jawab apabila "
                "diwajibkan oleh kebijakan kampus."
            ),
        ],
    ),
    (
        "5. TOPIK KONTROL: EKOSISTEM LAUT",
        [
            (
                "Ekosistem padang lamun berperan "
                "dalam menjaga kestabilan sedimen "
                "di wilayah pesisir. Akar dan "
                "rimpang lamun membantu mengurangi "
                "pergerakan partikel dasar laut. "
                "Habitat tersebut juga menjadi "
                "tempat berlindung berbagai "
                "organisme perairan, termasuk "
                "ikan muda dan hewan bentik."
            ),
            (
                "Perubahan suhu perairan dan "
                "peningkatan kekeruhan dapat "
                "memengaruhi pertumbuhan lamun. "
                "Upaya konservasi dilakukan "
                "melalui pemantauan kualitas "
                "air, pengendalian aktivitas "
                "pesisir, dan rehabilitasi "
                "area yang rusak. Keberhasilan "
                "program konservasi perlu "
                "dinilai melalui indikator "
                "ekologis secara berkala."
            ),
        ],
    ),
    (
        "6. TOPIK KONTROL: PANGAN DAN PERTANIAN",
        [
            (
                "Pengelolaan irigasi merupakan "
                "faktor penting dalam budidaya "
                "tanaman padi. Ketersediaan "
                "air yang sesuai dengan tahap "
                "pertumbuhan membantu tanaman "
                "menyerap unsur hara dan "
                "mengurangi risiko penurunan "
                "produktivitas akibat kekeringan."
            ),
            (
                "Kualitas hasil panen juga "
                "dipengaruhi oleh penyimpanan "
                "setelah proses pengeringan. "
                "Kadar air gabah yang terlalu "
                "tinggi dapat mempercepat "
                "pertumbuhan mikroorganisme "
                "dan menurunkan mutu beras. "
                "Pengelolaan pascapanen yang "
                "tepat membantu menjaga "
                "ketahanan pangan."
            ),
        ],
    ),
    (
        "7. KESIMPULAN",
        [
            (
                "Pemanfaatan AI dapat mendukung "
                "pengembangan kompetensi dan "
                "motivasi belajar mahasiswa "
                "melalui pembelajaran adaptif, "
                "akses informasi yang cepat, "
                "dan bantuan akademik interaktif. "
                "Namun, manfaat tersebut perlu "
                "diimbangi dengan penggunaan "
                "yang bertanggung jawab agar "
                "mahasiswa tetap mengembangkan "
                "pemikiran kritis dan "
                "kemandirian belajar."
            ),
        ],
    ),
]


# ==========================================
# STYLING PDF
# ==========================================

styles = getSampleStyleSheet()

styles.add(
    ParagraphStyle(
        name="TestTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=21,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.HexColor("#17324D"),
    )
)

styles.add(
    ParagraphStyle(
        name="TestSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        spaceAfter=18,
        textColor=colors.HexColor("#526579"),
    )
)

styles.add(
    ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#17324D"),
    )
)

styles.add(
    ParagraphStyle(
        name="TestBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        spaceAfter=10,
        alignment=0,
    )
)


# ==========================================
# NOMOR HALAMAN
# ==========================================

def draw_footer(canvas, doc):

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.setFillColor(
        colors.grey
    )

    canvas.drawString(
        2 * cm,
        1.4 * cm,
        "DOKUMEN SINTETIS - HANYA UNTUK TESTING",
    )

    canvas.drawRightString(
        A4[0] - 2 * cm,
        1.4 * cm,
        f"Halaman {doc.page}",
    )

    canvas.restoreState()


# ==========================================
# GENERATE PDF
# ==========================================

def generate_test_pdf():

    doc = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=A4,
        rightMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    story = []

    story.append(
        Paragraph(
            TITLE,
            styles["TestTitle"],
        )
    )

    story.append(
        Paragraph(
            SUBTITLE,
            styles["TestSubtitle"],
        )
    )

    story.append(
        Paragraph(
            "Catatan: Dokumen ini dibuat "
            "secara sintetis untuk mengevaluasi "
            "seleksi semantik AntiKopas. "
            "Bukan artikel ilmiah yang dipublikasikan.",
            styles["TestBody"],
        )
    )

    for heading, paragraphs in SECTIONS:

        heading_block = Paragraph(
            heading,
            styles["SectionTitle"],
        )

        first_paragraph = Paragraph(
            paragraphs[0],
            styles["TestBody"],
        )

        story.append(
            KeepTogether([
                heading_block,
                first_paragraph,
            ])
        )

        for paragraph in paragraphs[1:]:

            story.append(
                Paragraph(
                    paragraph,
                    styles["TestBody"],
                )
            )

    doc.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    print()
    print("================================")
    print("PDF TESTING BERHASIL DIBUAT")
    print("================================")
    print("Lokasi:", OUTPUT_FILE)
    print("Ukuran:", OUTPUT_FILE.stat().st_size, "bytes")
    print("================================")


if __name__ == "__main__":
    generate_test_pdf()
