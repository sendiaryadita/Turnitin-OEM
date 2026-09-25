from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file):
    """
    Mengambil teks dari file PDF.
    """

    reader = PdfReader(file)

    text = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text.append(page_text)

    return "\n".join(text)


def extract_text_from_docx(file):
    """
    Mengambil teks dari file DOCX.
    """

    document = Document(file)

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)


def extract_text(file):
    """
    Memilih parser berdasarkan ekstensi file.
    """

    filename = file.name.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file)

    if filename.endswith(".docx"):
        return extract_text_from_docx(file)

    raise ValueError(
        "Format file tidak didukung. Gunakan PDF atau DOCX."
    )