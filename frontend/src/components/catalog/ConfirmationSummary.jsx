export default function ConfirmationSummary({ title, rows = [], note, actions = [], onAction }) {
  return (
    <div className="card" style={{ overflow: "hidden", padding: 0 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: 14, borderBottom: "1px solid #F4ECEE" }}>
        <span style={{ width: 34, height: 24, borderRadius: 6, background: "linear-gradient(135deg,#C2002E,#8A0D28)" }} />
        <div className="card-title" style={{ margin: 0 }}>{title}</div>
      </div>
      <div>
        {rows.map((r, i) => (
          <div key={i} style={{
            display: "flex", justifyContent: "space-between", padding: "12px 14px",
            borderBottom: "1px solid #F4ECEE",
          }}>
            <span style={{ fontSize: 13, color: "var(--ink-600)" }}>{r.label}</span>
            <span style={{ fontSize: 13.5, fontWeight: 800, color: r.highlighted ? "var(--red-500)" : "var(--ink-900)" }}>
              {r.value}
            </span>
          </div>
        ))}
      </div>
      {note && (
        <div className="info-banner" style={{ margin: 12 }}>
          <span style={{ color: "var(--red-500)", fontWeight: 800 }}>□</span><span>{note}</span>
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: "0 12px 12px" }}>
        {actions.map((a, i) => (
          <button
            key={i}
            className={`btn btn-${a.style || "primary"}`}
            onClick={() => onAction && onAction(a)}
          >
            {a.requires_biometric ? "Confirmar · " : ""}{a.label || "Continuar"}
          </button>
        ))}
      </div>
    </div>
  );
}
