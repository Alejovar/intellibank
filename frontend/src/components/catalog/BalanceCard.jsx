export default function BalanceCard({ accountLabel, maskedNumber, balance, limit, available, progressPercent }) {
  const fmt = (n) => (n ?? 0).toLocaleString("es-MX", { style: "currency", currency: "MXN" });
  const pct = progressPercent ?? (limit ? Math.min(100, (balance / limit) * 100) : null);
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ width: 34, height: 24, borderRadius: 6, background: "linear-gradient(135deg,#C2002E,#8A0D28)", flex: "none" }} />
          <div>
            <div className="card-title">{accountLabel}</div>
            <div style={{ fontSize: 12, color: "var(--ink-500)", letterSpacing: ".08em" }}>{maskedNumber}</div>
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 11, color: "var(--ink-600)" }}>
            {limit ? "Saldo actual" : "Saldo disponible"}
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-.02em" }}>{fmt(balance)}</div>
        </div>
      </div>
      {pct !== null && (
        <div style={{ marginTop: 12 }}>
          <div className="progress-bar"><div style={{ width: `${pct}%` }} /></div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--ink-500)", marginTop: 7, fontWeight: 600 }}>
            <span>Límite: {fmt(limit)}</span>
            {available !== undefined && <span>Disponible: {fmt(available)}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
