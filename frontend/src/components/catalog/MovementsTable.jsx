export default function MovementsTable({ movements = [] }) {
  const fmt = (n) => (n ?? 0).toLocaleString("es-MX", { style: "currency", currency: "MXN" });
  return (
    <div className="card">
      <div className="card-title">Movimientos</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 6 }}>
        {movements.map((m, i) => (
          <div key={i} style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "9px 0", borderBottom: i < movements.length - 1 ? "1px solid var(--line-100)" : "none",
          }}>
            <div>
              <div style={{ fontSize: 13.5, fontWeight: 500 }}>{m.description}</div>
              <div style={{ fontSize: 11.5, color: "var(--ink-600)" }}>{m.category} · {m.date}</div>
            </div>
            <div style={{ fontSize: 13.5, fontWeight: 600, color: m.amount < 0 ? "var(--ink-900)" : "var(--ok-600)" }}>
              {m.amount < 0 ? "-" : "+"}{fmt(Math.abs(m.amount))}
            </div>
          </div>
        ))}
        {movements.length === 0 && <div style={{ fontSize: 13, color: "var(--ink-600)" }}>Sin movimientos.</div>}
      </div>
    </div>
  );
}
