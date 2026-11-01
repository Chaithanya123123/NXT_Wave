import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { fetchHealth, fetchTts, streamAsk, transcribeAudio } from './api.js'
import Sidebar from './components/Sidebar.jsx'
import ChatMessage from './components/ChatMessage.jsx'
import ChatInput from './components/ChatInput.jsx'
import TracePanel from './components/TracePanel.jsx'

const EXAMPLES = [
  {
    icon: '🌧️',
    title: 'Will it rain this week?',
    sub: 'Check the 7-day forecast before you spray',
    q: 'Will it rain this week? Can I spray pesticide on my crop?',
    tint: 'blue',
  },
  {
    icon: '💰',
    title: 'Tomato price today?',
    sub: 'Live mandi rates near your district',
    q: "What is today's tomato price in the nearest mandi?",
    tint: 'amber',
  },
  {
    icon: '🌱',
    title: 'Which crop suits my soil?',
    sub: 'Soil health + fertilizer advice',
    q: 'Which crop is best for my soil? Should I add fertilizer?',
    tint: 'green',
  },
  {
    icon: '🐛',
    title: 'Pest on my rice crop',
    sub: 'Identify the pest and get treatment',
    q: 'There are brown spots on my rice leaves. What pest or disease is this and what should I spray?',
    tint: 'red',
  },
]

const EMOJI_RE =
  /[\u{1F000}-\u{1FAFF}\u2600-\u27BF\u2300-\u23FF\u2B00-\u2BFF\uFE0F\u200D\u20E3]+/gu

