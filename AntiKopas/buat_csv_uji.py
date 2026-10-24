
import csv
import random
from pathlib import Path

# Format:
# bidang, teks_asli, parafrase, klaim_berbeda, kontradiksi

DATA = [
    (
        "Pendidikan",
        "Hasil penelitian menunjukkan bahwa pembelajaran berbasis proyek meningkatkan kemampuan berpikir kritis siswa, berdasarkan perbandingan nilai sebelum dan sesudah pembelajaran.",
        "Perbandingan hasil pengukuran awal dan akhir memperlihatkan peningkatan kemampuan berpikir kritis siswa setelah penerapan pembelajaran berbasis proyek.",
        "Pembelajaran berbasis proyek meningkatkan keterampilan kerja sama siswa, sedangkan kemampuan berpikir kritis tidak dianalisis dalam penelitian tersebut.",
        "Penelitian menemukan penurunan kemampuan berpikir kritis siswa setelah pembelajaran berbasis proyek diterapkan."
    ),
    (
        "Teknologi Informasi",
        "Penggunaan autentikasi dua faktor berkorelasi positif dengan keberhasilan pencegahan akses tidak sah pada layanan akademik daring.",
        "Pada layanan akademik berbasis internet, tingkat keberhasilan mencegah akses ilegal cenderung lebih tinggi ketika penggunaan autentikasi dua faktor meningkat.",
        "Autentikasi dua faktor berkaitan dengan kemudahan pengguna mengingat prosedur masuk akun, tetapi penelitian tidak mengukur pencegahan akses ilegal.",
        "Semakin intensif autentikasi dua faktor digunakan, semakin rendah keberhasilan mencegah akses tidak sah."
    ),
    (
        "Kesehatan Masyarakat",
        "Program edukasi kebersihan tangan meningkatkan pengetahuan pencegahan penyakit menular pada siswa sekolah dasar.",
        "Pengetahuan siswa sekolah dasar mengenai pencegahan penyakit menular mengalami peningkatan setelah mereka mengikuti edukasi kebersihan tangan.",
        "Program edukasi kebersihan tangan meningkatkan kepuasan siswa terhadap fasilitas sekolah tanpa mengevaluasi pengetahuan tentang penyakit menular.",
        "Edukasi kebersihan tangan menyebabkan pengetahuan pencegahan penyakit menular pada siswa mengalami penurunan."
    ),
    (
        "Keperawatan",
        "Pelaksanaan pemeriksaan pasien secara terjadwal meningkatkan kelengkapan dokumentasi tindakan keperawatan di ruang rawat inap.",
        "Dokumentasi tindakan keperawatan menjadi lebih lengkap ketika pemeriksaan pasien di ruang rawat inap dilakukan sesuai jadwal.",
        "Pemeriksaan pasien yang terjadwal mempercepat pergantian giliran perawat, tetapi tidak mengukur kelengkapan dokumentasi tindakan.",
        "Kelengkapan dokumentasi tindakan keperawatan menurun setelah pemeriksaan pasien secara terjadwal diterapkan."
    ),
    (
        "Psikologi",
        "Survei mahasiswa menemukan hubungan negatif antara durasi penggunaan media sosial pada malam hari dan kualitas tidur.",
        "Kualitas tidur mahasiswa cenderung lebih rendah ketika waktu yang mereka habiskan untuk menggunakan media sosial pada malam hari semakin panjang.",
        "Penelitian menghubungkan penggunaan media sosial pada malam hari dengan frekuensi komunikasi mahasiswa, bukan dengan kualitas tidur mereka.",
        "Hasil survei menyatakan bahwa semakin lama mahasiswa menggunakan media sosial pada malam hari, semakin baik kualitas tidurnya."
    ),
    (
        "Ekonomi",
        "Peningkatan literasi keuangan berhubungan positif dengan kemampuan mahasiswa menyusun anggaran pengeluaran bulanan.",
        "Mahasiswa dengan literasi keuangan lebih tinggi cenderung memiliki kemampuan lebih baik dalam merencanakan pengeluaran setiap bulan.",
        "Penelitian literasi keuangan mahasiswa berfokus pada minat investasi saham dan tidak mengevaluasi penyusunan anggaran bulanan.",
        "Mahasiswa yang mempunyai literasi keuangan lebih tinggi justru menunjukkan kemampuan penyusunan anggaran yang lebih rendah."
    ),
    (
        "Manajemen",
        "Kelompok pegawai dengan intensitas penerapan kerja hibrida tinggi melaporkan kepuasan pengaturan lokasi kerja lebih baik daripada kelompok berintensitas rendah.",
        "Kepuasan pegawai dalam menentukan lokasi bekerja lebih tinggi pada kelompok yang lebih sering menjalankan kebijakan kerja hibrida.",
        "Pegawai yang sering menjalankan kerja hibrida memiliki waktu perjalanan lebih singkat, tetapi penelitian tidak membandingkan kepuasan pengaturan lokasi kerja.",
        "Kelompok dengan intensitas kerja hibrida rendah memiliki kepuasan pengaturan lokasi kerja lebih tinggi dibandingkan kelompok berintensitas tinggi."
    ),
    (
        "Akuntansi",
        "Penggunaan aplikasi pencatatan transaksi membantu usaha mikro mengurangi kesalahan pengelompokan pemasukan dan pengeluaran.",
        "Kesalahan klasifikasi penerimaan dan biaya pada usaha mikro berkurang setelah aplikasi pencatatan transaksi digunakan.",
        "Aplikasi pencatatan transaksi membantu usaha mikro mengiklankan produk secara digital, tetapi tidak digunakan untuk mengelompokkan pemasukan dan biaya.",
        "Kesalahan pengelompokan pemasukan dan pengeluaran justru meningkat setelah usaha mikro menggunakan aplikasi pencatatan transaksi."
    ),
    (
        "Hukum",
        "Pelaksanaan mediasi sebelum persidangan berhasil mengurangi jumlah sengketa perdata yang berlanjut ke tahap pemeriksaan hakim.",
        "Lebih sedikit sengketa perdata diteruskan ke pemeriksaan hakim ketika para pihak lebih dahulu menempuh proses mediasi.",
        "Pelaksanaan mediasi meningkatkan pemahaman masyarakat mengenai prosedur pengadilan tanpa mengukur jumlah perkara yang berlanjut.",
        "Mediasi sebelum persidangan menyebabkan lebih banyak sengketa perdata diteruskan ke tahap pemeriksaan hakim."
    ),
    (
        "Administrasi Publik",
        "Digitalisasi proses perizinan memperpendek rata-rata waktu penyelesaian permohonan izin usaha pada kantor pelayanan daerah.",
        "Rata-rata durasi penyelesaian izin usaha di kantor pelayanan daerah berkurang setelah prosedur perizinan dialihkan ke sistem digital.",
        "Digitalisasi perizinan meningkatkan jumlah pemohon yang menggunakan layanan daring, tetapi penelitian tidak membahas waktu penyelesaian.",
        "Setelah digitalisasi perizinan diterapkan, rata-rata waktu penyelesaian permohonan izin usaha menjadi lebih panjang."
    ),
    (
        "Ilmu Komunikasi",
        "Personalisasi pesan kampanye berkorelasi positif dengan tingkat keterlibatan penerima buletin elektronik.",
        "Tingkat interaksi penerima buletin elektronik cenderung meningkat seiring dengan tingginya penggunaan pesan kampanye yang dipersonalisasi.",
        "Personalisasi pesan kampanye berkaitan dengan biaya produksi buletin elektronik, sedangkan keterlibatan penerima tidak dianalisis.",
        "Penggunaan pesan kampanye yang semakin personal berhubungan dengan semakin rendahnya keterlibatan penerima buletin elektronik."
    ),
    (
        "Sosiologi",
        "Partisipasi rutin dalam kegiatan warga berkaitan dengan tingkat kepercayaan sosial yang lebih tinggi di lingkungan permukiman.",
        "Warga yang lebih sering mengikuti kegiatan lingkungan cenderung memiliki kepercayaan sosial lebih tinggi terhadap sesama penghuni permukiman.",
        "Kegiatan warga berkaitan dengan penataan fasilitas umum, tetapi penelitian tidak menilai tingkat kepercayaan sosial.",
        "Semakin sering warga berpartisipasi dalam kegiatan lingkungan, semakin rendah tingkat kepercayaan sosial yang mereka laporkan."
    ),
    (
        "Pertanian",
        "Penerapan irigasi tetes mengurangi penggunaan air pada budidaya cabai tanpa menurunkan hasil panen secara signifikan.",
        "Budidaya cabai dengan sistem irigasi tetes menggunakan lebih sedikit air, sementara hasil panennya tidak mengalami penurunan yang bermakna secara statistik.",
        "Irigasi tetes meningkatkan kemudahan penjadwalan pemupukan cabai, tetapi penggunaan air dan hasil panen tidak diukur.",
        "Irigasi tetes meningkatkan kebutuhan air dan menyebabkan penurunan hasil panen cabai yang signifikan."
    ),
    (
        "Lingkungan",
        "Program pemilahan sampah rumah tangga menurunkan proporsi sampah tercampur yang dikirim ke tempat pembuangan akhir.",
        "Jumlah relatif sampah yang masih bercampur dan berakhir di tempat pembuangan akhir berkurang setelah program pemilahan rumah tangga diterapkan.",
        "Program pemilahan sampah meningkatkan kesadaran warga mengenai daur ulang, tetapi tidak mengevaluasi proporsi sampah tercampur.",
        "Setelah program pemilahan rumah tangga diterapkan, proporsi sampah tercampur yang dikirim ke tempat pembuangan akhir justru meningkat."
    ),
    (
        "Teknik Sipil",
        "Penambahan serat pada campuran beton meningkatkan ketahanan terhadap retak awal, tetapi tidak menghasilkan peningkatan kuat tekan yang signifikan.",
        "Campuran beton berserat memiliki ketahanan retak dini lebih baik, sementara perubahan kuat tekannya tidak bermakna secara statistik.",
        "Penambahan serat pada beton memengaruhi kemudahan proses pengecoran, sedangkan ketahanan retak dan kuat tekan tidak diuji.",
        "Beton yang diberi serat menunjukkan ketahanan retak awal lebih rendah dan peningkatan kuat tekan yang signifikan."
    ),
    (
        "Teknik Industri",
        "Penerapan daftar periksa kualitas menurunkan jumlah produk cacat pada lini pengemasan dibandingkan kondisi sebelum intervensi.",
        "Jumlah cacat produk di lini pengemasan berkurang setelah prosedur pemeriksaan menggunakan daftar periksa kualitas diterapkan.",
        "Daftar periksa kualitas mempercepat proses pelatihan operator pengemasan, tetapi jumlah produk cacat tidak dievaluasi.",
        "Setelah daftar periksa kualitas diterapkan, jumlah produk cacat pada lini pengemasan mengalami peningkatan."
    ),
    (
        "Pariwisata",
        "Pengembangan wisata berbasis komunitas meningkatkan keterlibatan pelaku usaha lokal dalam penyediaan layanan wisata.",
        "Pelaku usaha setempat menjadi lebih banyak terlibat dalam layanan wisata setelah pendekatan pariwisata berbasis komunitas dikembangkan.",
        "Pengembangan wisata berbasis komunitas meningkatkan jumlah unggahan promosi destinasi, tetapi tidak mengukur partisipasi pelaku usaha lokal.",
        "Penerapan wisata berbasis komunitas mengurangi keterlibatan pelaku usaha lokal dalam penyediaan layanan wisata."
    ),
    (
        "Kewirausahaan",
        "Pendampingan pemasaran digital membantu usaha kecil memperluas jangkauan calon pelanggan di luar wilayah penjualan sebelumnya.",
        "Usaha kecil dapat menjangkau lebih banyak calon pembeli dari wilayah baru setelah menerima pendampingan dalam pemasaran digital.",
        "Pendampingan pemasaran digital meningkatkan kemampuan pemilik usaha membuat laporan kas, tetapi tidak mengukur jangkauan calon pelanggan.",
        "Setelah mengikuti pendampingan pemasaran digital, jangkauan calon pelanggan usaha kecil justru menyempit."
    ),
    (
        "Bahasa dan Sastra",
        "Diskusi kelompok setelah kegiatan membaca meningkatkan kemampuan siswa mengidentifikasi gagasan utama dalam teks eksposisi.",
        "Kemampuan menemukan ide pokok teks eksposisi pada siswa meningkat ketika pembacaan dilanjutkan dengan diskusi kelompok.",
        "Diskusi kelompok setelah membaca membantu siswa menghafal istilah sastra, tetapi tidak menguji kemampuan menemukan gagasan utama.",
        "Kemampuan siswa menentukan gagasan utama teks eksposisi menurun setelah kegiatan membaca disertai diskusi kelompok."
    ),
    (
        "Ilmu Politik",
        "Pendidikan pemilih pemula meningkatkan pemahaman mahasiswa terhadap tahapan pemungutan dan penghitungan suara.",
        "Mahasiswa menjadi lebih memahami prosedur pencoblosan serta penghitungan suara setelah mengikuti pendidikan bagi pemilih pemula.",
        "Pendidikan pemilih pemula meningkatkan ketertarikan mahasiswa terhadap debat politik, tetapi tidak mengukur pemahaman prosedur pemungutan suara.",
        "Pemahaman mahasiswa mengenai tahapan pemungutan dan penghitungan suara berkurang setelah mengikuti pendidikan pemilih pemula."
    ),
]

