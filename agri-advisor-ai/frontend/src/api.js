const API_BASE = import.meta.env.VITE_API_URL || ''

export async function fetchHealth() {
  const r = await fetch(`${API_BASE}/health`)
  if (!r.ok) throw new Error(`health ${r.status}`)
  return r.json()
}

/**
 * POST /ask/stream — NDJSON stream.
 * onTrace(line) is called as the agent works; resolves with the final result.
 */
export async function streamAsk(payload, { onTrace, signal } = {}) {
  const res = await fetch(`${API_BASE}/ask/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  if (!res.body) throw new Error('streaming not supported by browser')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result = null

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (!line.trim()) continue
      let event
      try {
        event = JSON.parse(line)
      } catch {
        continue
      }
      if (event.type === 'trace') onTrace?.(event.line)
      else if (event.type === 'done') result = event.result
      else if (event.type === 'error') throw new Error(event.error || 'stream failed')
    }
  }
  return result
}

export async function transcribeAudio(blob, langHint) {
  const form = new FormData()
  form.append('audio', blob, 'recording.webm')
  const qs = langHint && langHint !== 'auto' ? `?lang_hint=${langHint}` : ''
  const r = await fetch(`${API_BASE}/transcribe${qs}`, { method: 'POST', body: form })
  if (!r.ok) throw new Error(`transcribe ${r.status}: ${await r.text()}`)
  return (await r.json()).transcript || ''
}

export async function fetchTts(text, langCode) {
  const r = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, lang_code: langCode || 'en' }),
  })
  if (!r.ok) throw new Error(`tts ${r.status}`)
  return r.blob()
}
