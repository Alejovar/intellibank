const money = (value) => (value ?? 0).toLocaleString("es-MX", {
  style: "currency", currency: "MXN", maximumFractionDigits: 0,
});

export default function BeforeAfterPortfolio({ before = {}, after = {} }) {
  return (
    <div className="card">
      <div className="card-title">Tu evolución</div>
      <div className="before-after-grid">
        <div><small>Antes</small><strong>{money(before.totalValue)}</strong><span>{money(before.totalGain)} de ganancia</span></div>
        <div className="before-after-arrow">→</div>
        <div><small>Ahora</small><strong>{money(after.totalValue)}</strong><span className={Number(after.totalGain || 0) >= 0 ? "positive" : "negative"}>{money(after.totalGain)} de ganancia</span></div>
      </div>
    </div>
  );
}
