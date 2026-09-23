# Interconnecting between Digital Awareness and Application Design

## BAGIAN 1. Identitas dan Topik Proyek Aplikasi

**Nama Aplikasi:** AntiKopas

**Deskripsi Singkat dan Tujuan:**
Antikopas adalah aplikasi yang dibuat untuk membantu memeriksa tingkat kemiripan karya tulisan ilmiah dengan menggunakan sumber literatur terbuka yang sudah terpublikasi. Didalam aplikasi ini pengguna cukup mengupload dokumen dengan format PDF/DOXC, dan Teks untuk mengecek. Lalu sistem akan memproses dan membandingkan karya tulis dengan sumber-sumber yang sesuai. Untuk masalah yang ingin kami selesaikan adalah sulitnya mahasiswa untuk mengecek sendiri hasil tulisan karya ilmiahnya, dan untuk mengecek harus membayar kepada orang yang memiliki akses. Mengingat proses yang sangat sulit dan juga menghabiskan uang yang lumayan hanya untuk sekedar mengecek kemiripan karya tulis ilmiah, disinilah kami ingin membuat aplikasi Antikopas ini. Dengan Antikopas, pengguna bisa mengecek hasil tulisan karya ilmiahnya dan mendapat gambaran awal bagian mana dari tulisannya yang perlu di cek ulang atau di ubah/parafrase, dan tentunya gratis.

**Target Pengguna Utama:**
Mahasiswa sebagai target utama.

## BAGIAN 2. Resume Modul Digital Awareness

1. **Modul 1: There's a whole new world out there!**
Dimodul pertama ini membahas tentang perkembangan teknologi yang membuat pekerjaan manusia menjadi lebih mudah. Yang sebelumnya dilakukan secara manual sekarang sudah banyak yang berubah menjadi digital. Dengan adanya teknologi digital, banyak pekerjaan bisa dilakukan dengan lebih cepat dan praktis, sehingga manusia ngga perlu melakukan semuanya secara manual seperti zaman dulu.

2. **Modul 2: You'll Need Some Basic Tools**
Dimodul kedua ini akan membahas tentang dasar-dasar penggunaan perangkat dan teknologi. Didalamnya dijelaskan mengenai perangkat yang digunakan, sistem operasi, dan gimana cara mengatur file dan folder biar lebih mudah untuk digunakan. Dan juga, modul ini menjelaskan pentingnya menggunakan password yang kuat untuk menjaga keamanan akun agar tidak mudah diakses oleh orang lain.

3. **Modul 3: This is how you get around and find what you're looking for**
Pada modul ketiga membahas tentang gimana caranya mencari informasi menggunakan teknologi digital. Salah satunya menggunakan browser untuk mencari informasi di internet, selain itu juga terdapat cara untuk mencari file yang tersimpan didalam perangkat. Modul ini juga membahas mengenai copyright dan public domain, sehingga pengguna harus mengetahui apakah suatu informasi atau bahan yang ditemukan di internet boleh digunakan secara bebas atau masih memiliki hak cipta.

4. **Modul 4: It just keeps getting better**
Dimodul keempat ini membahas tentang perkembangan teknologi terutama AI yang makin berkembang dan banyak digunakan dalam kehidupan sehari-hari. Selain perkembangan AI, modul ini membahas juga mengenai etika dalam menggunakan internet. Pengguna teknologi harus tetap memiliki tanggung jawab dalam menggunakan teknologi dan tidak boleh menggunakan teknologi secara sembarangan yang dapat merugikan orang lain.

5. **Modul 5: Even Though It's Digital, It is Real, With Real Consequences**
Pada modul kelima membahas tentang data pribadi dan dampak dari aktivitas yang dilakukan didunia digital. Data pribadi seperti informasi yang bersifat sensitif harus dijaga agar tidak disalahgunakan oleh orang lain. Selain itu, aktivitas yang dilakukan di internet juga dapat meninggalkan jejak digital yang sulit untuk dihilangkan. Modul ini juga membahas mengenai komunikasi yang negatif, penipuan, dan pembajakan yang harus dihindari saat menggunakan teknologi digital.

6. **Modul 6: Learn About Anything and Everything**
Pada modul keenam akan membahas tentang bagaimana cara menghadapi masalah yang terjadi pada perangkat atau teknologi dengan melakukan troubleshooting. Pengguna harus bisa mengenali masalah yang terjadi dan mencoba mencari solusi dasar sebelum meminta bantuan orang lain. Selain itu, modul ini juga membahas tentang skills gap, yaitu kesenjangan kemampuan yang dimiliki seseorang dalam menggunakan teknologi. Karena teknologi terus berkembang, pengguna juga harus terus belajar agar kemampuan digitalnya tidak tertinggal.