rows = []

for bidang, text_a, paraphrase, different, contradiction in DATA:
    rows.extend([
        {
            "text_a": text_a,
            "text_b": paraphrase,
            "label": 1,
            "bidang": bidang,
            "jenis_pasangan": "parafrase",
            "data_origin": "synthetic_demo",
        },
        {
            "text_a": text_a,
            "text_b": different,
            "label": 0,
            "bidang": bidang,
            "jenis_pasangan": "topik_sama_klaim_berbeda",
            "data_origin": "synthetic_demo",
        },
        {
            "text_a": text_a,
            "text_b": contradiction,
            "label": 0,
            "bidang": bidang,
            "jenis_pasangan": "kontradiksi",
            "data_origin": "synthetic_demo",
        },
    ])

random.Random(42).shuffle(rows)

output = Path("dataset/academic_real_test.csv")
output.parent.mkdir(parents=True, exist_ok=True)

columns = [
    "text_a", "text_b", "label",
    "bidang", "jenis_pasangan", "data_origin"
]

with output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

assert len(rows) == 60
assert sum(r["label"] == 1 for r in rows) == 20
assert sum(r["label"] == 0 for r in rows) == 40

print("CSV berhasil dibuat!")
print("Lokasi:", output)
print("Total:", len(rows), "pasangan")
print("Label 1: 20 | Label 0: 40")
