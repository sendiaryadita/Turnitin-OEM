from detector.services.document_parser import extract_text


file_path = "DRAF JURNAL DATA ANALISIS.pdf"

with open(file_path, "rb") as file:
    text = extract_text(file)


print("Jumlah karakter:", len(text))

print("\n===== HASIL EKSTRAKSI =====\n")
print(text[:2000])