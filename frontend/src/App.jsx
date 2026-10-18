import { useEffect, useState } from 'react'
import { api } from './api/client'
import logo from './assets/antikopas-logo.png'
import heroIllustration from './assets/image-transparent.png'
import heroIllustrationOriginal from './assets/image.png'
import './App.css'

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('antikopas_access'))
  const [showLogin, setShowLogin] = useState(false)
  const [login, setLogin] = useState({ username: '', password: '' })
  const [form, setForm] = useState({ title: '', file: null })
  const [analyses, setAnalyses] = useState([])
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (token) {
      loadAnalyses()
    }
  }, [token])

  async function loadAnalyses() {
    try {
      const data = await api.listAnalyses()
      setAnalyses(data.results || [])
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function handleLogin(event) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    try {
      const data = await api.login(login.username, login.password)
      localStorage.setItem('antikopas_access', data.access)
      localStorage.setItem('antikopas_refresh', data.refresh)
      setToken(data.access)
    } catch (error) {
      setMessage(error.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleUpload(event) {
    event.preventDefault()
    if (!form.title.trim() || !form.file) {
      setMessage('Judul dan file wajib diisi.')
      return
    }
    setBusy(true)
    setMessage('Dokumen sedang dianalisis. Proses ini dapat membutuhkan waktu.')
    try {
      const data = await api.detect(form.title, form.file)
      setResult(data)
      setMessage('Analisis selesai.')
      setForm({ title: '', file: null })
      event.target.reset()
      await loadAnalyses()
    } catch (error) {
      setMessage(error.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Hapus riwayat analisis ini?')) return
    try {
      await api.deleteAnalysis(id)
      if (result?.analysis_id === id) setResult(null)
      setMessage('Riwayat berhasil dihapus.')
      await loadAnalyses()
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function handleOpenReport(url) {
    const reportWindow = window.open('', '_blank')
    try {
      const blob = await api.getReport(url)
      const objectUrl = URL.createObjectURL(blob)
      if (reportWindow) reportWindow.location.href = objectUrl
      else window.open(objectUrl, '_blank')
    } catch (error) {
      if (reportWindow) reportWindow.close()
      setMessage(error.message)
    }
  }

  function logout() {
    localStorage.removeItem('antikopas_access')
    localStorage.removeItem('antikopas_refresh')
    setToken(null)
    setResult(null)
  }

  if (!token && !showLogin) {
    return <LandingPage onStart={() => setShowLogin(true)} />
  }

  if (!token) {
    return (
      <main className="auth-shell">
        <section className="auth-visual">
          <div className="auth-visual-brand"><img className="brand-image" src={logo} alt="Logo AntiKopas" /><span>Anti<span>Kopas</span></span></div>
          <img className="auth-visual-art" src={heroIllustrationOriginal} alt="Ilustrasi analisis dokumen" />
          <div className="auth-visual-copy"><h2>Analisis Dokumen<br />Tanpa Ragu</h2><p>Aman, Cepat, dan Akurat.</p></div>
        </section>
        <section className="auth-card">
          <button className="back-link" onClick={() => setShowLogin(false)}>← Kembali ke beranda</button>
          <div className="auth-brand"><img className="brand-image auth-logo" src={logo} alt="Logo AntiKopas" /><span>Anti<span>Kopas</span></span></div>
          <p className="eyebrow">RUANG KERJA AKADEMIK DIGITAL</p>
          <h1>Masuk untuk <em>memeriksa.</em></h1>
          <p className="muted">Masuk untuk memeriksa dokumen dan melihat riwayat laporan.</p>
          <form onSubmit={handleLogin} className="stack-form">
            <label>Username<input value={login.username} onChange={(e) => setLogin({ ...login, username: e.target.value })} /></label>
            <label>Password<input type="password" value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })} /></label>
            <button className="auth-submit" disabled={busy}>{busy ? 'Memproses...' : 'Masuk ke aplikasi'}</button>
          </form>
          {message && <p className="notice error">{message}</p>}
          <p className="auth-footnote">Workspace privat untuk analisis dokumen akademik.</p>
        </section>
      </main>
    )
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><img className="brand-image dashboard-logo" src={logo} alt="Logo AntiKopas" /><strong>AntiKopas</strong></div>
        <div className="topbar-actions"><span className="user-avatar">S</span><button className="button-ghost" onClick={logout}><LineIcon type="logout" /> Keluar</button></div>
      </header>
      <section className="content">
        <div className="intro"><p className="eyebrow">DASHBOARD</p><h1>Periksa dokumen akademik</h1><p className="muted">Unggah file untuk mendapatkan analisis kemiripan dan laporan.</p></div>
        <div className="grid">
          <form className="panel stack-form" onSubmit={handleUpload}>
            <h2><LineIcon type="file" /> Analisis baru</h2>
            <label>Judul dokumen<span className="input-with-icon"><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Contoh: Analisis Kuantitatif Mikrobiologi" /><LineIcon type="pencil" /></span></label>
            <label className="file-input"><span>File dokumen</span><span className="upload-dropzone"><input type="file" accept="application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx" onChange={(e) => setForm({ ...form, file: e.target.files[0] || null })} /><span className="upload-icon"><LineIcon type="upload" /></span><strong>{form.file ? form.file.name : <>Tarik & lepas file di sini, atau <u>Cari file</u></>}</strong><small>Mendukung format PDF & Word (.docx)</small></span></label>
            <button disabled={busy}>{busy ? 'Menganalisis...' : <>Mulai analisis <LineIcon type="search" /></>}</button>
            {busy && <div className="analysis-loading" role="status" aria-live="polite"><div className="loading-heading"><span className="loading-spinner"></span><strong>Sedang menganalisis dokumen</strong></div><p>Dokumen sedang dibaca dan dibandingkan dengan sumber akademik.</p><div className="loading-track"><i></i></div><small>Mohon tunggu, proses ini dapat membutuhkan waktu.</small></div>}
            {message && <p className="notice">{message}</p>}
          </form>
          <section className="panel">
            <div className="panel-heading"><h2><LineIcon type="refresh" /> Riwayat analisis</h2><button className="button-ghost" onClick={loadAnalyses}><LineIcon type="refresh" /> Muat ulang</button></div>
            {analyses.length === 0 ? <div className="empty-history"><div className="empty-icon"><LineIcon type="search" /></div><h3>Belum ada analisis</h3><p>Dokumen yang Anda periksa akan muncul di sini.</p></div> : <div className="history">{analyses.map((item) => <div className="history-item" key={item.id}><div><strong>{item.title}</strong><span>{item.status} · {item.matched_chunks}/{item.total_chunks} chunk cocok</span></div><b>{item.similarity_index.toFixed(2)}%</b><button className="delete-button" onClick={() => handleDelete(item.id)} aria-label={`Hapus ${item.title}`}>Hapus</button></div>)}</div>}
          </section>
        </div>
        {result && <section className="panel result"><div><p className="eyebrow">HASIL TERBARU</p><h2>{result.title}</h2><div className="score">{Number(result.similarity_index).toFixed(2)}<span>%</span></div><p className="muted">{result.matched_chunks} dari {result.total_chunks} segmen cocok</p></div><button className="button" onClick={() => handleOpenReport(result.report_url)}>Buka report PDF</button></section>}
      </section>
    </main>
  )
}

function LineIcon({ type }) {
  const paths = {
    file: <><rect x="6" y="3" width="12" height="18" rx="2" /><path d="M14 3v5h5M9 12h6M9 16h6" /></>,
    refresh: <><path d="M20 11a8 8 0 0 0-14-4L4 9" /><path d="M4 4v5h5M4 13a8 8 0 0 0 14 4l2-2" /><path d="M20 20v-5h-5" /></>,
    upload: <><path d="M12 16V4M7 9l5-5 5 5" /><path d="M5 20h14a2 2 0 0 0 2-2v-2M3 16v2a2 2 0 0 0 2 2" /></>,
    search: <><rect x="5" y="3" width="11" height="17" rx="2" /><path d="M9 8h4M9 12h3" /><circle cx="16.5" cy="16.5" r="3.5" /><path d="m19 19 2 2" /></>,
    pencil: <><path d="m4 16-.7 4.7L8 20l10.8-10.8a2.2 2.2 0 0 0-3.1-3.1L4 16Z" /><path d="m14.5 7.5 3 3" /></>,
    logout: <><path d="M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5M15 16l4-4-4-4M19 12H9" /></>,
    spark: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z" /><path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7L19 16Z" /></>,
    folder: <><path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" /></>,
    lock: <><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v2" /></>,
    chart: <><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M7 17v-4M12 17V8M17 17v-7M6 17h12" /></>,
  }
  return <svg className="line-icon" viewBox="0 0 24 24" aria-hidden="true">{paths[type]}</svg>
}

function LandingPage({ onStart }) {
  return (
    <main className="landing-page">
      <header className="landing-nav">
        <a className="landing-brand" href="#top" aria-label="AntiKopas beranda">
          <img className="brand-image landing-logo" src={logo} alt="Logo AntiKopas" />
          <span>Anti<span>Kopas</span></span>
        </a>
        <nav className="landing-links" aria-label="Navigasi utama">
          <a href="#cara-kerja">Cara kerja</a>
          <a href="#fitur">Keunggulan</a>
          <a href="#keamanan">Keamanan</a>
        </nav>
        <button className="nav-login" onClick={onStart}>Masuk ke aplikasi</button>
      </header>

      <section className="landing-hero" id="top">
        <div className="hero-copy">
          <p className="landing-kicker">RUANG KERJA AKADEMIK DIGITAL</p>
          <h1>Temukan kemiripan.<br /><em>Jaga orisinalitas.</em></h1>
          <p className="hero-description">Analisis dokumen akademik dengan alur yang sederhana, hasil yang transparan, dan laporan yang siap digunakan.</p>
          <div className="hero-actions"><button className="hero-button" onClick={onStart}>Mulai pemeriksaan <span>↗</span></button><a href="#cara-kerja" className="hero-secondary">Lihat cara kerja</a></div>
          <div className="hero-proof"><span className="proof-dot"></span><span>PDF & DOCX</span><span className="proof-divider">•</span><span>Berbasis sumber akademik</span></div>
        </div>
        <div className="hero-art"><img className="hero-illustration" src={heroIllustration} alt="Ilustrasi analisis kemiripan dokumen" /></div>
      </section>

      <section className="trust-strip"><span>Dirancang untuk penulis akademik</span><b>Draft</b><b>Research</b><b>Review</b><b>Report</b></section>

      <section className="landing-section process-section" id="cara-kerja">
        <div className="section-heading"><p className="landing-kicker">ALUR YANG RINGKAS</p><h2>Dari dokumen ke insight<br /><em>dalam tiga langkah.</em></h2></div>
        <div className="process-grid"><div className="process-item"><span className="step-number">01</span><span className="process-icon"><LineIcon type="upload" /></span><h3>Unggah dokumen</h3><p>Masukkan file PDF atau DOCX dan beri judul agar pemeriksaan mudah dilacak.</p></div><div className="process-item"><span className="step-number">02</span><span className="process-icon"><LineIcon type="search" /></span><h3>Mesin menganalisis</h3><p>Mesin AI membaca segmen dokumen dan membandingkannya dengan sumber akademik.</p></div><div className="process-item"><span className="step-number">03</span><span className="process-icon"><LineIcon type="chart" /></span><h3>Pahami hasilnya</h3><p>Lihat indeks kemiripan, bukti sumber, riwayat, dan unduh laporan PDF.</p></div></div>
      </section>

      <section className="landing-section feature-section" id="fitur">
        <div className="feature-intro"><p className="landing-kicker">DIBUAT UNTUK KERJA YANG SERIUS</p><h2>Lebih dari sekadar<br /><em>angka persentase.</em></h2><div className="feature-visual"><div className="source-tag">Source match <i></i><i></i></div><div className="report-sheet"><b></b><b></b><b></b><i></i><i></i><i></i></div><div className="match-tag">Dokumen <strong>24%</strong></div></div></div>
        <div className="feature-list"><article><span><LineIcon type="spark" /></span><div><h3>Evidence-first</h3><p>Hasil dilengkapi potongan sumber agar angka dapat dipahami dan ditinjau.</p></div></article><article><span><LineIcon type="folder" /></span><div><h3>Rapi sejak awal</h3><p>Riwayat analisis tersimpan teratur dan report dapat dibuka kembali.</p></div></article><article id="keamanan"><span><LineIcon type="lock" /></span><div><h3>Workspace privat</h3><p>Akses dibatasi akun pengguna dan dokumen tidak masuk repository publik.</p></div></article></div>
      </section>

      <section className="landing-cta"><div className="cta-deco cta-doc"><div><LineIcon type="file" /><LineIcon type="lock" /></div></div><div className="cta-content"><p className="landing-kicker">SIAP MEMULAI?</p><h2>Jadikan pemeriksaan akademik<br /><em>lebih tenang dan terukur.</em></h2><button className="hero-button" onClick={onStart}>Masuk ke workspace <span>↗</span></button></div><div className="cta-deco cta-chart"><LineIcon type="chart" /></div></section>
      <footer className="landing-footer"><strong>AntiKopas</strong><span>Academic similarity workspace</span><span>© 2026</span></footer>
    </main>
  )
}

export default App
