import { useEffect, useRef, useState } from 'react'
import { deleteDocument, listDocuments, uploadDocument } from './api'

const STATUS_STYLES = {
  indexed: { label: 'Indexed', className: 'bg-emerald-900/60 text-emerald-300' },
  no_text: { label: 'No text found', className: 'bg-amber-900/60 text-amber-300' },
}

function formatSize(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState(null) // { type: 'ok' | 'error', text }
  const fileInput = useRef(null)

  async function refresh() {
    try {
      setDocuments(await listDocuments())
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleUpload(event) {
    const file = event.target.files?.[0]
    event.target.value = '' // lets the same file be chosen again later
    if (!file) return

    setUploading(true)
    setMessage(null)
    try {
      const data = await uploadDocument(file)
      setMessage({ type: 'ok', text: data.message })
      await refresh()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(doc) {
    if (!window.confirm(`Delete "${doc.filename}" and its search index?`)) return

    setMessage(null)
    try {
      await deleteDocument(doc.document_id)
      setMessage({ type: 'ok', text: `Deleted ${doc.filename}.` })
      await refresh()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <section className="rounded-2xl border border-slate-700 bg-slate-800 p-6">
        <h2 className="text-lg font-semibold">Upload a document</h2>
        <p className="mt-1 text-sm text-slate-400">
          PDF files up to 20 MB. Large files can take a minute to index.
        </p>
        <input
          ref={fileInput}
          type="file"
          accept="application/pdf,.pdf"
          onChange={handleUpload}
          className="hidden"
        />
        <button
          onClick={() => fileInput.current?.click()}
          disabled={uploading}
          className="mt-4 rounded-xl bg-violet-600 px-5 py-3 font-medium hover:bg-violet-500 disabled:opacity-40"
        >
          {uploading ? 'Uploading and indexing...' : 'Choose PDF'}
        </button>
      </section>

      {message && (
        <div
          className={`rounded-xl border p-4 text-sm ${
            message.type === 'ok'
              ? 'border-emerald-800 bg-emerald-950/50 text-emerald-300'
              : 'border-red-800 bg-red-950/50 text-red-300'
          }`}
        >
          {message.text}
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Uploaded documents</h2>

        {loading && <p className="text-sm text-slate-400">Loading...</p>}
        {!loading && documents.length === 0 && (
          <p className="text-sm text-slate-400">No documents yet. Upload a PDF to get started.</p>
        )}

        {documents.map((doc) => {
          const status = STATUS_STYLES[doc.status] ?? {
            label: doc.status,
            className: 'bg-slate-700 text-slate-300',
          }
          return (
            <div
              key={doc.document_id}
              className="flex flex-col gap-3 rounded-xl border border-slate-700 bg-slate-800 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <p className="truncate font-medium">{doc.filename}</p>
                <p className="mt-1 text-xs text-slate-400">
                  {doc.page_count} pages · {formatSize(doc.size_bytes)} · uploaded{' '}
                  {new Date(doc.uploaded_at).toLocaleString()}
                </p>
                <span className={`mt-2 inline-block rounded-full px-2 py-0.5 text-xs ${status.className}`}>
                  {status.label}
                </span>
              </div>
              <button
                onClick={() => handleDelete(doc)}
                className="shrink-0 rounded-lg border border-red-900 px-3 py-2 text-sm text-red-300 hover:bg-red-950/50"
              >
                Delete
              </button>
            </div>
          )
        })}
      </section>
    </div>
  )
}