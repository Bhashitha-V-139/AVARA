const API_BASE = 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, options)
  } catch {
    throw new Error('Cannot reach the AVARA backend. Is it running on port 8000?')
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // Keep the generic message if the body isn't JSON.
    }
    const error = new Error(detail)
    error.status = response.status
    throw error
  }

  return response.json()
}

export function getHealth() {
  return request('/health')
}

export function askQuestion(question, sessionId) {
  return request('/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId }),
  })
}

export function listDocuments() {
  return request('/documents')
}

export function uploadDocument(file) {
  const form = new FormData()
  form.append('file', file)
  // No Content-Type header here: the browser sets it, including the file boundary.
  return request('/documents/upload', { method: 'POST', body: form })
}

export function deleteDocument(documentId) {
  return request(`/documents/${documentId}`, { method: 'DELETE' })
}

export function runAgent(text) {
  return request('/agent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request: text }),
  })
}