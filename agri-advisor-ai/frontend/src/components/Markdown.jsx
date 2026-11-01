import { Fragment } from 'react'

// Tiny safe markdown renderer — headers, bullet lists, bold, italic, code.
// Builds React elements only (no dangerouslySetInnerHTML), so it's XSS-safe.

const INLINE_RE = /(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`)/g

function renderInline(text) {
  const out = []
  let last = 0
  let m
  let i = 0
  INLINE_RE.lastIndex = 0
  while ((m = INLINE_RE.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index))
    const tok = m[0]
    if (tok.startsWith('**')) out.push(<strong key={i++}>{tok.slice(2, -2)}</strong>)
    else if (tok.startsWith('`')) out.push(<code key={i++}>{tok.slice(1, -1)}</code>)
    else out.push(<em key={i++}>{tok.slice(1, -1)}</em>)
    last = m.index + tok.length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

export default function Markdown({ text }) {
  if (!text) return null
  const lines = String(text).replace(/\r/g, '').split('\n')
  const blocks = []
  let para = []
  let list = []
  let key = 0

  const flushPara = () => {
    if (para.length) {
      blocks.push(<p key={key++}>{renderInline(para.join('\n'))}</p>)
      para = []
    }
  }
  const flushList = () => {
    if (list.length) {
      blocks.push(
        <ul key={key++}>
          {list.map((li, j) => (
            <li key={j}>{renderInline(li)}</li>
          ))}
        </ul>
      )
      list = []
    }
  }
  const flushAll = () => {
    flushPara()
    flushList()
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    const header = line.match(/^(#{1,4})\s+(.*)$/)
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/)

    if (header) {
      flushAll()
      const level = header[1].length
      const content = renderInline(header[2])
      if (level <= 3) blocks.push(<h3 key={key++}>{content}</h3>)
      else blocks.push(<h4 key={key++}>{content}</h4>)
    } else if (bullet) {
      flushPara()
      list.push(bullet[1])
    } else if (!line.trim()) {
      flushAll()
    } else {
      flushList()
      para.push(line)
    }
  }
  flushAll()
  return <div className="md">{blocks.map((b, i) => <Fragment key={i}>{b}</Fragment>)}</div>
}
