const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status, payload = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  const isJson = response.headers.get('content-type')?.includes('application/json')
  const payload = isJson ? await response.json() : null

  if (!response.ok) {
    throw new ApiError(
      payload?.detail || `Request failed with status ${response.status}.`,
      response.status,
      payload,
    )
  }

  return payload
}

function abortableDelay(milliseconds, signal) {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(resolve, milliseconds)
    signal?.addEventListener('abort', () => {
      window.clearTimeout(timer)
      reject(new DOMException('The request was aborted.', 'AbortError'))
    }, { once: true })
  })
}

export async function generateStudy(text, detailLevel = 'medium', signal, onProgress, image = null) {
  const body = {
    text,
    detail_level: detailLevel,
  }

  if (image) {
    body.image = image
  }

  let job = await request('/api/study/jobs', {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  })
  onProgress?.(job)

  while (job.status !== 'ready') {
    if (job.status === 'error') {
      throw new ApiError(job.error || 'Study generation failed.', 502, job)
    }

    await abortableDelay(500, signal)
    job = await request(`/api/study/jobs/${encodeURIComponent(job.request_id)}`, {
      method: 'GET',
      signal,
    })
    onProgress?.(job)
  }

  return job.result
}

export function printStudy(requestId, signal) {
  return request(`/api/study/${encodeURIComponent(requestId)}/print`, {
    method: 'POST',
    signal,
  })
}

export function listHistory(signal) {
  return request('/api/history', {
    method: 'GET',
    signal,
  })
}

export function printHistory(requestId, signal) {
  return request(`/api/history/${encodeURIComponent(requestId)}/print`, {
    method: 'POST',
    signal,
  })
}

export function createHistoryShare(requestId, signal) {
  return request(`/api/history/${encodeURIComponent(requestId)}/share`, {
    method: 'POST',
    signal,
  })
}

export function printQrShare(shareId, signal) {
  return request(`/api/shares/${encodeURIComponent(shareId)}/print`, {
    method: 'POST',
    signal,
  })
}

export function previewUrl(path) {
  if (!path || /^https?:\/\//i.test(path)) return path
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}
