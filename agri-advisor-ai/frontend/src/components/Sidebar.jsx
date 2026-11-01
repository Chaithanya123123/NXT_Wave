const LANGUAGES = [
  ['auto', '🌐 Auto-detect (recommended)'],
  ['english', 'English'],
  ['hindi', 'हिन्दी (Hindi)'],
  ['telugu', 'తెలుగు (Telugu)'],
  ['tamil', 'தமிழ் (Tamil)'],
  ['marathi', 'मराठी (Marathi)'],
  ['kannada', 'ಕನ್ನಡ (Kannada)'],
  ['bengali', 'বাংলা (Bengali)'],
  ['gujarati', 'ગુજરાતી (Gujarati)'],
  ['punjabi', 'ਪੰਜਾਬੀ (Punjabi)'],
]

export default function Sidebar({ open, onClose, settings, onChange, health }) {
  const set = (patch) => onChange({ ...settings, ...patch })

  return (
    <>
      <div className={`overlay ${open ? 'show' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <span className="brand-mark">🌾</span>
          <div>
            <strong>AgriAdvisor AI</strong>
            <small>Smart advice for your farm</small>
          </div>
          <button className="icon-btn close-btn" onClick={onClose} aria-label="Close settings">
            ✕
          </button>
        </div>

        <section className="side-section">
          <label className="field-label" htmlFor="location">
            📍 Your location
          </label>
          <input
            id="location"
            className="text-input big"
            value={settings.location}
            placeholder="District or town, e.g. Kurnool"
            onChange={(e) => set({ location: e.target.value })}
          />
          <p className="hint">
            Used for weather &amp; soil advice. Market price questions work without it.
          </p>
        </section>

        <section className="side-section">
          <label className="field-label" htmlFor="language">
            🗣️ I want answers in
          </label>
          <select
            id="language"
            className="text-input big"
            value={settings.language}
            onChange={(e) => set({ language: e.target.value })}
          >
            {LANGUAGES.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </section>

        <section className="side-section toggles">
          <label className="toggle">
            <input
              type="checkbox"
              checked={settings.voiceInput}
              onChange={(e) => set({ voiceInput: e.target.checked })}
            />
            <span className="slider" />
            <span className="toggle-label">🎤 Ask by voice (speak instead of typing)</span>
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={settings.autoTts}
              onChange={(e) => set({ autoTts: e.target.checked })}
            />
            <span className="slider" />
            <span className="toggle-label">🔊 Read every answer aloud</span>
          </label>
        </section>

        <section className="how-it-works">
          <strong>How it works</strong>
          <ol>
            <li><span>1</span> Ask your question — type or speak</li>
            <li><span>2</span> Watch live data being fetched</li>
            <li><span>3</span> Get advice in your language</li>
          </ol>
        </section>

        <footer className="sidebar-footer">
          <div className={`status-pill ${health?.status === 'ok' ? 'ok' : 'err'}`}>
            {health?.status === 'ok' ? '● Connected to live data' : '● Backend unreachable'}
          </div>
          <p className="hint sources-list">
            Sources: Open-Meteo weather · Agmarknet mandi prices · SoilGrids soil health ·
            expert crop advisories
          </p>
        </footer>
      </aside>
    </>
  )
}
