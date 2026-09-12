export default function SuccessScreen({ title, message, details = [], actions = [], onAction }) {
  return (
    <div style={{ textAlign: "center", padding: "8px 2px", animation: "riseIn .22s ease" }}>
      <div className="success-mark"><span>✓</span></div>
      <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-.025em" }}>{title}</div>
      <div style={{ fontSize: 14, color: "var(--ink-600)", lineHeight: 1.55, margin: "6px auto 0", maxWidth: 290 }}>{message}</div>

      {details.length > 0 && (
        <div className="card" style={{ marginTop: 16, padding: 0, overflow: "hidden", textAlign: "left" }}>
          {details.map((d, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "11px 14px", borderBottom: i < details.length - 1 ? "1px solid #F4ECEE" : 0, fontSize: 13.5 }}>
              <span style={{ color: "var(--ink-600)" }}>{d.label}</span>
              <span style={{ fontWeight: 800 }}>{d.value}</span>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
        {actions.map((a, i) => (
          <button key={i} className={`btn btn-${a.style || "primary"}`} onClick={() => onAction && onAction(a)}>
            {a.label || "Continuar"}
          </button>
        ))}
      </div>
    </div>
  );
}