## BAGIAN 3. Hubungan dan Implementasi pada Topik Proyek

### 1. Bagaimana rancangan aplikasi dapat mempermudah tugas sehari-hari pengguna? Apa proses "analog/tradisional" dari topik proyekmu yang berhasil disederhanakan menjadi digital.

AntiKopas dapat membantu mahasiswa dalam melakukan pengecekan kemiripan karya tulis ilmiah. Sebelum adanya aplikasi ini, mahasiswa harus membaca kembali tulisan yang dibuat lalu mencari dan membandingkannya dengan berbagai sumber secara manual atau menyewa jasa pengecekan berbayar. Hal tersebut tentunya membutuhkan waktu yang cukup lama dan menguras dompet. Dengan adanya AntiKopas, pengguna cukup mengupload dokumen atau memasukkan teks, kemudian sistem akan membantu memproses dan membandingkan tulisan dengan sumber literatur yang sesuai. Jadi pengguna tidak perlu melakukan semua pengecekan secara manual dan tidak perlu mengeluarkan uang, sehingga bisa lebih mudah mengetahui bagian tulisan yang perlu diperiksa kembali.

### 2. Jika aplikasimu memiliki fitur penyimpanan file atau pendaftaran akun, bagaimana kamu merancang struktur penyimpanan file yang intuitif bagi pengguna awam? Bagaimana kamu membantu pengguna membuat kata sandi yang aman?

Untuk penyimpanan file, aplikasi ini ngga menyimpan dokumen pengguna secara permanen di server. Konsep aplikasi yang kami buat kurang lebih seperti layanan pengolahan dokumen online contohnya ilovepdf, dimana pengguna cukup mengupload dokumen atau memasukkan teks, kemudian file tersebut diproses oleh sistem untuk melakukan pengecekan. Setelah proses selesai, hasil pengecekan akan langsung ditampilkan kepada pengguna dan pengguna dapat mendownload hasil tersebut jika diperlukan. File yang digunakan untuk proses pengecekan tidak disimpan secara permanen di server. Kami memilih cara ini karena jika setiap dokumen dan hasil pengecekan disimpan, kapasitas penyimpanan server akan semakin cepat penuh dan dapat menambah beban server, terutama jika jumlah pengguna dan dokumen yang diperiksa semakin banyak. Dengan tidak menyimpan file secara permanen, kapasitas server dapat digunakan lebih efisien dan data pengguna yang tersimpan juga lebih sedikit.

Untuk keamanan password, pengguna akan diberikan aturan tertentu ketika membuat akun, seperti menggunakan password dengan jumlah karakter yang cukup misal minimal 8 karakter serta kombinasi huruf, angka dan simbol. Password yang digunakan pengguna tidak disimpan dalam bentuk teks biasa, tetapi menggunakan proses enkripsi. Dengan begitu, password asli pengguna tidak dapat langsung dilihat dari database apabila terjadi kebocoran data. Selain itu, pengguna juga hanya dapat mengakses akun miliknya sendiri.

### 3. Bagaimana kamu mendesain fitur pencarian (search bar) di dalam aplikasi agar pengguna dapat mencari informasi dengan mudah? Selain itu, sebutkan asset eksternal yang digunakan dalam aplikasi (library, API, gambar, icon). Apakah asset-aset tersebut berlisensi open-source, public domain, atau memiliki hak cipta khusus yang wajib dicantumkan?

Fitur pencarian pada aplikasi dibuat sederhana agar mudah digunakan oleh pengguna. Pengguna cukup memasukkan judul atau kata kunci yang berhubungan dengan karya tulis yang ingin diperiksa dan juga filenya. Setelah itu sistem akan menggunakan kata kunci tersebut untuk mencari sumber literatur yang sesuai melalui API OpenAlex. Dengan begitu pengguna tidak perlu mencari sumber satu per satu secara manual.

