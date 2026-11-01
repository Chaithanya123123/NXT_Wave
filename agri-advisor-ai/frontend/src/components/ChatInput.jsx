import { useEffect, useRef, useState } from 'react'

export default function ChatInput({ busy, voiceEnabled, onSend, onVoice, quickPrompts }) {
  const [text, setText] = useState('')
  const [recording, setRecording] = useState(false)
  const [micError, setMicError] = useState(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])
  const textareaRef = useRef(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 150)}px`
  }, [text])

  const submit = () => {
    if (!text.trim() || busy) return
    onSend(text)
    setText('')
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const startRecording = async () => {
    setMicError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : ''
      const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      chunksRef.current = []
      rec.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data)
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: rec.mimeType || 'audio/webm' })
        if (blob.size > 0) onVoice(blob)
        else setMicError('No audio captured — please try again.')
      }
      rec.start()
      recorderRef.current = rec
      setRecording(true)
    } catch {
      setMicError('Microphone access denied. Please allow the mic in your browser.')
    }
  }

  const stopRecording = () => {
    recorderRef.current?.stop()
    setRecording(false)
  }

  return (
    <div className="composer">
      {quickPrompts?.length > 0 && (
        <div className="chip-row">
          {quickPrompts.map((p) => (
            <button key={p.title} className="quick-chip small" onClick={() => sendSafely(p.q)}>
              <span>{p.icon}</span> {p.title}
            </button>
          ))}
        </div>
      )}

      {micError && <div className="error-bar small">⚠️ {micError}</div>}
      {recording && (
        <div className="recording-banner">
          <span className="rec-dot" /> Listening… speak your question, then tap ⏹ to send
        </div>
      )}

      <div className={`composer-box ${recording ? 'recording' : ''}`}>
        <button
          className={`mic-btn ${voiceEnabled ? '' : 'muted'} ${recording ? 'active' : ''}`}
          onClick={recording ? stopRecording : startRecording}
          title={voiceEnabled ? (recording ? 'Stop and send' : 'Record your question') : 'Turn on voice input in settings'}
          disabled={busy || !voiceEnabled}
        >
          {recording ? '⏹' : '🎤'}
        </button>

        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          placeholder={
            recording
              ? 'Listening…'
              : 'Type your question here — or use the mic 🎤'
          }
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={busy || recording}
        />

        <button
          className="send-btn"
          onClick={submit}
          disabled={busy || !text.trim() || recording}
          title="Send question"
        >
          {busy ? <span className="spinner" /> : '➤'}
        </button>
      </div>

      <p className="composer-hint">
        {voiceEnabled ? '🎤 Tap the mic to speak · ' : ''}Press <strong>Enter</strong> to send
      </p>
    </div>
  )

  function sendSafely(q) {
    onSend(q)
  }
}
