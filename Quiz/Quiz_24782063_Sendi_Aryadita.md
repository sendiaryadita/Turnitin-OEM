## Bagian 1. Identitas dan Topik Proyek Aplikasi

**Nama Aplikasi:** AntiKopas

**Deskripsi Singkat dan Tujuan Utama:**

AntiKopas itu platform berbasis web buat ngecek tingkat kemiripan teks di tugas akhir, makalah, atau artikel ilmiah terhadap sumber literatur terbuka. Masalah yang mau diselesaikan simpel sih: ngebantu mahasiswa biar ngga ragu sama keaslian tulisannya sebelum dikumpulin ke dosen. Secara teknis, sistem ini mengekstrak teks lalu memprosesnya pakai model AI `paraphrase-multilingual-MiniLM-L12-v2` dari *library* `sentence-transformers` buat ngebaca kemiripan makna, yang kemudian dicocokin langsung sama database publik lewat OpenAlex API. Nantinya, aplikasi bakal nampilin bagian teks mana aja yang terindikasi mirip beserta sumber referensinya, jadi pengguna bisa langsung revisi, benerin sitasi, atau parafrase mandiri tanpa ribet.

**Target Pengguna Utama:**

Mahasiswa aktif yang lagi ngerjain tugas, laporan, atau karya tulis ilmiah.

---

## Bagian 2. Resume Modul Digital Awareness

**1. Modul 1: There's a whole new world out there!**

Inti modul ini ngebahas transisi gila-gilaan dari dunia analog ke digital. Internet yang dulunya cuma teks statis, sekarang udah masuk era Web 2.0 yang interaktif banget (e-commerce, medsos). Terus ada konsep IoT (Internet of Things) yang bikin barang fisik sehari-hari bisa konek ke internet dan jadi pinter. Dampaknya kerasa banget, kayak kebiasaan ngantri di bank sekarang pindah ke *mobile banking*. Layanannya juga diklasifikasiin jadi tiga: publik (situs pemerintah), privat (layanan berbayar), dan komunitas (medsos atau Wikipedia).

**2. Modul 2: You'll Need Some Basic Tools**

Fokusnya di pengenalan *hardware*, tipe koneksi (kabel vs Bluetooth), sampai OS kayak Windows atau Android yang jadi otak perangkat. Kita juga diajarin manajemen data yang rapi pake *file explorer*—intinya bikin folder dan namain file secara spesifik biar gampang dicari, ngga cuma ditumpuk berantakan di *desktop*. Buat urusan keamanan, modul ini nekenin banget buat bikin *password* yang kuat. Hindari pake urutan angka atau tanggal lahir, dan beralih ke kombinasi huruf, angka, simbol, atau pake *passphrase* (frasa panjang) biar akun ngga gampang dibobol.

**3. Modul 3: This is how you get around and find what you're looking for**

Modul ini ngasih trik *searching* efisien di mesin pencari, kayak pake tanda kutip ("") buat nyari kata pasti, tanda minus (-) buat nge-blok kata tertentu, atau `filetype:` buat nyari ekstensi file spesifik. Dibahas juga penggunaan *shortcut* `Ctrl+F` buat nyari teks, plus pengelolaan *cookies* dan *bookmarks*. Buat *developer*, poin paling krusialnya itu paham soal HAKI (Hak Kekayaan Intelektual). Kita wajib bisa bedain mana aset yang kena *copyright* penuh, mana yang pake lisensi *Creative Commons*, dan mana yang *Public Domain* atau *open-source* yang bebas kita manfaatin.

**4. Modul 4: It just keeps getting better**

