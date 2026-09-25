from detector.services.openalex import search_literature


results = search_literature(
    "regulasi emosi remaja",
    per_page=5
)

print(f"Jumlah hasil: {len(results)}")

for i, result in enumerate(results, start=1):
    print(f"\n--- Literatur {i} ---")
    print(f"Judul : {result['title']}")
    print(f"Tahun : {result['year']}")
    print(f"DOI   : {result['doi']}")
    print(f"TEXT  : {result['text'][:500]}")