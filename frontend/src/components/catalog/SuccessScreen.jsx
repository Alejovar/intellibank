export default function SuccessScreen({ title, message, details = [], actions = [], onAction }) {
  return (
    <div className="card" style={{ textAlign: "center" }}>
      <div style={{
        width: 64, height: 64, borderRadius: "50%", background: "#eef7ee",
        display: "flex", alignItems: "center", justifyContent: "center",
        margin: "6px auto 14px", fontSize: 30,
      }}>✅</div>
      <div style={{ fontSize: 17, fontWeight: 700 }}>{title}</div>
      <div style={{ fontSize: 13, color: "var(--ink-600)", marginTop: 4 }}>{message}</div>

      {details.length > 0 && (
        <div style={{ marginTop: 16, textAlign: "left" }}>
          {details.map((d, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontSize: 13 }}>
              <span style={{ color: "var(--ink-600)" }}>{d.label}</span>
              <span style={{ fontWeight: 600 }}>{d.value}</span>
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
