const money = (value) => (value ?? 0).toLocaleString("es-MX", {
  style: "currency", currency: "MXN", maximumFractionDigits: 0,
});

export default function PortfolioSummaryCard({ totalInvested = 0, totalValue = 0, totalGain = 0, gainPct = 0, asOf }) {
  const positive = totalGain >= 0;
  return (
    <div className="card investment-summary-card">
      <div className="card-subtitle">Valor actual de tu portafolio</div>
      <div className="investment-total">{money(totalValue)}</div>
      <div className="investment-metrics">
        <span><small>Invertido</small><strong>{money(totalInvested)}</strong></span>
        <span><small>Rendimiento</small><strong className={positive ? "positive" : "negative"}>{positive ? "+" : ""}{money(totalGain)} ({gainPct}%)</strong></span>
      </div>
      {asOf && <div className="field-help">Actualizado {asOf}</div>}
    </div>
  );
}
