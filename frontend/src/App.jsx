import { useCallback, useEffect, useState } from 'react'
import { api } from './api/client'
import logo from './assets/antikopas-logo.png'
import heroIllustration from './assets/image-transparent.png'
import heroIllustrationOriginal from './assets/image.png'
import gambar1 from './assets/gambar1.jpg'
import gambar2 from './assets/gambar2.jpg'
import gambar3 from './assets/gambar3.jpg'
import './App.css'

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('antikopas_access'))
  const [currentUser, setCurrentUser] = useState(null)
  const [identityError, setIdentityError] = useState('')
  const [showLogin, setShowLogin] = useState(false)
  const [showRegister, setShowRegister] = useState(false)
  const [login, setLogin] = useState({ username: '', password: '' })
  const [registration, setRegistration] = useState({ username: '', password: '', passwordConfirm: '' })
  const [form, setForm] = useState({ title: '', file: null })
  const [analyses, setAnalyses] = useState([])
  const [historyMeta, setHistoryMeta] = useState({ page: 1, totalPages: 1, count: 0 })
  const [historyQuery, setHistoryQuery] = useState('')
  const [historyStatus, setHistoryStatus] = useState('')
  const [stats, setStats] = useState(null)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  
  // Popup ketika pencarian jurnal OpenAlex gagal.
  // Tidak mengubah backend, model AI, atau logika scan.
  useEffect(() => {
    if (!token || busy) return

    const errorText = String(message || '').toLowerCase()

    const literatureFailed =
      errorText.includes('pencarian openalex gagal') ||
      errorText.includes('openalex tidak tersedia')

    if (!literatureFailed) return

    const style = document.createElement('style')

    style.textContent = `
      .antikopas-literature-modal {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        margin: 0;
        width: min(420px, calc(100% - 32px));
        max-width: 420px;
        box-sizing: border-box;
        padding: 32px 28px;
        border: 1px solid #f5d9d0;
        border-radius: 22px;
        background: #ffffff;
        box-shadow: 0 24px 70px rgba(20, 27, 64, 0.22);
        text-align: center;
        color: #171d4b;
      }

      .antikopas-literature-modal::backdrop {
        background: rgba(18, 23, 51, 0.52);
        backdrop-filter: blur(4px);
      }

      .antikopas-literature-icon {
        display: grid;
        place-items: center;
        width: 62px;
        height: 62px;
        margin: 0 auto 18px;
        border-radius: 50%;
        background: #fff0e9;
        color: #e97855;
        font-size: 30px;
        font-weight: 800;
      }

      .antikopas-literature-title {
        margin: 0 0 12px;
        color: #171d4b;
        font-size: 23px;
        line-height: 1.3;
        font-weight: 800;
      }

      .antikopas-literature-description {
        margin: 0;
        color: #626c85;
        font-size: 14px;
        line-height: 1.7;
      }

      .antikopas-literature-retry,
      .antikopas-literature-close {
        display: block;
        width: 100%;
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 15px;
        font-weight: 700;
        cursor: pointer;
      }

      .antikopas-literature-retry {
        margin-top: 26px;
        background: #e97855;
        color: white;
        border: none;
      }

      .antikopas-literature-retry:hover {
        background: #d96544;
      }

      .antikopas-literature-close {
        margin-top: 10px;
        background: #ffffff;
        color: #171d4b;
        border: 1px solid #e6e7ef;
      }

      .antikopas-literature-close:hover {
        background: #f7f8fc;
      }
    `

    document.head.appendChild(style)

    const dialog = document.createElement('dialog')
    dialog.className = 'antikopas-literature-modal'
    dialog.setAttribute(
      'aria-labelledby',
      'antikopas-literature-title'
    )

    // Konten bersifat statis, tanpa HTML dari server.
    dialog.innerHTML = `
      <div class="antikopas-literature-icon">!</div>

      <h2
        id="antikopas-literature-title"
        class="antikopas-literature-title"
      >
        Koneksi Literatur Gagal
      </h2>

      <p class="antikopas-literature-description">
        Sistem belum berhasil mengambil seluruh sumber
        akademik dari OpenAlex.
        Analisis dibatalkan agar hasil kemiripan
        tidak menyesatkan.
        Silakan coba lagi.
      </p>

      <button
        type="button"
        class="antikopas-literature-retry"
      >
        Coba Lagi
      </button>

      <button
        type="button"
        class="antikopas-literature-close"
      >
        Tutup
      </button>
    `

    document.body.appendChild(dialog)

    const retryButton = dialog.querySelector(
      '.antikopas-literature-retry'
    )

    const closeButton = dialog.querySelector(
      '.antikopas-literature-close'
    )

    function closeLiteratureModal() {
      if (dialog.open) dialog.close()
      setMessage('')
    }

    function retryLiteratureScan() {
      // Ambil form upload yang sudah ada di dashboard.
      const uploadForm = document.querySelector(
        'form.dashboard-reference-upload'
      )

      closeLiteratureModal()

      // Menjalankan ulang fungsi handleUpload yang asli
      // melalui submit form, tanpa menyalin kode scan.
      if (uploadForm && !busy) {
        uploadForm.requestSubmit()
      }
    }

    function handleEscape(event) {
      event.preventDefault()
      closeLiteratureModal()
    }

    retryButton.addEventListener(
      'click',
      retryLiteratureScan
    )

    closeButton.addEventListener(
      'click',
      closeLiteratureModal
    )

    dialog.addEventListener(
      'cancel',
      handleEscape
    )

    dialog.showModal()

    return () => {
      retryButton.removeEventListener(
        'click',
        retryLiteratureScan
      )

      closeButton.removeEventListener(
        'click',
        closeLiteratureModal
      )

      dialog.removeEventListener(
        'cancel',
        handleEscape
      )

      if (dialog.open) dialog.close()

      dialog.remove()
      style.remove()
    }
  }, [message, token, busy])

  // Modal custom ketika sesi login telah berakhir.
  useEffect(() => {
    if (!token) return

    const sessionExpired =
      message === 'Request gagal (401)' ||
      message === 'Report gagal dibuka (401)'

    if (!sessionExpired) return

    // Styling modal khusus AntiKopas.
    const style = document.createElement('style')
    style.textContent = `
      .antikopas-session-modal {
        width: min(420px, calc(100% - 32px));
        max-width: 420px;
        box-sizing: border-box;
        padding: 32px 28px;
        border: 1px solid #f5d9d0;
        border-radius: 22px;
        background: #ffffff;
        box-shadow: 0 24px 70px rgba(20, 27, 64, 0.22);
        text-align: center;
        color: #171d4b;
        position: fixed;
        inset: 0;
        margin: auto;
      }

      .antikopas-session-modal::backdrop {
        background: rgba(18, 23, 51, 0.52);
        backdrop-filter: blur(4px);
      }

      .antikopas-session-icon {
        display: grid;
        place-items: center;
        width: 62px;
        height: 62px;
        margin: 0 auto 18px;
        border-radius: 50%;
        background: #fff0e9;
        color: #e97855;
        font-size: 30px;
        font-weight: 800;
      }

      .antikopas-session-title {
        margin: 0 0 12px;
        font-size: 23px;
        line-height: 1.3;
        font-weight: 800;
        color: #171d4b;
      }

      .antikopas-session-description {
        margin: 0;
        color: #626c85;
        font-size: 14px;
        line-height: 1.7;
      }

      .antikopas-session-button {
        display: block;
        width: 100%;
        margin-top: 26px;
        padding: 14px 20px;
        background: #e97855;
        color: #ffffff;
        border: none;
        border-radius: 12px;
        font-size: 15px;
        font-weight: 700;
        cursor: pointer;
      }

      .antikopas-session-button:hover {
        background: #d96544;
      }
    `

    document.head.appendChild(style)

    // Membuat dialog tanpa mengubah struktur App.jsx.
    const dialog = document.createElement('dialog')
    dialog.className = 'antikopas-session-modal'

    const icon = document.createElement('div')
    icon.className = 'antikopas-session-icon'
    icon.textContent = '!'

    const title = document.createElement('h2')
    title.className = 'antikopas-session-title'
    title.textContent = 'Sesi Anda Telah Berakhir'

    const description = document.createElement('p')
    description.className = 'antikopas-session-description'
    description.textContent =
      'Silakan login kembali untuk melanjutkan menggunakan AntiKopas.'

    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'antikopas-session-button'
    button.textContent = 'OK, Login Kembali'

    dialog.append(icon, title, description, button)
    document.body.appendChild(dialog)

    // Menjaga agar dialog tidak tertutup sebelum konfirmasi.
    const preventClose = (event) => event.preventDefault()
    dialog.addEventListener('cancel', preventClose)

    button.addEventListener('click', () => {
      localStorage.removeItem('antikopas_access')
      localStorage.removeItem('antikopas_refresh')

      dialog.close()

      setToken(null)
      setCurrentUser(null)
      setIdentityError('')
      setShowLogin(true)
      setShowRegister(false)
      setResult(null)
      setAnalyses([])
      setStats(null)
      setMessage('')
    })

    dialog.showModal()

    return () => {
      if (dialog.open) dialog.close()
      dialog.remove()
      style.remove()
    }
  }, [message, token])


  const loadAnalyses = useCallback(async () => {
    try {
      const data = await api.listAnalyses({ page: historyMeta.page, query: historyQuery, status: historyStatus })
      setAnalyses(data.results || [])
      setHistoryMeta({ page: data.page || 1, totalPages: data.total_pages || 1, count: data.count || 0 })
    } catch (error) {
      setMessage(error.message)
    }
  }, [historyMeta.page, historyQuery, historyStatus])

  const loadStats = useCallback(async () => {
    try {
      setStats(await api.getStats())
    } catch (error) {
      setMessage(error.message)
    }
  }, [])

  // Periksa identitas pengguna melalui API setelah login atau saat sesi dipulihkan.
  useEffect(() => {
    if (!token) return

    let cancelled = false

    async function loadCurrentUser() {
      try {
        const data = await api.getCurrentUser()
        if (!data.user || !['user', 'admin'].includes(data.user.role)) {
          throw new Error('Role akun tidak dikenali.')
        }
        if (!cancelled) {
          setCurrentUser(data.user)
          setIdentityError('')
        }
      } catch (error) {
        if (!cancelled) {
          setCurrentUser(null)
          setIdentityError(error.message)
          setMessage(error.message)
        }
      }
    }

    loadCurrentUser()

    return () => {
      cancelled = true
    }
  }, [token])

  useEffect(() => {
    if (!token || currentUser?.role !== 'user') return
    const initialLoad = window.setTimeout(() => {
      loadAnalyses()
      loadStats()
    }, 0)
    return () => window.clearTimeout(initialLoad)
  }, [token, currentUser?.role, loadAnalyses, loadStats])

  useEffect(() => {
    if (!token || currentUser?.role !== 'user') return undefined
    const timer = window.setInterval(() => {
      if (analyses.some((item) => item.status === 'pending' || item.status === 'processing')) loadAnalyses()
    }, 3000)
    return () => window.clearInterval(timer)
  }, [token, currentUser?.role, analyses, loadAnalyses])

  async function handleLogin(event) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    try {
      const data = await api.login(login.username, login.password)
      localStorage.setItem('antikopas_access', data.access)
      localStorage.setItem('antikopas_refresh', data.refresh)
      setCurrentUser(null)
      setIdentityError('')
      setToken(data.access)
    } catch (error) {
      setMessage(error.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleRegister(event) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    try {
      await api.register(registration.username, registration.password, registration.passwordConfirm)
      setLogin({ username: registration.username, password: '' })
      setRegistration({ username: '', password: '', passwordConfirm: '' })
      setShowRegister(false)
      setMessage('Akun berhasil dibuat. Silakan masuk.')
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
    const allowedExtensions = ['.pdf', '.docx']
    const fileName = form.file.name.toLowerCase()
    if (!allowedExtensions.some((extension) => fileName.endsWith(extension))) {
      setMessage('Format file tidak didukung. Gunakan PDF atau DOCX.')
      return
    }
    if (form.file.size > 25 * 1024 * 1024) {
      setMessage('Ukuran file terlalu besar. Maksimal ukuran file adalah 25 MB.')
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
      await loadStats()
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function handleRename(item) {
    const title = window.prompt('Masukkan judul baru:', item.title)
    if (title === null || !title.trim() || title.trim() === item.title) return
    try {
      await api.updateAnalysis(item.id, title.trim())
      setMessage('Judul analisis berhasil diperbarui.')
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
    setCurrentUser(null)
    setIdentityError('')
    setToken(null)
    setResult(null)
    setAnalyses([])
    setStats(null)
    setMessage('')
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
          <h1>{showRegister ? <>Buat akun <em>baru.</em></> : <>Masuk untuk <em>memeriksa.</em></>}</h1>
          <p className="muted">{showRegister ? 'Daftar untuk menyimpan analisis dan laporan Anda.' : 'Masuk untuk memeriksa dokumen dan melihat riwayat laporan.'}</p>
          {showRegister ? <form onSubmit={handleRegister} className="stack-form">
            <label>Username<input required value={registration.username} onChange={(e) => setRegistration({ ...registration, username: e.target.value })} /></label>
            <label>Password<input required type="password" value={registration.password} onChange={(e) => setRegistration({ ...registration, password: e.target.value })} /></label>
            <label>Konfirmasi password<input required type="password" value={registration.passwordConfirm} onChange={(e) => setRegistration({ ...registration, passwordConfirm: e.target.value })} /></label>
            <button className="auth-submit" disabled={busy}>{busy ? 'Memproses...' : 'Daftar akun'}</button>
            <button type="button" className="auth-switch" onClick={() => { setShowRegister(false); setMessage('') }}>Sudah punya akun? Masuk</button>
          </form> : <form onSubmit={handleLogin} className="stack-form">
            <label>Username<input required value={login.username} onChange={(e) => setLogin({ ...login, username: e.target.value })} /></label>
            <label>Password<input required type="password" value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })} /></label>
            <button className="auth-submit" disabled={busy}>{busy ? 'Memproses...' : 'Masuk ke aplikasi'}</button>
            <button type="button" className="auth-switch" onClick={() => { setShowRegister(true); setMessage('') }}>Belum punya akun? Daftar</button>
          </form>}
          {message && <p className="notice error">{message}</p>}
          <p className="auth-footnote">Workspace privat untuk analisis dokumen akademik.</p>
        </section>
      </main>
    )
  }

  // Jangan tampilkan dashboard apa pun sebelum role berhasil diverifikasi.
  if (!currentUser) {
    return (
      <main className="auth-shell" style={{ display: 'grid', gridTemplateColumns: '1fr', placeItems: 'center' }}>
        <section className="auth-card" style={{ width: 'min(540px, calc(100% - 32px))' }} aria-live="polite">
          <div className="auth-brand"><img className="brand-image auth-logo" src={logo} alt="Logo AntiKopas" /><span>Anti<span>Kopas</span></span></div>
          <h1>{identityError ? 'Verifikasi akun gagal' : 'Memeriksa akun...'}</h1>
          <p className="muted">{identityError ? 'Identitas akun belum berhasil diverifikasi. Coba lagi atau masuk kembali.' : 'Mohon tunggu, kami sedang memeriksa hak akses akun Anda.'}</p>
          {identityError && (
            <>
              <p className="notice error">{identityError}</p>
              <button className="auth-submit" onClick={() => window.location.reload()}>Coba lagi</button>
              <button className="auth-switch" onClick={logout}>Keluar</button>
            </>
          )}
        </section>
      </main>
    )
  }

  // Administrator menggunakan dashboard pengelolaan, bukan workspace analisis user.
  if (currentUser.role === 'admin') {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'
    const adminUrl = new URL('/admin/', new URL(apiUrl, window.location.origin)).href

    return (
      <main className="dashboard-reference">
        <nav className="dashboard-reference-nav">
          <div className="dashboard-reference-actions">
            <span className="dashboard-reference-avatar" aria-label={`Akun ${currentUser.username}`}>{currentUser.username.charAt(0).toUpperCase()}</span>
            <button className="dashboard-reference-logout" onClick={logout}><LineIcon type="logout" /> Keluar</button>
          </div>
        </nav>

        <section className="dashboard-reference-main">
          <div className="dashboard-reference-intro">
            <span>AREA ADMINISTRATOR</span>
            <h1>Dashboard Pengelolaan AntiKopas</h1>
            <p>Selamat datang, {currentUser.username}. Kelola pengguna, dokumen, hasil analisis, dan laporan melalui panel administrator.</p>
          </div>
          <div className="dashboard-reference-grid">
            <section className="dashboard-reference-card">
              <div className="dashboard-reference-card-heading"><h2>Panel administrator</h2><LineIcon type="lock" /></div>
              <p className="muted">Buka Django Admin untuk mengelola data AntiKopas sesuai hak akses akun.</p>
              <a href={adminUrl} target="_blank" rel="noopener noreferrer" className="hero-button" style={{ display: 'inline-flex', alignItems: 'center', textDecoration: 'none', marginTop: '16px' }}>
                Buka panel administrator <span aria-hidden="true">↗</span>
              </a>
              <p className="muted" style={{ marginTop: '16px' }}>Django Admin menggunakan sesi login sendiri. Jika diminta, masuk kembali menggunakan akun administrator.</p>
            </section>
            <section className="dashboard-reference-card">
              <div className="dashboard-reference-card-heading"><h2>Identitas akun</h2><LineIcon type="lock" /></div>
              <p><strong>Username:</strong> {currentUser.username}</p>
              <p><strong>Role:</strong> Administrator</p>
              <p><strong>Hak akses:</strong> {currentUser.is_superuser ? 'Superuser' : 'Staff'}</p>
              <p className="muted">Hak akses sebenarnya tetap ditentukan dan diperiksa oleh backend Django.</p>
            </section>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="dashboard-reference">
      <nav className="dashboard-reference-nav">
        <div className="dashboard-reference-actions">
          <span className="dashboard-reference-avatar" aria-label={`Akun ${currentUser.username}`}>{currentUser.username.charAt(0).toUpperCase()}</span>
          <button className="dashboard-reference-logout" onClick={logout}><LineIcon type="logout" /> Keluar</button>
        </div>
      </nav>
      <section className="dashboard-reference-main">
        <div className="dashboard-reference-intro">
          <span>Dashboard</span>
          <h1>Periksa dokumen akademik</h1>
          <p>Unggah file untuk mendapatkan analisis kemiripan dan laporan.</p>
        </div>
        <div className="dashboard-reference-grid">
          <form className="dashboard-reference-card dashboard-reference-upload" onSubmit={handleUpload}>
            <div className="dashboard-reference-card-heading"><h2>Analisis baru</h2><LineIcon type="file" /></div>
            <label className="dashboard-reference-label">Judul dokumen
              <span className="dashboard-reference-title-input"><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Contoh: Analisis Kuantitatif Mikrobiologi" /><LineIcon type="pencil" /></span>
            </label>
            <label className="dashboard-reference-label dashboard-reference-file-label">File dokumen
              <span className="dashboard-reference-dropzone">
                <input type="file" accept="application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx" onChange={(e) => setForm({ ...form, file: e.target.files[0] || null })} />
                <span className="dashboard-reference-upload-icon"><LineIcon type="upload" /></span>
                <strong>{form.file ? form.file.name : <>Tarik & lepas file di sini, atau <u>Cari file</u></>}</strong>
                <small>Mendukung format PDF & Word (.docx)</small>
              </span>
            </label>
            <button className="dashboard-reference-submit" disabled={busy}>{busy ? 'Menganalisis...' : <>Mulai analisis <LineIcon type="search" /></>}</button>
            {busy && <div className="analysis-loading" role="status" aria-live="polite"><div className="loading-heading"><span className="loading-spinner"></span><strong>Sedang menganalisis dokumen</strong></div><p>Dokumen sedang dibaca dan dibandingkan dengan sumber akademik.</p><div className="loading-track"><i></i></div><small>Mohon tunggu, proses ini dapat membutuhkan waktu.</small></div>}
            {message && <p className="notice">{message}</p>}
          </form>
          <section className="dashboard-reference-card dashboard-reference-history">
            <div className="dashboard-reference-card-heading"><h2>Riwayat analisis</h2><button className="dashboard-reference-refresh" onClick={() => { loadAnalyses(); loadStats() }}><LineIcon type="refresh" /> Muat ulang</button></div>
            <div className="dashboard-reference-filters"><input value={historyQuery} onChange={(e) => { setHistoryQuery(e.target.value); setHistoryMeta({ ...historyMeta, page: 1 }) }} placeholder="Cari judul analisis..." /><select value={historyStatus} onChange={(e) => { setHistoryStatus(e.target.value); setHistoryMeta({ ...historyMeta, page: 1 }) }}><option value="">Semua status</option><option value="processing">Diproses</option><option value="completed">Selesai</option><option value="failed">Gagal</option></select></div>
            {analyses.length === 0 ? <div className="dashboard-reference-empty"><div className="dashboard-reference-empty-art"><svg width="100" height="100" viewBox="0 0 100 100" fill="none" aria-hidden="true"><rect x="25" y="15" width="45" height="60" rx="4" fill="white" stroke="#1e1b4b" strokeWidth="2.5"/><line x1="35" y1="30" x2="60" y2="30" stroke="#f27a61" strokeWidth="3" strokeLinecap="round"/><line x1="35" y1="40" x2="60" y2="40" stroke="#fbd0c8" strokeWidth="3" strokeLinecap="round"/><line x1="35" y1="50" x2="60" y2="50" stroke="#fbd0c8" strokeWidth="3" strokeLinecap="round"/><line x1="35" y1="60" x2="50" y2="60" stroke="#fbd0c8" strokeWidth="3" strokeLinecap="round"/><circle cx="55" cy="55" r="14" fill="#fcfaf8" stroke="#1e1b4b" strokeWidth="3"/><line x1="65" y1="65" x2="78" y2="78" stroke="#f27a61" strokeWidth="6" strokeLinecap="round"/></svg></div><h3>{historyQuery || historyStatus ? 'Tidak ada hasil' : 'Belum ada analisis.'}</h3><p>{historyQuery || historyStatus ? 'Coba ubah kata kunci atau filter.' : 'Dokumen yang Anda periksa akan muncul di sini.'}</p></div> : <div className="history">{analyses.map((item) => <div className="history-item" key={item.id}><div><strong>{item.title}</strong><span>{item.status} · {item.matched_chunks}/{item.total_chunks} chunk cocok</span></div><b>{item.similarity_index.toFixed(2)}%</b><div className="history-actions"><button className="history-action" onClick={() => handleRename(item)}>Edit</button>{item.report_url && <button className="history-action" onClick={() => handleOpenReport(item.report_url)}>Report</button>}<button className="delete-button" onClick={() => handleDelete(item.id)} aria-label={`Hapus ${item.title}`}>Hapus</button></div></div>)}</div>}
            {historyMeta.totalPages > 1 && <div className="dashboard-reference-pagination"><button disabled={historyMeta.page <= 1} onClick={() => setHistoryMeta({ ...historyMeta, page: historyMeta.page - 1 })}>Sebelumnya</button><span>Halaman {historyMeta.page} dari {historyMeta.totalPages}</span><button disabled={historyMeta.page >= historyMeta.totalPages} onClick={() => setHistoryMeta({ ...historyMeta, page: historyMeta.page + 1 })}>Berikutnya</button></div>}
          </section>
        </div>
        {stats && <section className="dashboard-reference-stats"><div><strong>{stats.total_analyses}</strong><span>Total analisis</span></div><div><strong>{stats.completed_analyses}</strong><span>Selesai</span></div><div><strong>{stats.processing_analyses}</strong><span>Diproses</span></div><div><strong>{Number(stats.average_similarity).toFixed(2)}%</strong><span>Rata-rata kemiripan</span></div></section>}
        {result && <section className="panel result"><div><p className="eyebrow">HASIL TERBARU</p><h2>{result.title}</h2><div className="score">{Number(result.similarity_index).toFixed(2)}<span>%</span></div><p className="muted">{result.matched_chunks} dari {result.total_chunks} segmen cocok</p>{result.diagnostic_message && <p className="notice diagnostic">{result.diagnostic_message}</p>}{result.source_similarities?.length > 0 && <div className="source-summary"><h3>Sumber yang cocok</h3>{result.source_similarities.slice(0, 5).map((source) => <div className="source-summary-item" key={source.openalex_id || source.doi || source.title}><div><strong>{source.title}</strong><span>{source.matched_chunks} segmen · {Number(source.similarity_percentage).toFixed(2)}%</span></div>{source.url && <a href={source.url} target="_blank" rel="noreferrer">Buka sumber</a>}</div>)}</div>}</div><button className="button" onClick={() => handleOpenReport(result.report_url)}>Buka report PDF</button></section>}
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

      <AlurRingkas />

      <section className="landing-section feature-section" id="fitur">
        <div className="feature-intro"><p className="landing-kicker">DIBUAT UNTUK KERJA YANG SERIUS</p><h2>Lebih dari sekadar<br /><em>angka persentase.</em></h2><div className="feature-visual"><div className="source-tag">Source match <i></i><i></i></div><div className="report-sheet"><b></b><b></b><b></b><i></i><i></i><i></i></div><div className="match-tag">Dokumen <strong>24%</strong></div></div></div>
        <div className="feature-list"><article><span><LineIcon type="spark" /></span><div><h3>Evidence-first</h3><p>Hasil dilengkapi potongan sumber agar angka dapat dipahami dan ditinjau.</p></div></article><article><span><LineIcon type="folder" /></span><div><h3>Rapi sejak awal</h3><p>Riwayat analisis tersimpan teratur dan report dapat dibuka kembali.</p></div></article><article id="keamanan"><span><LineIcon type="lock" /></span><div><h3>Workspace privat</h3><p>Akses dibatasi akun pengguna dan dokumen tidak masuk repository publik.</p></div></article></div>
      </section>

      <section className="landing-cta"><div className="cta-deco cta-doc"><div><LineIcon type="file" /><LineIcon type="lock" /></div></div><div className="cta-content"><p className="landing-kicker">SIAP MEMULAI?</p><h2>Jadikan pemeriksaan akademik<br /><em>lebih tenang dan terukur.</em></h2><button className="hero-button" onClick={onStart}>Masuk ke workspace <span>↗</span></button></div><div className="cta-deco cta-chart"><LineIcon type="chart" /></div></section>
      <footer className="landing-footer"><strong>AntiKopas</strong><span>Academic similarity workspace</span><span>© 2026</span></footer>
    </main>
  )
}

function AlurRingkas() {
  const steps = [
    { number: '01', image: gambar1, alt: 'Unggah dokumen', title: 'Unggah dokumen', description: 'Masukkan file PDF atau DOCX dan beri judul agar pemeriksaan mudah dilacak.' },
    { number: '02', image: gambar2, alt: 'Mesin menganalisis', title: 'Mesin menganalisis', description: 'Mesin AI membaca segmen dokumen dan membandingkannya dengan sumber akademik.' },
    { number: '03', image: gambar3, alt: 'Pahami hasilnya', title: 'Pahami hasilnya', description: 'Lihat indeks kemiripan, bukti sumber, riwayat, dan unduh laporan PDF.' },
  ]

  return (
    <section className="alur-ringkas" id="cara-kerja">
      <div className="alur-ringkas-inner">
        <div className="alur-ringkas-header">
          <span>Alur yang ringkas</span>
          <h2>Dari dokumen ke<br /><strong>insight dalam tiga langkah.</strong></h2>
        </div>
        <div className="alur-ringkas-grid">
          <FlowArrow className="alur-arrow-one" curve="down" />
          <FlowArrow className="alur-arrow-two" curve="up" />
          {steps.map((step) => <article className="alur-card" key={step.number}>
            <span className="alur-number">{step.number}</span>
            <div className="alur-image-wrap"><img src={step.image} alt={step.alt} /></div>
            <h3>{step.title}</h3>
            <p>{step.description}</p>
          </article>)}
        </div>
      </div>
    </section>
  )
}

function FlowArrow({ className, curve }) {
  const path = curve === 'down' ? 'M0 10 Q50 20 100 10' : 'M0 10 Q50 0 100 10'
  return <div className={`alur-arrow ${className}`} aria-hidden="true"><svg viewBox="0 0 100 20" fill="none" stroke="#64748b" strokeWidth="1.5" strokeDasharray="4 4"><path d={path} /><polyline points="95,5 100,10 95,15" strokeDasharray="none" /></svg></div>
}

export default App
