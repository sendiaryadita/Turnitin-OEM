# AntiKopas Frontend

Frontend React + Vite untuk aplikasi analisis kemiripan dokumen AntiKopas.

## Menjalankan di komputer lokal

Pastikan backend Django berjalan terlebih dahulu pada `http://127.0.0.1:8000`.

```powershell
npm install
npm run dev
```

Buka alamat yang ditampilkan Vite, biasanya `http://localhost:5173`.

## Konfigurasi API

Salin `.env.example` menjadi `.env` jika alamat backend berbeda:

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

Jangan memasukkan secret atau token ke dalam frontend. Token login disimpan sementara di browser untuk mengakses API.

## Validasi

```powershell
npm run lint
npm run build
```

Fitur utama:

- Login JWT.
- Upload PDF dan DOCX.
- Analisis dokumen melalui API backend.
- Riwayat analisis.
- Penghapusan riwayat.
- Pembukaan report PDF.
