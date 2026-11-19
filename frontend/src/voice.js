// Browser speech features. Each function returns a safe fallback if the browser lacks support.

const SpeechRecognitionClass =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null

export function canListen() {
  return Boolean(SpeechRecognitionClass)
}

export function canSpeak() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

// Listens for one spoken phrase. Only a final, non-empty result is passed to onText.
// Returns a stop function.
export function listenOnce({ onText, onError, onEnd }) {
  if (!SpeechRecognitionClass) {
    onError('Voice input is not supported in this browser. Try Chrome or Edge.')
    return () => {}
  }

  const recognition = new SpeechRecognitionClass()
  recognition.lang = 'en-US'
  recognition.continuous = false
  recognition.interimResults = false
  recognition.maxAlternatives = 1

  let handled = false

  recognition.onresult = (event) => {
    if (handled) return
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i]
      // Ignore partial results. Only a final result is a complete phrase.
      if (!result.isFinal) continue
      const transcript = result[0]?.transcript?.trim() ?? ''
      if (transcript) {
        handled = true
        recognition.stop()
        onText(transcript)
        return
      }
    }
  }

  recognition.onerror = (event) => {
    const messages = {
      'not-allowed': 'Microphone access was blocked. Allow it in the browser address bar.',
      'no-speech': 'No speech was detected. Try again.',
      'audio-capture': 'No microphone was found.',
    }
    onError(messages[event.error] ?? `Voice input failed (${event.error}).`)
  }

  recognition.onend = () => onEnd?.()

  recognition.start()
  return () => recognition.stop()
}

// Reads text aloud. Calling it again cancels anything still speaking.
export function speak(text, onEnd) {
  if (!canSpeak() || !text) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'en-US'
  utterance.rate = 1.0
  utterance.onend = () => onEnd?.()
  window.speechSynthesis.speak(utterance)
}

export function stopSpeaking() {
  if (canSpeak()) window.speechSynthesis.cancel()
}