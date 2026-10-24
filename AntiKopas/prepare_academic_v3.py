
from pathlib import Path
import pandas as pd

# Pasangan sintetis baru:
# teks utama, parafrase setara, klaim berbeda

examples = [
    (
        "Pelatihan keamanan digital meningkatkan kemampuan staf mengenali pesan penipuan.",
        "Kemampuan staf mengidentifikasi pesan penipuan membaik setelah mengikuti pelatihan keamanan digital.",
        "Pelatihan keamanan digital justru menurunkan kemampuan staf mengenali pesan penipuan."
    ),
    (
        "Penggunaan pupuk hayati meningkatkan pertumbuhan akar tanaman jagung tanpa mengubah tinggi tanaman secara signifikan.",
        "Akar tanaman jagung tumbuh lebih baik setelah penggunaan pupuk hayati, tetapi tinggi tanaman tidak menunjukkan perubahan bermakna.",
        "Pupuk hayati meningkatkan tinggi tanaman jagung secara signifikan, sedangkan pertumbuhan akar tidak mengalami perubahan."
    ),
    (
        "Hasil survei menunjukkan bahwa kepuasan pelanggan berkorelasi positif dengan kecepatan layanan.",
        "Semakin cepat layanan diberikan, semakin tinggi kepuasan pelanggan menurut hasil survei.",
        "Survei membuktikan bahwa kecepatan layanan merupakan satu-satunya penyebab kepuasan pelanggan."
    ),
    (
        "Peneliti mengumpulkan data wawancara setelah menyelesaikan analisis kuesioner.",
        "Analisis jawaban kuesioner dilakukan lebih dahulu sebelum peneliti melaksanakan wawancara.",
        "Peneliti melakukan wawancara sebelum mengumpulkan dan menganalisis jawaban kuesioner."
    ),
    (
        "Perbedaan rata-rata tekanan darah antara kelompok perlakuan dan kontrol tidak signifikan.",
        "Tidak ditemukan selisih tekanan darah yang bermakna secara statistik antara kelompok intervensi dan pembanding.",
        "Rata-rata tekanan darah kelompok perlakuan secara signifikan lebih rendah daripada kelompok kontrol."
    ),
    (
        "Intensitas pelatihan berkaitan dengan peningkatan produktivitas, tetapi penelitian tidak membuktikan hubungan sebab-akibat.",
        "Produktivitas cenderung meningkat seiring intensitas pelatihan, meskipun hubungan kausal belum dapat disimpulkan.",
        "Penelitian membuktikan bahwa peningkatan intensitas pelatihan secara langsung menyebabkan produktivitas naik."
    ),
    (
        "Penerapan sistem antrean elektronik memperpendek waktu tunggu pasien di loket pendaftaran.",
        "Pasien menunggu lebih singkat pada proses pendaftaran setelah sistem antrean elektronik digunakan.",
        "Penerapan sistem antrean elektronik memperpanjang waktu tunggu pasien pada layanan pendaftaran."
    ),
    (
        "Pada kelompok yang menerima pendampingan, literasi keuangan berhubungan positif dengan ketepatan pencatatan transaksi.",
        "Hubungan searah antara literasi keuangan dan ketepatan pencatatan transaksi ditemukan pada peserta yang memperoleh pendampingan.",
        "Hubungan positif tersebut hanya ditemukan pada kelompok yang tidak memperoleh pendampingan."
    ),
    (
        "Pemanfaatan perangkat lunak analisis data mengurangi kesalahan penghitungan statistik deskriptif.",
        "Kesalahan dalam perhitungan statistik deskriptif menurun setelah perangkat lunak analisis data dimanfaatkan.",
        "Penggunaan perangkat lunak analisis data meningkatkan kesalahan perhitungan statistik deskriptif."
    ),
    (
        "Metode pembelajaran kolaboratif meningkatkan kemampuan siswa menyampaikan alasan dalam diskusi.",
        "Siswa menjadi lebih mampu mengemukakan argumentasi selama diskusi setelah mengikuti pembelajaran kolaboratif.",
        "Pembelajaran kolaboratif meningkatkan kecepatan membaca siswa, tetapi kemampuan argumentasi tidak diukur."
    ),
    (
        "Penerapan pengawasan mutu berkala menurunkan persentase produk yang gagal memenuhi standar.",
        "Proporsi produk tidak sesuai standar berkurang ketika pemeriksaan kualitas dilakukan secara berkala.",
        "Persentase produk tidak sesuai standar meningkat setelah pemeriksaan kualitas berkala diterapkan."
    ),
    (
        "Penggunaan transportasi umum berkorelasi negatif dengan jumlah kendaraan pribadi yang memasuki pusat kota.",
        "Semakin tinggi penggunaan angkutan umum, semakin sedikit kendaraan pribadi yang tercatat memasuki pusat kota.",
        "Penggunaan angkutan umum berhubungan dengan peningkatan jumlah kendaraan pribadi di pusat kota."
    ),
    (
        "Program literasi informasi membantu mahasiswa membedakan sumber ilmiah dan sumber yang tidak terverifikasi.",
        "Kemampuan mahasiswa memilah rujukan akademik dari informasi yang belum tervalidasi meningkat setelah program literasi informasi.",
        "Program literasi informasi meningkatkan minat mahasiswa mengikuti organisasi, tetapi ketepatan pemilihan sumber tidak dianalisis."
    ),
    (
        "Peningkatan transparansi anggaran berhubungan dengan bertambahnya kepercayaan masyarakat terhadap pemerintah desa.",
        "Kepercayaan warga kepada pemerintah desa cenderung lebih tinggi ketika informasi anggaran disampaikan secara terbuka.",
        "Penelitian menunjukkan kepercayaan masyarakat menurun seiring meningkatnya keterbukaan informasi anggaran desa."
    ),
    (
        "Pelatihan pertolongan pertama meningkatkan ketepatan tindakan awal petugas saat menghadapi kondisi darurat.",
        "Petugas mengambil tindakan awal yang lebih tepat dalam situasi darurat setelah memperoleh pelatihan pertolongan pertama.",
        "Pelatihan pertolongan pertama meningkatkan kecepatan administrasi petugas, sementara ketepatan penanganan darurat tidak dievaluasi."
    ),
    (
        "Penambahan vegetasi peneduh menurunkan suhu permukaan pada jalur pejalan kaki.",
        "Suhu permukaan lintasan pedestrian berkurang setelah jumlah tanaman peneduh ditingkatkan.",
        "Penambahan tanaman peneduh justru meningkatkan suhu permukaan pada jalur pedestrian."
    ),
    (
        "Analisis menunjukkan bahwa tingkat pengangguran dan daya beli rumah tangga memiliki hubungan negatif.",
        "Daya beli rumah tangga cenderung menurun ketika tingkat pengangguran meningkat.",
        "Penelitian menemukan daya beli rumah tangga meningkat seiring kenaikan tingkat pengangguran."
    ),
    (
        "Audit internal yang lebih sering berkaitan dengan peningkatan kepatuhan pelaporan keuangan.",
        "Semakin rutin pemeriksaan internal dilakukan, semakin tinggi kepatuhan terhadap ketentuan laporan keuangan.",
        "Frekuensi audit internal yang lebih tinggi berkaitan dengan penurunan kepatuhan pelaporan keuangan."
    ),
    (
        "Pemakaian media pembelajaran visual meningkatkan pemahaman konsep geometri tanpa memperbaiki kecepatan menyelesaikan soal.",
        "Media visual membantu siswa memahami geometri, tetapi waktu yang dibutuhkan untuk menyelesaikan soal tidak membaik.",
        "Media pembelajaran visual mempercepat penyelesaian soal geometri secara signifikan tanpa meningkatkan pemahaman konsep."
    ),
    (
        "Penelitian observasional menemukan hubungan antara aktivitas fisik rutin dan kualitas tidur yang lebih baik.",
        "Individu yang lebih teratur beraktivitas fisik cenderung memiliki kualitas tidur lebih baik berdasarkan pengamatan penelitian.",
        "Eksperimen acak membuktikan bahwa aktivitas fisik merupakan penyebab tunggal peningkatan kualitas tidur."
    ),
]

