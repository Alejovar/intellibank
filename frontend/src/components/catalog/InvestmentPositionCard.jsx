const money = (value) => (value ?? 0).toLocaleString("es-MX", {
  style: "currency", currency: "MXN", maximumFractionDigits: 0,
});

export default function InvestmentPositionCard({ product, amount = 0, currentValue = 0, gain = 0, gainPct = 0, risk, status }) {
  return (
    <div className="card investment-position-card">
      <div className="investment-position-heading">
        <div><div className="card-title">{product}</div><div className="card-subtitle">{risk ? `Riesgo ${risk}` : "Posición activa"}</div></div>
        {status && <span className="badge">{status}</span>}
      </div>
      <div className="investment-position-values">
        <span><small>Valor actual</small><strong>{money(currentValue)}</strong></span>
        <span><small>Ganancia</small><strong className={gain >= 0 ? "positive" : "negative"}>{gain >= 0 ? "+" : ""}{money(gain)} ({gainPct}%)</strong></span>
      </div>
      <div className="field-help">Aportación inicial: {money(amount)}</div>
    </div>
  );
}