function stripEmoji(text) {
  return text
    .replace(EMOJI_RE, ' ')
    .replace(/[#*`>|_]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [busy, setBusy] = useState(false)
  const [liveTrace, setLiveTrace] = useState([])
  const [error, setError] = useState(null)
  const [health, setHealth] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [settings, setSettings] = useState({
    location: 'Kurnool',
    language: 'auto',
    voiceInput: false,
    autoTts: false,
  })

  const scrollRef = useRef(null)
  const audioUrlsRef = useRef([])

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth({ status: 'down' }))
  }, [])

  useEffect(() => () => {
    audioUrlsRef.current.forEach((u) => URL.revokeObjectURL(u))
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, liveTrace, busy])

  const recentHistory = useMemo(
    () =>
      messages
        .filter((m) => !m.error)
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content })),
    [messages]
  )

  const speak = useCallback(async (text, langCode) => {
    try {
      const blob = await fetchTts(stripEmoji(text), langCode || 'en')
      const url = URL.createObjectURL(blob)
      audioUrlsRef.current.push(url)
      return url
    } catch {
      return null
    }
  }, [])

  const sendQuery = useCallback(
    async (query) => {
      const text = (query || '').trim()
      if (!text || busy) return
      setError(null)
      setBusy(true)
      setLiveTrace([])
      setMessages((prev) => [...prev, { role: 'user', content: text }])

      const payload = {
        query: text,
        location_hint: settings.location?.trim() || null,
        declared_lang: settings.language === 'auto' ? null : settings.language,
        history: recentHistory,
      }

      try {
        const result = await streamAsk(payload, {
          onTrace: (line) => setLiveTrace((prev) => [...prev, line]),
        })
        if (!result) throw new Error('No answer returned — please retry.')

        const answer = result.answer || 'No answer returned — retry.'
        let audioUrl = null
        if (settings.autoTts) audioUrl = await speak(answer, result.detected_lang_code)

        const geo = result.tool_outputs?.geocode
        let warning = null
        if (settings.location && geo && geo.ok === false) {
          warning = `We couldn't find “${settings.location}” on the map — weather and soil were skipped. Try a district name like Kurnool or Indore.`
        }

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: answer,
            sources: result.sources || [],
            trace: result.reasoning_trace || [],
            lang: result.detected_language,
            langCode: result.detected_lang_code,
            audioUrl,
            warning,
          },
        ])
      } catch (err) {
        const msg =
          err?.name === 'AbortError'
            ? 'Request cancelled.'
            : String(err?.message || err)
        setError(msg)
        setMessages((prev) => [...prev, { role: 'assistant', content: `⚠️ ${msg}`, error: true }])
      } finally {
        setLiveTrace([])
        setBusy(false)
      }
    },
    [busy, recentHistory, settings, speak]
  )

  const handleVoice = useCallback(
    async (blob) => {
      setError(null)
      try {
        const transcript = await transcribeAudio(blob, settings.language)
        if (!transcript) {
          setError("We couldn't hear you — please try recording again.")
          return
        }
        await sendQuery(transcript)
      } catch (err) {
        setError(`Voice input failed: ${err?.message || err}`)
      }
    },
    [sendQuery, settings.language]
  )

  const playMessageAudio = useCallback(
    async (msg) => {
      if (msg.audioUrl) {
        new Audio(msg.audioUrl).play().catch(() => {})
        return
      }
      const url = await speak(msg.content, msg.langCode)
      if (url) new Audio(url).play().catch(() => {})
      else setError("Voice reply is unavailable — check the backend's SARVAM_API_KEY.")
    },
    [speak]
  )

  const online = health?.status === 'ok'

  return (
    <div className="app">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        settings={settings}
        onChange={setSettings}
        health={health}
      />

      <main className="chat">
        <header className="chat-header">
          <button
            className="icon-btn menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open settings"
          >
            ☰
          </button>

          <div className="brand">
            <span className="brand-mark">🌾</span>
            <div className="brand-text">
              <strong>AgriAdvisor AI</strong>
              <small>Your farm advisor</small>
            </div>
          </div>

          <label className="lang-switch" title="Answer language">
            <span className="lang-ico">🗣️</span>
            <select
              value={settings.language}
              onChange={(e) => setSettings({ ...settings, language: e.target.value })}
            >
              <option value="auto">Auto</option>
              <option value="english">English</option>
              <option value="hindi">हिन्दी</option>
              <option value="telugu">తెలుగు</option>
              <option value="tamil">தமிழ்</option>
              <option value="marathi">मराठी</option>
              <option value="kannada">ಕನ್ನಡ</option>
              <option value="bengali">বাংলা</option>
              <option value="gujarati">ગુજરાતી</option>
              <option value="punjabi">ਪੰਜਾਬੀ</option>
            </select>
          </label>

          <span className={`badge ${online ? 'badge-ok' : 'badge-err'}`}>
            {online ? '● Live' : '● Offline'}
          </span>
        </header>

        <div className="messages" ref={scrollRef}>
          {messages.length === 0 && !busy && (
            <div className="empty-state">
              <div className="empty-icon">🌾</div>
              <h2>Ask anything about your farm</h2>
              <p className="empty-sub">
                Weather · Market prices · Pests · Soil — answered live, in your language.
              </p>

              <div className="example-grid">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex.title}
                    className={`example-card ${ex.tint}`}
                    onClick={() => sendQuery(ex.q)}
                  >
                    <span className="ex-icon">{ex.icon}</span>
                    <span className="ex-body">
                      <span className="ex-title">{ex.title}</span>
                      <span className="ex-sub">{ex.sub}</span>
                    </span>
                    <span className="ex-arrow">›</span>
                  </button>
                ))}
              </div>

              <p className="voice-hint">
                <button className="voice-hint-btn" onClick={() => setSettings((s) => ({ ...s, voiceInput: true }))}>
                  🎤
                </button>
                Prefer to speak? Turn on <strong>Voice input</strong> in settings and tap the mic
                below.
              </p>
            </div>
          )}

          {messages.map((m, i) => (
            <ChatMessage
              key={i}
              message={m}
              onSpeak={playMessageAudio}
              onRetry={m.error && m.role === 'assistant' ? () => sendQuery(messages[i - 1]?.content) : null}
            />
          ))}

          {busy && (
            <div className="message assistant">
              <div className="avatar">🤖</div>
              <div className="bubble">
                <div className="thinking">
                  <span className="thinking-ico">🌾</span>
                  <div>
                    <strong>AgriAdvisor is checking live data…</strong>
                    <p>Weather, mandi prices and soil reports are being fetched for you.</p>
                  </div>
                </div>
                <TracePanel lines={liveTrace} live />
              </div>
            </div>
          )}

          {error && !busy && <div className="error-bar">⚠️ {error}</div>}
        </div>

        <ChatInput
          busy={busy}
          voiceEnabled={settings.voiceInput}
          onSend={sendQuery}
          onVoice={handleVoice}
          quickPrompts={messages.length === 0 ? [] : EXAMPLES.slice(0, 3)}
        />
      </main>
    </div>
  )
}