new_rows = []

for text_a, positive, negative in examples:
    new_rows.append({
        "text_a": text_a,
        "text_b": positive,
        "label": 1,
        "source": "academic_v3_synthetic"
    })
    new_rows.append({
        "text_a": text_a,
        "text_b": negative,
        "label": 0,
        "source": "academic_v3_synthetic"
    })

# Dataset akademik yang sebelumnya hanya bagian train
old_path = Path(
    "dataset/academic_v2/academic_train_v2.csv"
)

if not old_path.exists():
    raise FileNotFoundError(old_path)

old = pd.read_csv(old_path)

required = {"text_a", "text_b", "label"}
if not required.issubset(old.columns):
    raise ValueError("Kolom dataset V2 tidak sesuai")

old = old[["text_a", "text_b", "label"]].copy()
old["source"] = "academic_v2_train"

new = pd.DataFrame(new_rows)

# Gabungkan hanya data training
combined = pd.concat(
    [old, new],
    ignore_index=True
)

combined = combined.dropna(
    subset=["text_a", "text_b", "label"]
)

combined["label"] = combined["label"].astype(int)

# Deteksi pasangan bolak-balik
combined["pair_key"] = combined.apply(
    lambda r: " || ".join(sorted([
        r["text_a"].strip().casefold(),
        r["text_b"].strip().casefold()
    ])),
    axis=1
)

conflicts = combined.groupby(
    "pair_key"
)["label"].nunique()

if (conflicts > 1).any():
    raise ValueError(
        "Ada pasangan sama dengan label bertentangan!"
    )

combined = combined.drop_duplicates(
    subset=["pair_key"]
).drop(columns=["pair_key"])

combined = combined.sample(
    frac=1, random_state=42
).reset_index(drop=True)

output_dir = Path("dataset/academic_v3")
output_dir.mkdir(parents=True, exist_ok=True)

output = output_dir / "train.csv"

combined.to_csv(
    output,
    index=False,
    encoding="utf-8-sig"
)

print("\n=== DATASET V3 BERHASIL DIBUAT ===")
print("File:", output)
print("Jumlah pasangan:", len(combined))
print("Distribusi label:")
print(combined["label"].value_counts())
print("\nCatatan: label tambahan masih perlu diperiksa manual.")
