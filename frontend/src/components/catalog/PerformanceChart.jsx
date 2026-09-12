const money = (value) => (value ?? 0).toLocaleString("es-MX", {
  style: "currency", currency: "MXN", maximumFractionDigits: 0,
});

export default function PerformanceChart({ data = [], totalGain = 0, returnPct = 0, period = "Acumulado" }) {
  const max = Math.max(...data.map((item) => Math.abs(Number(item.value || item.gain || 0))), 1);
  return (
    <div className="card">
      <div className="investment-position-heading">
        <div><div className="card-title">Rendimiento</div><div className="card-subtitle">{period}</div></div>
        <span className={totalGain >= 0 ? "positive" : "negative"}>{totalGain >= 0 ? "+" : ""}{money(totalGain)}</span>
      </div>
      <div className="performance-chart">
        {data.map((item, index) => {
          const value = Number(item.value ?? item.gain ?? 0);
          return (
            <div className="performance-bar-row" key={item.label || index}>
              <span>{item.label}</span>
              <div className="performance-bar"><i style={{ width: `${Math.max(5, Math.round(Math.abs(value) / max * 100))}%`, background: value >= 0 ? "var(--ok-600)" : "var(--red-500)" }} /></div>
              <strong className={value >= 0 ? "positive" : "negative"}>{item.returnPct != null ? `${item.returnPct}%` : `${value >= 0 ? "+" : ""}${money(value)}`}</strong>
            </div>
          );
        })}
        {!data.length && <div className="saved-empty">Aún no hay datos para mostrar una tendencia.</div>}
      </div>
      <div className="field-help">Rendimiento total: {returnPct}%</div>
    </div>
  );
}
