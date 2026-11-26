import { memo, useEffect, useState } from 'react'
import { api } from '../api/client'

function friendlyAnalysisStage(stage) {
  const value = String(stage || '').trim()
  const normalized = value.toLowerCase()

  if (!value) return 'Sedang memproses dokumen'
  if (normalized.includes('gagal')) return 'Pemeriksaan gagal'
  if (normalized.includes('selesai')) return 'Pemeriksaan selesai'
  if (normalized.includes('sitasi')) return 'Memeriksa sitasi'
  if (normalized.includes('laporan') || normalized.includes('report')) return 'Menyiapkan laporan'
  if (normalized.includes('cross') || normalized.includes('academic') || normalized.includes('validasi')) {
    return 'Memvalidasi kecocokan semantik'
  }
  if (normalized.includes('full text') || normalized.includes('fulltext') || normalized.includes('pdf jurnal')) {
    return 'Memeriksa isi sumber akademik'
  }
  if (['embedding', 'bge', 'membandingkan', 'semantik'].some((term) => normalized.includes(term))) {
    return 'Membandingkan isi dokumen dengan sumber akademik'
  }
  if (['openalex', 'literatur', 'sumber akademik', 'mencari sumber'].some((term) => normalized.includes(term))) {
    return 'Mencari sumber akademik'
  }
  if (['dokumen', 'membaca', 'preprocess', 'persiapan'].some((term) => normalized.includes(term))) {
    return 'Membaca dan menyiapkan dokumen'
  }
  return value
}

const AnalysisProgress = memo(function AnalysisProgress({ active, completed }) {
  const [progress, setProgress] = useState({ percent: 0, stage: 'Mengirim dokumen' })

  useEffect(() => {
    if (!active || completed) return undefined
    let cancelled = false
    let inFlight = false
    let timer

    async function pollProgress() {
      if (cancelled || inFlight || document.visibilityState !== 'visible') return
      inFlight = true
      try {
        const data = await api.listAnalyses({ page: 1, pageSize: 1, status: 'processing' })
        const job = data.results?.[0]
        if (!cancelled && job) {
          const incoming = Number(job.progress_percent)
          const stage = friendlyAnalysisStage(job.progress_stage)
          setProgress((current) => {
            const percent = Number.isFinite(incoming)
              ? Math.max(current.percent, Math.min(incoming, 99))
              : current.percent
            return current.percent === percent && current.stage === stage
              ? current
              : { percent, stage }
          })
        }
      } catch {
        // Request analisis utama tetap menangani kesalahan pemeriksaan.
      } finally {
        inFlight = false
        if (!cancelled) timer = window.setTimeout(pollProgress, 2000)
      }
    }

    function handleVisibility() {
      window.clearTimeout(timer)
      pollProgress()
    }

    pollProgress()
    document.addEventListener('visibilitychange', handleVisibility)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [active, completed])

  const percent = completed ? 100 : progress.percent
  return (
    <div className="analysis-loading" role="status" aria-live="polite">
      <div className="loading-heading">
        <span className="loading-spinner" aria-hidden="true" />
        <strong>{completed ? 'Analisis selesai' : 'Sedang menganalisis dokumen'}</strong>
        <b className="loading-percentage">{percent}%</b>
      </div>
      <p>{completed ? 'Pemeriksaan selesai' : progress.stage}</p>
      <div className="loading-track" role="progressbar" aria-label="Progres analisis" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}>
        <i style={{ transform: `scaleX(${percent / 100})` }} />
      </div>
      <small>{completed ? 'Analisis berhasil diselesaikan.' : 'Progress mengikuti tahapan pemeriksaan yang sedang dikerjakan.'}</small>
    </div>
  )
})

export default AnalysisProgress