Beberapa asset eksternal yang digunakan dalam pengembangan aplikasi yaitu:
- **OpenAlex API**, digunakan untuk mencari dan mengambil informasi dari literatur ilmiah, seperti judul, tahun publikasi, DOI, dan informasi sumber lainnya.
- **Python requests**, digunakan untuk menghubungkan aplikasi dengan OpenAlex API sehingga aplikasi dapat mengirim permintaan dan menerima data dari API tersebut.
- **Python sentence-transformers**, digunakan untuk menjalankan model Sentence Transformer yang berfungsi mengubah teks menjadi bentuk angka atau embedding agar dapat dibandingkan oleh sistem.
- **Model paraphrase-multilingual-MiniLM-L12-v2**, digunakan untuk menghasilkan embedding dari teks sehingga sistem dapat membandingkan kemiripan makna antara tulisan mahasiswa dengan teks yang berasal dari literatur.
- **Library ekstraksi teks dokumen**, digunakan untuk mengambil isi teks dari file seperti PDF dan DOCX sebelum teks tersebut diproses lebih lanjut oleh sistem.

Dalam penggunaan asset eksternal, aplikasi ini tetap memperhatikan lisensi dan aturan penggunaan dari masing-masing komponen yang digunakan. Untuk sumber literatur, pencarian juga disesuaikan dengan ruang lingkup proyek, yaitu menggunakan sumber yang dapat diakses secara terbuka.

### 4. Jika aplikasimu memiliki fitur interaksi social, bagaimana kamu mencegah pelanggaran etika digital di dalamnya? Jika aplikasi menggunakan fitur pintar berbasis AI, bagaimana kamu memastikan AI tersebut bekerja secara etis dan bertanggung jawab bagi pengguna?

Aplikasi ini ngga memiliki fitur interaksi sosial seperti chat atau komentar antar pengguna, jadi kemungkinan terjadinya masalah seperti penghinaan atau pembulyan melalui fitur tersebut dapat dikurangi. Pada aplikasi ini, AI digunakan untuk membantu mengetahui tingkat kemiripan tulisan. Hasil dari AI tidak langsung dianggap sebagai bukti bahwa seseorang melakukan plagiarisme, pengguna perlu mengecek kembali hasil, karena AI memiliki kekurangan. Hasil yang diberikan hanya menjadi gambaran awal mengenai bagian tulisan yang memiliki kemiripan dengan sumber lain.

### 5. Data pribadi sensitive (PII) apa saja yang dikumpulkan oleh aplikasimu? Bagaimana cara kamu melindungi data tersebut agar tidak bocor atau disalahgunakan? Bagaimana aplikasi meminimalkan Risiko pengguna menjadi korban penipuan siber di platform mu?

Data yang dikumpulkan oleh aplikasi yang akan dirancang hanya data yang diperlukan untuk menjalankan aplikasi, seperti username, email, dan dokumen karya tulis yang diupload untuk dilakukan pemeriksaan. Aplikasi tidak perlu meminta data pribadi lain yang tidak berhubungan dengan fungsi aplikasi seperti nomor identitas atau informasi keuangan. Untuk melindungi data pengguna, aplikasi menerapkan autentikasi dan pembatasan akses pada fitur yang membutuhkan akun. Untuk mengurangi risiko penipuan, aplikasi juga harus memberikan informasi yang jelas mengenai komunikasi resmi dari AntiKopas. Misalnya, pengguna diberitahu bahwa aplikasi tidak akan pernah meminta password melalui email atau pesan. Dengan begitu pengguna dapat lebih mudah mengenali apabila ada pihak lain yang mencoba mengatasnamakan AntiKopas.

### 6. Ketika aplikasi mengalami masalah teknis (misalnya kehilangan koneksi internet atau kegagalan memuat data), bagaimana aplikasi mengomunikasikannya kepada pengguna? Tuliskan contoh rancangan pesan error ramah pengguna yang memandu pengguna melakukan troubleshooting mandiri secara mudah.

Jika terjadi masalah teknis seperti koneksi internet terputus atau server tidak dapat memberikan data yang diminta, aplikasi akan memberikan pesan yang mudah dipahami oleh pengguna. Pesan error tidak hanya menampilkan kode kesalahan, tetapi juga memberikan informasi mengenai masalah yang terjadi dan langkah yang bisa dilakukan oleh pengguna.

Contoh pesan error jika koneksi internet bermasalah:

> *"Pemeriksaan tidak dapat dilanjutkan karena koneksi internet terputus. Silahkan periksa kembali koneksi internet Anda, kemudian tekan tombol 'Coba Lagi' untuk melanjutkan pemeriksaan."*

Contoh pesan jika dokumen gagal dimuat:

> *"Dokumen gagal dimuat. Pastikan file yang diupload menggunakan format PDF atau DOCX dan ukuran file tidak lebih dari 10 MB. Setelah itu silahkan coba upload kembali."*

Dengan cara tersebut, pengguna bisa mencoba menyelesaikan masalah sederhana secara mandiri tanpa harus langsung meminta bantuan kepada tim pengembang.
