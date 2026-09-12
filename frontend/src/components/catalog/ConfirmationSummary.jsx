export default function ConfirmationSummary({ title, rows = [], note, actions = [], onAction }) {
  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div style={{ marginTop: 8 }}>
        {rows.map((r, i) => (
          <div key={i} style={{
            display: "flex", justifyContent: "space-between", padding: "8px 0",
            borderBottom: i < rows.length - 1 ? "1px solid var(--line-100)" : "none",
          }}>
            <span style={{ fontSize: 13, color: "var(--ink-600)" }}>{r.label}</span>
            <span style={{ fontSize: 13.5, fontWeight: 700, color: r.highlighted ? "var(--ok-600)" : "var(--ink-900)" }}>
              {r.value}
            </span>
          </div>
        ))}
      </div>
      {note && (
        <div className="info-banner tip" style={{ marginTop: 10 }}>
          <span>🔒</span><span>{note}</span>
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 12 }}>
        {actions.map((a, i) => (
          <button
            key={i}
            className={`btn btn-${a.style || "primary"}`}
            onClick={() => onAction && onAction(a)}
          >
            {a.requires_biometric ? "🔐 " : ""}{a.label || "Continuar"}
          </button>
        ))}
      </div>
    </div>
  );
}
