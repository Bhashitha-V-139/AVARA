import { useState } from 'react'
import { runAgent } from './api'

const EXAMPLES = [
  'Summarize the whistleblower policy',
  'Search the documents for how to report a violation',
  'Create an onboarding checklist for a new software engineer',
  'Turn this into a task list: prepare for a policy review meeting',
]

const TOOL_LABELS = {
  extract_policy_information: 'Policy extraction',
  search_knowledge_base: 'Knowledge search',
  summarize_document: 'Document summary',
  generate_onboarding_checklist: 'Onboarding checklist',
  create_task_list: 'Task list',
}

const POLICY_FIELDS = {
  purpose: 'Purpose',
  scope: 'Scope',
  responsibilities: 'Responsibilities',
  consequences: 'Consequences',
  contacts: 'Contacts',
}

function Cite({ items }) {
  if (!items?.length) return null
  const text = items.map((c) => `${c.document}, PDF page ${c.page_number}`).join('; ')
  return <span className="ml-2 text-xs text-slate-400">({text})</span>
}

function ToolResult({ call }) {
  const r = call.result
  if (!r) return null

  if (r.status !== 'ok') {
    return (
      <p className="text-sm text-amber-300">
        {r.error || 'No matching content was found in the documents.'}
      </p>
    )
  }

  switch (call.name) {
    case 'extract_policy_information':
      return (
        <dl className="space-y-2 text-sm">
          {Object.entries(POLICY_FIELDS).map(([key, label]) => {
            const field = r.fields?.[key]
            if (!field) return null
            const notStated = field.citations.length === 0
            return (
              <div key={key}>
                <dt className="font-medium text-slate-200">{label}</dt>
                <dd className={notStated ? 'text-amber-300' : 'text-slate-300'}>
                  {field.value}
                  <Cite items={field.citations} />
                </dd>
              </div>
            )
          })}
        </dl>
      )

    case 'search_knowledge_base':
      return (
        <ul className="space-y-2 text-sm">
          {r.results.map((hit, i) => (
            <li key={i}>
              <span className="text-slate-200">
                {hit.document}, PDF page {hit.page_number}
              </span>
              <p className="line-clamp-2 text-slate-400">{hit.snippet}</p>
            </li>
          ))}
        </ul>
      )

    case 'summarize_document':
      return (
        <div className="space-y-3 text-sm">
          {r.sections.map((s, i) => (
            <div key={i}>
              <p className="font-medium text-slate-200">{s.title}</p>
              <p className="text-slate-300">
                {s.summary}
                <Cite items={s.citations} />
              </p>
            </div>
          ))}
          <p className="text-xs text-slate-500">
            Based on {r.coverage.chunks_read} of {r.coverage.chunks_total} text sections, covering
            pages {r.coverage.pages_read.join(', ')}. This may not cover the whole document.
          </p>
        </div>
      )

    case 'generate_onboarding_checklist':
      return (
        <ul className="space-y-1 text-sm">
          {r.items.map((item, i) => (
            <li key={i} className="text-slate-300">
              ☐ {item.task}
              <Cite items={item.citations} />
            </li>
          ))}
        </ul>
      )

    case 'create_task_list':
      return (
        <ul className="space-y-1 text-sm">
          {r.tasks.map((t, i) => (
            <li key={i} className="text-slate-300">
              ☐ {t.task}
              <span className="ml-2 text-xs text-slate-500">
                {t.from === 'documents' ? 'from documents' : 'from your request'}
              </span>
              <Cite items={t.citations} />
            </li>
          ))}
        </ul>
      )

    default:
      return <pre className="overflow-x-auto text-xs text-slate-400">{JSON.stringify(r, null, 2)}</pre>
  }
}

function ToolLog({ calls }) {
  if (!calls.length) {
    return <p className="text-sm text-slate-400">No tools were needed for this request.</p>
  }

  return (
    <div className="space-y-3">
      {calls.map((call, i) => (
        <div key={i} className="rounded-xl border border-slate-700 bg-slate-900 p-4">
          <div className="flex items-center justify-between gap-2">
            <p className="font-medium">{TOOL_LABELS[call.name] ?? call.name}</p>
            <span
              className={`rounded-full px-2 py-0.5 text-xs ${
                call.status === 'ok'
                  ? 'bg-emerald-900/60 text-emerald-300'
                  : 'bg-amber-900/60 text-amber-300'
              }`}
            >
              {call.status}
            </span>
          </div>
          <p className="mt-1 break-all text-xs text-slate-500">
            Arguments: {JSON.stringify(call.arguments)}
          </p>
          <div className="mt-3">
            <ToolResult call={call} />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Agent() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function run(request) {
    const value = request.trim()
    if (!value || loading) return

    setText(value)
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      setResult(await runAgent(value))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <section className="rounded-2xl border border-slate-700 bg-slate-800 p-6">
        <h2 className="text-lg font-semibold">Agent tools</h2>
        <p className="mt-1 text-sm text-slate-400">
          AVARA chooses which read-only tools to use, runs them, and shows each result.
        </p>

        <form
          className="mt-4 flex gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            run(text)
          }}
        >
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
            placeholder="Describe what you need..."
            className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 focus:border-violet-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="rounded-xl bg-violet-600 px-5 py-3 font-medium hover:bg-violet-500 disabled:opacity-40"
          >
            Run
          </button>
        </form>

        <div className="mt-4 flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              onClick={() => run(example)}
              disabled={loading}
              className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-violet-500 disabled:opacity-40"
            >
              {example}
            </button>
          ))}
        </div>
      </section>

      {loading && (
        <p className="animate-pulse text-sm text-slate-400">AVARA is working through the request...</p>
      )}

      {error && (
        <div className="rounded-xl border border-red-800 bg-red-950/50 p-4 text-red-300">{error}</div>
      )}

      {result && (
        <section className="space-y-4">
          <div className="rounded-2xl bg-slate-800 p-5">
            <h3 className="text-xs font-medium uppercase tracking-wide text-slate-400">Answer</h3>
            <p className="mt-2 whitespace-pre-wrap leading-relaxed">
              {result.answer.replace(/\*\*/g, '')}
            </p>
            {result.limit_reached && (
              <p className="mt-3 text-xs text-amber-300">
                The tool limit (3 calls) was reached, so this answer uses the results gathered so far.
              </p>
            )}
          </div>

          <div className="space-y-3">
            <h3 className="text-xs font-medium uppercase tracking-wide text-slate-400">Tools used</h3>
            <ToolLog calls={result.tool_calls} />
          </div>
        </section>
      )}
    </div>
  )
}