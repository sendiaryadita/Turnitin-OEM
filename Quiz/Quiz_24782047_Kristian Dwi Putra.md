# Quiz Digital Awareness

## 1. Nama Aplikasi
AntiKopas

## 2. Deskripsi Singkat Aplikasi
AntiKopas adalah aplikasi yang dibuat untuk membantu penulis, khususnya
mahasiswa, dalam mengecek tingkat kemiripan karya tulis dengan sumber
literatur yang tersedia. Dengan memanfaatkan teknologi AI, AntiKopas
membantu pengguna menemukan bagian teks yang memiliki kemiripan dengan
sumber literatur lain.

Aplikasi ini menyediakan fitur unggah dokumen (seperti file PDF dan
Word), kemudian sistem akan melakukan analisis terhadap isi dokumen
untuk menemukan teks yang memiliki kesamaan dengan literatur pembanding.

# BAGIAN 2. Resume Modul Digital Awareness

## Modul 1: There's a whole new world out there!
Modul 1 menjelaskan bagaimana teknologi mengubah kehidupan manusia dari
cara aktivitasnya. Sebelum teknologi berkembang banyak pekerjaan
dilakukan secara manual dan membutuhkan waktu lama. Contohnya dulu
mengirim pesan harus menggunakan surat, tetapi sekarang dapat dilakukan
melalui aplikasi seperti WhatsApp. Perkembangan teknologi juga memiliki
dampak seperti masalah privasi data sehingga pengguna harus memahami
teknologi secara bijak.

## Modul 2: You'll Need Some Basic Tools
Modul 2 menjelaskan kegunaan perangkat dan aplikasi yang sering
digunakan dalam aktivitas sehari-hari. Sistem operasi menjadi bagian
penting karena berfungsi sebagai penghubung antara pengguna, aplikasi,
dan perangkat keras seperti Windows, macOS, Linux, serta sistem operasi
lainnya. Modul ini juga menjelaskan pentingnya menjaga keamanan akun
dengan menggunakan kata sandi yang kuat agar akun tidak mudah diretas.

## Modul 3: This is how you get around and find what you're looking for
Modul 3 menjelaskan bahwa mencari informasi di internet tidak hanya
sekadar mengetik kata kunci, tetapi juga perlu mengetahui cara menemukan
sumber terpercaya dan memahami penggunaan informasi agar tidak melanggar
hak cipta.

## Modul 4: It just keeps getting better
Modul 4 membahas bagaimana teknologi memberikan manfaat dan dampak dalam
kehidupan sehari-hari. AI sudah banyak digunakan dalam berbagai bidang
seperti kesehatan, transportasi, pendidikan, hingga layanan digital.
Namun penggunaan AI harus dilakukan secara bijak karena dampaknya
bergantung pada bagaimana manusia menggunakannya.

## Modul 5: Even Though It's Digital, It is Real, With Real Consequences
Modul 5 menjelaskan bahwa dunia digital bukan hanya memberikan
kemudahan, tetapi juga memiliki dampak dan risiko. Setiap aktivitas di
internet dapat meninggalkan jejak digital sehingga pengguna harus bijak
dalam membagikan informasi dan menjaga data pribadi.

## Modul 6: Learn About Anything and Everything
Modul 6 menjelaskan bahwa pengguna perlu terus belajar dan meningkatkan
kemampuan digital. Selain menggunakan teknologi, pengguna juga harus
mampu mencari informasi, memahami masalah, dan menemukan solusi ketika
mengalami kendala.

# BAGIAN 3. Hubungan dan Implementasi pada Topik Proyek

## 1. Bagaimana pengaruh aplikasi yang kamu buat terhadap aktivitas pengguna?
AntiKopas dibuat untuk mempermudah proses pengecekan kemiripan karya
tulis akademik yang sebelumnya masih dilakukan secara manual dan
membutuhkan banyak waktu.

Dengan adanya AntiKopas, proses pengecekan dapat dilakukan secara lebih
praktis dan otomatis. Pengguna cukup mengunggah dokumen seperti PDF atau
Word maupun memasukkan teks secara langsung, kemudian sistem akan
melakukan analisis kemiripan dengan sumber literatur yang tersedia.

## 2. Jika aplikasimu memiliki fitur penyimpanan file atau pendaftaran akun, bagaimana kamu merancang struktur penyimpanan file yang intuitif bagi pengguna awam? Bagaimana kamu membantu pengguna membuat kata sandi yang aman?
Pada aplikasi AntiKopas, file pengguna tidak bakal disimpan secara
permanen di server. Konsepnya seperti i love pdf, yaitu penyimpanan
sementara untuk keperluan pemrosesan. Setelah proses selesai, hasil
analisis dapat dilihat dan diunduh oleh pengguna.

Untuk mengamankan akun, pengguna membuat password yang kuat dengan
minimal 8 karakter serta kombinasi huruf, angka, dan simbol. Password
pengguna tidak disimpan dalam bentuk asli.

## 3. Bagaimana kamu mendesain fitur pencarian (search bar) di dalam aplikasi agar pengguna dapat mencari informasi dengan mudah?
Fitur search-nya dibikin simpel banget biar nggak bikin bingung. Tinggal
ketik judul atau kata kunci karya tulis, terus sistem otomatis nanya ke
API OpenAlex buat nyari literatur pembanding.

AntiKopas menggunakan OpenAlex API, Python requests,
sentence-transformers, model paraphrase-multilingual-MiniLM-L12-v2, dan
library ekstraksi dokumen.

## 4. Jika aplikasimu memiliki fitur interaksi social, bagaimana kamu mencegah pelanggaran etika digital di dalamnya?
AntiKopas tidak memiliki fitur komentar atau chat antar user sehingga
mengurangi risiko cyberbullying. AI hanya digunakan sebagai asisten
pembanding, bukan hakim yang menentukan plagiarisme.

## 5. Data pribadi sensitive (PII) apa saja yang dikumpulkan oleh aplikasimu?
Data pribadi yang diambil dibatasin banget, cuma username, email, dan
dokumen yang lagi dicek. Akses riwayat pengecekan dikunci menggunakan
sistem login atau autentikasi.

## 6. Ketika aplikasi mengalami masalah teknis, bagaimana aplikasi mengomunikasikannya kepada pengguna?
Kalau ada error, aplikasi tidak menampilkan layar blank. Sebaliknya,
muncul notifikasi yang menjelaskan masalah dan solusi praktis.

Contoh: 
- File terlalu besar: ukuran file melebihi batas maksimal. 
- Sesi login habis: pengguna diminta login kembali. 
- Server sibuk: pengguna diminta mencoba kembali. 
- Format file tidak didukung: pengguna diarahkan menggunakan PDF atau DOCX.
