export default function BalanceCard({ accountLabel, maskedNumber, balance, limit, available, progressPercent }) {
  const fmt = (n) => (n ?? 0).toLocaleString("es-MX", { style: "currency", currency: "MXN" });
  const pct = progressPercent ?? (limit ? Math.min(100, (balance / limit) * 100) : null);
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div className="card-title">{accountLabel}</div>
          <div style={{ fontSize: 12, color: "var(--ink-600)" }}>{maskedNumber}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 11, color: "var(--ink-600)" }}>
            {limit ? "Saldo actual" : "Saldo disponible"}
          </div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{fmt(balance)}</div>
        </div>
      </div>
      {pct !== null && (
        <div style={{ marginTop: 12 }}>
          <div className="progress-bar"><div style={{ width: `${pct}%` }} /></div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, color: "var(--ink-600)", marginTop: 6 }}>
            <span>Limite: {fmt(limit)}</span>
            {available !== undefined && <span>Disponible: {fmt(available)}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
