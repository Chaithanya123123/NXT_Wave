import Markdown from './Markdown.jsx'

const TOOL_META = {
  weather: { icon: '🌦️', label: 'Weather' },
  mandi: { icon: '💰', label: 'Mandi price' },
  soil: { icon: '🌱', label: 'Soil test' },
  rag: { icon: '📚', label: 'Expert advice' },
  geocode: { icon: '📍', label: 'Location' },
}

export default function ChatMessage({ message, onSpeak, onRetry }) {
  const { role, content, sources = [], trace = [], lang, audioUrl, warning, error } = message
  const isUser = role === 'user'

  return (
    <div className={`message ${isUser ? 'user' : 'assistant'} ${error ? 'is-error' : ''}`}>
      {!isUser && <div className="avatar">{error ? '⚠️' : '🤖'}</div>}
      <div className="bubble-wrap">
        <div className="bubble">
          {isUser ? (
            <div className="answer-text">{content}</div>
          ) : (
            <Markdown text={content} />
          )}

          {warning && <div className="warning">⚠️ {warning}</div>}

          {!isUser && !error && (
            <div className="msg-meta">
              {lang && (
                <span className="lang-chip" title="Language detected">
                  🗣️ {lang}
                </span>
              )}
              {sources.map((s) => {
                const meta = TOOL_META[s] || { icon: '•', label: s }
                return (
                  <span key={s} className="source-chip" title={`Data from ${meta.label}`}>
                    {meta.icon} {meta.label}
                  </span>
                )
              })}
              <button className="listen-btn" onClick={() => onSpeak(message)}>
                🔊 Listen
              </button>
              {audioUrl && <audio controls src={audioUrl} className="inline-audio" />}
            </div>
          )}

          {!isUser && !error && trace.length > 0 && (
            <details className="trace-details">
              <summary>🧠 See how I found this answer ({trace.length} steps)</summary>
              <pre>{trace.join('\n')}</pre>
            </details>
          )}
        </div>
        {!isUser && error && onRetry && (
          <button className="retry-btn" onClick={onRetry}>
            🔄 Try again
          </button>
        )}
      </div>
    </div>
  )
}
