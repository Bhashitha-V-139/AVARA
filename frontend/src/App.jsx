import { useEffect, useRef, useState } from 'react'
import { askQuestion } from './api'
import Agent from './Agent'
import KnowledgeBase from './KnowledgeBase'
import { canListen, canSpeak, listenOnce, speak, stopSpeaking } from './voice'

const SUGGESTIONS = [
  'What ethical standards are expected from employees?',
  'What is the purpose of the whistleblower policy?',
  'How should an employee report a violation?',
]

function AssistantMessage({ message, onSpeak, speakingId, id }) {
  const { answer, grounded, citations, missing } = message
  const isSpeaking = speakingId === id

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span
          className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
            grounded
              ? 'bg-emerald-900/60 text-emerald-300'
              : 'bg-amber-900/60 text-amber-300'
          }`}
        >
          {grounded ? 'Supported by documents' : 'Not found in documents'}
        </span>
        {canSpeak() && (
          <button
            onClick={() => onSpeak(id, answer)}
            className="rounded-lg border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:border-violet-500"
          >
            {isSpeaking ? 'Stop reading' : 'Read aloud'}
          </button>
        )}
      </div>

      <p className="whitespace-pre-wrap leading-relaxed">{answer}</p>

      {missing?.length > 0 && (
        <div className="rounded-xl border border-amber-700/50 bg-amber-950/40 p-3 text-sm">
          <p className="font-medium text-amber-300">Not covered by the documents:</p>
          <ul className="mt-1 ml-5 list-disc text-amber-200">
            {missing.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {citations?.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-slate-400">Sources</p>
          {citations.map((c) => (
            <div key={c.number} className="rounded-lg border border-slate-700 bg-slate-900 p-3 text-sm">
              <p className="font-medium text-slate-200">
                [{c.number}] {c.filename} · PDF page {c.page_number}
              </p>
              <p className="mt-1 line-clamp-2 text-slate-400">{c.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ChatView({ messages, loading, bottomRef, onSuggestion, onSpeak, speakingId }) {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {messages.length === 0 && (
        <div className="space-y-4 pt-8 text-center">
          <p className="text-slate-300">Ask a question about your uploaded documents.</p>
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => onSuggestion(s)}
                className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-left text-sm hover:border-violet-500"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.map((m, i) => {
        if (m.role === 'user') {
          return (
            <div key={i} className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl bg-violet-600 px-4 py-3">{m.content}</div>
            </div>
          )
        }
        if (m.role === 'error') {
          return (
            <div key={i} className="rounded-xl border border-red-800 bg-red-950/50 p-4 text-red-300">
              {m.content}
            </div>
          )
        }
        return (
          <div key={i} className="rounded-2xl bg-slate-800 p-5">
            <AssistantMessage
              message={m}
              id={i}
              onSpeak={onSpeak}
              speakingId={speakingId}
            />
          </div>
        )
      })}

      {loading && (
        <p className="animate-pulse text-sm text-slate-400">AVARA is searching the documents...</p>
      )}
      <div ref={bottomRef} />
    </div>
  )
}

export default function App() {
  const [view, setView] = useState('chat')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)
  const [voiceError, setVoiceError] = useState(null)
  const [speakingId, setSpeakingId] = useState(null)
  const [autoSpeak, setAutoSpeak] = useState(false)
  const stopListeningRef = useRef(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Stop any speech when the page unloads or the user leaves the chat.
  useEffect(() => () => stopSpeaking(), [])

  async function send(text) {
    const question = text.trim()
    if (!question || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const data = await askQuestion(question, sessionId)
      setSessionId(data.session_id)
      const index = messages.length + 1
      setMessages((prev) => [...prev, { role: 'assistant', ...data }])
      // Read aloud only verified answers, never "not found" or error text.
      if (autoSpeak && data.grounded) {
        setSpeakingId(index)
        speak(data.answer, () => setSpeakingId(null))
      }    } catch (err) {
      // An expired session starts a fresh conversation on the next question.
      if (err.status === 404) setSessionId(null)
      setMessages((prev) => [...prev, { role: 'error', content: err.message }])
    } finally {
      setLoading(false)
    }
  }

  function toggleListening() {
    if (listening) {
      stopListeningRef.current?.()
      setListening(false)
      return
    }
    setVoiceError(null)
    setListening(true)
    stopListeningRef.current = listenOnce({
        onText: (text) => {
        setInput(text)
        setListening(false)
      },
      onError: (message) => {
        setVoiceError(message)
        setListening(false)
      },
      onEnd: () => setListening(false),
    })
  }

  function handleSpeak(id, text) {
    if (speakingId === id) {
      stopSpeaking()
      setSpeakingId(null)
      return
    }
    setSpeakingId(id)
    speak(text, () => setSpeakingId(null))
  }

  function newConversation() {
    stopSpeaking()
    setMessages([])
    setSessionId(null)
    setInput('')
    setSpeakingId(null)
  }

  const tabClass = (name) =>
    `rounded-md px-3 py-1.5 text-sm ${
      view === name ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'
    }`

  return (
    <div className="flex h-screen flex-col bg-slate-900 text-slate-100">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold">AVARA</h1>
          <p className="text-xs text-slate-400">Your Knowledge. Your AI Expert.</p>
        </div>
        <div className="flex items-center gap-2">
          <nav className="flex rounded-lg border border-slate-700 p-1">
            <button onClick={() => setView('chat')} className={tabClass('chat')}>
              Chat
            </button>
            <button onClick={() => setView('knowledge')} className={tabClass('knowledge')}>
              Knowledge base
            </button>
            <button onClick={() => setView('agent')} className={tabClass('agent')}>
              Agent tools
            </button>
          </nav>
          {view === 'chat' && (
            <button
              onClick={newConversation}
              className="rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800"
            >
              New conversation
            </button>
          )}
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-6 py-6">
        {view === 'chat' && (
          <ChatView
            messages={messages}
            loading={loading}
            bottomRef={bottomRef}
            onSuggestion={send}
            onSpeak={handleSpeak}
            speakingId={speakingId}
          />
        )}
        {view === 'knowledge' && <KnowledgeBase />}
        {view === 'agent' && <Agent />}
      </main>

      {view === 'chat' && (
        <footer className="border-t border-slate-800 px-6 py-4">
          <div className="mx-auto mb-3 flex max-w-3xl flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
            {canSpeak() && (
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={autoSpeak}
                  onChange={(e) => {
                    setAutoSpeak(e.target.checked)
                    if (!e.target.checked) stopSpeaking()
                  }}
                />
                Read answers aloud automatically
              </label>
            )}
            {!canListen() && <span>Voice input works in Chrome or Edge.</span>}
          </div>

          {voiceError && (
            <p className="mx-auto mb-3 max-w-3xl text-sm text-amber-300">{voiceError}</p>
          )}

          <form
            className="mx-auto flex max-w-3xl gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              send(input)
            }}
          >
            <button
              type="button"
              onClick={toggleListening}
              disabled={loading || !canListen()}
              aria-label={listening ? 'Stop listening' : 'Speak your question'}
              className={`rounded-xl border px-4 py-3 disabled:opacity-40 ${
                listening
                  ? 'animate-pulse border-red-500 bg-red-950/50 text-red-300'
                  : 'border-slate-700 bg-slate-800 hover:border-violet-500'
              }`}
            >
              {listening ? 'Listening...' : 'Mic'}
            </button>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              placeholder="Ask about your documents..."
              className="flex-1 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 focus:border-violet-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-xl bg-violet-600 px-5 py-3 font-medium hover:bg-violet-500 disabled:opacity-40"
            >
              Send
            </button>
          </form>
        </footer>
      )}
    </div>
  )
}