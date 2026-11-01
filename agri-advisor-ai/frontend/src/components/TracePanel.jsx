export default function TracePanel({ lines, live }) {
  if (!lines?.length) {
    return live ? (
      <div className="trace-panel idle">
        <span className="trace-dot" /> Planning which live data to fetch…
      </div>
    ) : null
  }
  return (
    <div className={`trace-panel ${live ? 'live' : ''}`}>
      <div className="trace-header">
        <span className="trace-dot" /> Agent is working
      </div>
      <ul>
        {lines.map((l, i) => (
          <li key={i}>{l}</li>
        ))}
      </ul>
    </div>
  )
}
