const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'

async function refreshAccessToken() {
  const refresh = localStorage.getItem('antikopas_refresh')
  if (!refresh) return false
  const response = await fetch(`${API_URL}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!response.ok) return false
  const data = await response.json()
  localStorage.setItem('antikopas_access', data.access)
  return true
}

async function request(path, options = {}, canRefresh = true) {
  const response = await fetch(`${API_URL}${path}`, options)
  if (response.status === 401 && canRefresh && await refreshAccessToken()) {
    const headers = {
      ...(options.headers || {}),
      ...authHeaders(),
    }
    return request(path, { ...options, headers }, false)
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = Array.isArray(data.message) ? data.message.join(' ') : data.message
    throw new Error(message || `Request gagal (${response.status})`)
  }
  return data
}

async function downloadReport(url, canRefresh = true) {
  const response = await fetch(url, { headers: authHeaders() })
  if (response.status === 401 && canRefresh && await refreshAccessToken()) {
    return downloadReport(url, false)
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || data.message || `Report gagal dibuka (${response.status})`)
  }
  return response.blob()
}

function authHeaders() {
  const token = localStorage.getItem('antikopas_access')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const api = {
  login: (username, password) => request('/auth/token/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }),
  listAnalyses: () => request('/analyses/', { headers: authHeaders() }),
  deleteAnalysis: (id) => request(`/analyses/${id}/`, { method: 'DELETE', headers: authHeaders() }),
  getReport: (url) => downloadReport(url),
  detect: (title, file) => {
    const body = new FormData()
    body.append('title', title)
    body.append('file', file)
    return request('/detect/', { method: 'POST', headers: authHeaders(), body })
  },
}