Ngebahas lonjakan teknologi kayak AI dan LLMs (*Large Language Models*) yang sekarang bisa niru cara manusia belajar dan mecahin masalah. AI itu pada dasarnya netral, masalah etika biasanya muncul kalau data pelatihannya ngandung bias manusia. Makanya kita diwajibin punya etika internet: sopan, mikir dulu sebelum *posting*, dan ngga asal bercanda. Kita juga diajarin tanggung jawab digital, kayak ngebatesin *screen time*, nangkis misinformasi/*hoax*, dan sadar kalau perangkat kita itu terus nyedot listrik. Terakhir, karena aktivitas kita pasti ninggalin *digital footprint*, kita harus rajin ngecek *privacy settings* dan hapus akun lama.

**5. Modul 5: Even Though It's Digital, It is Real, With Real Consequences**

Poin utamanya ngingetin kalau tiap interaksi online kita bakal ngebentuk *digital personal* atau (jejak digital) yang sifatnya permanen, baik itu secara sosial, profesional, maupun sebagai konsumen. Jadi kita ngga boleh sembarangan ngelola Data Pribadi Sensitif (PII). Modul ini juga ngebongkar modus penipuan siber, mulai dari *phishing*, penipuan kedok asmara, sampai manipulasi sadis kayak *pig butchering scam*. Kita juga dilarang keras pake *software crack* atau *torrent* bajakan. Sebagai langkah *defense*, kita dituntut ngaktifin 2FA (*Two-Factor Authentication*) dan pake *tools* tambahan kayak VPN atau *Incognito mode* buat ngejaga privasi.

**6. Modul 6: Learn About Anything and Everything**

Modul penutup ini ngelatih kita buat ngga panik dan bisa *troubleshooting* mandiri pas ada masalah teknis, kayak ngecek *power*, matiin *background process* lewat *restart*, ngosongin *storage*, atau *update/reinstall software*. Selain itu, buat nutupin *skills gap* di ranah IT yang cepet banget berubah, kita didorong buat terus belajar otodidak manfaatin *platform online* (kayak Cisco NetAcad atau MOOCs), *webinar*, baca *e-book*, atau nongkrong di forum diskusi komunitas.

---

## BAGIAN 3. Hubungan dan Implementasi pada Topik Proyek

**1. Bagaimana rancangan aplikasi dapat mempermudah tugas sehari-hari pengguna? Apa proses “analog/tradisional” dari topik proyekmu yang berhasil disederhanakan menjadi digital.**

Rancangan aplikasi AntiKopas sangat mempermudah tugas mahasiswa dengan mengotomatisasi proses deteksi kemiripan teks yang biasanya memakan banyak waktu.

**Proses Analog/Tradisional:** Secara tradisional, proses verifikasi keaslian karya tulis sangat melelahkan. mahasiswa harus membaca dokumen secara manual, mengingat-ingat kalimatnya, lalu mencari sumber pembanding satu per satu di perpustakaan atau mesin pencari untuk memastikan tidak ada indikasi plagiarisme.

**Transformasi Digital:** AntiKopas mendigitalkan dan mengambil alih beban kerja tersebut. Pengguna cukup memasukkan teks atau mengunggah file karya tulis ke dalam sistem. Algoritma pemrosesan teks aplikasi akan membedah kalimat tersebut dan mencocokkannya secara otomatis dengan basis data literatur terbuka seperti OpenAlex. Hasilnya langsung tersaji berupa indikasi kemiripan beserta sumber referensinya, sehingga menghemat waktu berjam-jam menjadi hanya dalam hitungan menit saja.

**2. Jika aplikasimu memiliki fitur penyimpanan file atau pendaftaran akun, bagaimana kamu merancang struktur penyimpanan file yang intuitif bagi pengguna awam? Bagaimana kamu membantu pengguna membuat kata sandi yang aman?**

Sebagai aplikasi yang memproses dokumen tugas akhir atau makalah, tata kelola file dan perlindungan akun di AntiKopas harus dirancang dengan rapi dan aman, baik dari sisi pengguna awam maupun di level server.

**Rancangan Struktur Penyimpanan File:**

Untuk mencegah penumpukan data yang berantakan, sistem di backend akan memisahkan direktori secara hierarkis, misalnya membedakan folder `Dokumen_Mentah` dengan `Laporan_Hasil`, yang diurutkan berdasarkan ID pengguna. Namun, untuk pengguna awam di sisi antarmuka frontend, struktur ini disederhanakan menjadi menu "Riwayat Pengecekan". Pengguna tidak perlu membuat folder sendiri; sistem akan otomatis merapikan dan menamai ulang file mereka dengan kata lain auto-rename menjadi format standar. Dengan begitu, saat mahasiswa ingin mencari ulang hasil persentasenya, mereka bisa langsung menggunakan search bar di dashboard tanpa pusing mencari file.

**Bantuan Pembuatan Kata Sandi:**

Pada halaman registrasi, AntiKopas akan menyematkan indikator kekuatan sandi password strength meter. Sistem akan secara otomatis memblokir penggunaan sandi lemah seperti urutan angka `12345` atau nama depan dan mewajibkan kombinasi huruf, angka, serta karakter khusus. Untuk membantu mahasiswa yang malas menghafal sandi rumit, form pendaftaran akan menyarankan penggunaan passphrase kalimat panjang yang unik namun mudah diingat. Sebagai tambahan keamanan di balik layar, seluruh kata sandi akan diamankan menggunakan algoritma, sehingga tidak ada password yang tersimpan dalam bentuk teks mentah plaintext di dalam database kami.

**3. Bagaimana kamu mendesain fitur pencarian (search bar) di dalam aplikasi agar pengguna dapat mencari informasi dengan mudah? Selain itu, sebutkan asset eksternal yang digunakan dalam aplikasi (library, API, gambar, icon). Apakah asset-aset tersebut berlisensi open-source, public domain, atau memiliki hak cipta khusus yang wajib dicantumkan?**

Fitur *search bar* didesain sesederhana mungkin agar pengguna cukup mengetikkan judul karya tulis untuk melacak sumber literatur secara otomatis, dengan memanfaatkan seluruh aset eksternal yang legal dan berlisensi *open-source*, seperti OpenAlex API untuk pangkalan data, *library* Python (`requests`, `sentence-transformers`, serta pustaka ekstraksi dokumen), dan model AI `paraphrase-multilingual-MiniLM-L12-v2`.

**4. Jika aplikasimu memiliki fitur interaksi social, bagaimana kamu mencegah pelanggaran etika digital di dalamnya? Jika aplikasi menggunakan fitur pintar berbasis AI, bagaimana kamu memastikan AI tersebut bekerja secara etis dan bertanggung jawab bagi pengguna?**

**Pencegahan Pelanggaran Etika Digital:**

Secara desain, kami memang sengaja tidak menyematkan fitur interaksi sosial (seperti *live chat*, forum, atau kolom komentar publik) di dalam AntiKopas. Keputusan ini diambil untuk menutup celah terjadinya pelanggaran, seperti cyberbullying atau saling ejek antar mahasiswa terkait hasil pengecekan dokumen. Fokus utama aplikasi ini adalah sebagai alat produktivitas personal. Dengan mengisolasi interaksi, pengguna bisa mengecek dokumennya dengan tenang tanpa takut dihakimi secara sosial oleh pengguna lain.

**Tanggung Jawab Penggunaan AI:**

Karena AntiKopas digerakkan oleh AI (model *Sentence Transformer*), kami sadar betul bahwa AI tidak luput dari bias dan kesalahan. Untuk memastikan AI bekerja secara etis, sistem kami dirancang untuk tidak pernah memberikan vonis mutlak. Sebagai contoh, jika sistem menemukan kemiripan tinggi, aplikasi tidak akan mengeluarkan peringatan kasar seperti "Anda terdeteksi melakukan plagiarisme!". Sebaliknya, pesan yang ditampilkan dibuat netral dan bertanggung jawab, seperti Ditemukan indikasi kemiripan sebesar X% dengan sumber berikut. Kami menegaskan di dalam aplikasi bahwa AI hanya bertugas sebagai asisten pembanding teks, sementara keputusan akhir mengenai ada atau tidaknya unsur plagiat tetap berada di tangan manusia (mahasiswa atau pengguna itu sendiri).

**5. Data pribadi sensitive (PII) apa saja yang dikumpulkan oleh aplikasimu? Bagaimana cara kamu melindungi data tersebut agar tidak bocor atau disalahgunakan? Bagaimana aplikasi meminimalkan Risiko pengguna menjadi korban penipuan siber di platform mu?**

**Pengumpulan dan Perlindungan Data Pribadi (PII):**

Aplikasi AntiKopas menerapkan prinsip minimalisasi data. Kami hanya mengumpulkan informasi yang benar-benar esensial untuk operasional sistem, yaitu alamat email (untuk verifikasi akun) dan file dokumen karya tulis yang diunggah oleh pengguna. Kami sama sekali tidak meminta data sensitif yang tidak relevan seperti nomor telepon, NIK, atau informasi finansial. Untuk mencegah kebocoran atau penyalahgunaan data tersebut, sistem kami menerapkan pembatasan hak akses yang ketat berbasis autentikasi. Artinya, dokumen karya tulis yang diunggah akan dikunci dan hanya bisa dilihat atau dikelola oleh akun pemiliknya. Selain itu, jalur pengiriman data dari browser mahasiswa ke server kami diamankan menggunakan enkripsi (protokol HTTPS).

**Pencegahan Penipuan Siber (Fraud):**

Sebagai langkah mitigasi agar mahasiswa tidak menjadi korban *phishing* yang mengatasnamakan platform kami, AntiKopas akan menyematkan spanduk peringatan keamanan yang jelas di halaman *dashboard* atau halaman *login*. Pesan tersebut menegaskan bahwa tim resmi AntiKopas tidak akan pernah meminta *password* atau kode verifikasi apa pun melalui email maupun pesan singkat. Melalui penegasan ini, pengguna akan lebih diawasi dan tidak mudah tertipu apabila ada oknum yang mencoba memancing data mereka menggunakan identitas palsu.

**6. Ketika aplikasi mengalami masalah teknis (misalnya kehilangan koneksi internet atau kegagalan memuat data), bagaimana aplikasi mengomunikasikannya kepada pengguna? Tuliskan contoh rancangan pesan error ramah pengguna yang memandu pengguna melakukan troubleshooting mandiri secara mudah.**

**Komunikasi Masalah Teknis ke Pengguna:**

Sesuai dengan prinsip dasar *troubleshooting* di Modul 6, ketika sistem AntiKopas mengalami kegagalan, kami pantang menampilkan kode *error* mentah dari sistem (seperti `Error 500: Internal Server Error` atau `API Timeout`). Bahasa mesin seperti itu hanya akan membuat pengguna awam bingung dan panik. Sebagai gantinya, aplikasi akan menahan halaman agar tidak *crash* dan menggantinya dengan tampilan pesan yang ramah. Pesan ini difokuskan pada dua hal: memberi tahu apa yang salah dengan bahasa sehari-hari, dan memberikan langkah mandiri apa yang bisa pengguna lakukan saat itu juga.

**Contoh Rancangan Pesan Error yang Ramah Pengguna:**

- **Skenario 1: Jika koneksi internet terputus atau sistem gagal memuat dari OpenAlex:**

  > **"Koneksi Terputus"**
  >
  > *"Sistem kami kesulitan terhubung ke pangkalan data literatur saat ini. Yuk, pastikan lagi sambungan WiFi atau kuota internet kamu berjalan lancar. Kalau sudah stabil, silakan klik tombol **'Muat Ulang Pengecekan'** di bawah ini."*

- **Skenario 2: Jika file dokumen gagal dibaca oleh sistem ekstraksi teks:**

  > **"Gagal Membaca Dokumen"**
  >
  > *"Teks di dalam file kamu tidak bisa diproses. Mohon pastikan kembali bahwa dokumen karya tulis kamu disimpan dalam format **.PDF** atau **.DOCX**, dan pastikan file tersebut tidak terkunci oleh *password*. Silakan perbaiki file kamu lalu unggah kembali."*
