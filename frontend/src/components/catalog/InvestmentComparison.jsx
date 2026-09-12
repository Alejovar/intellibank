const money = (value) => (value ?? 0).toLocaleString("es-MX", {
  style: "currency", currency: "MXN", maximumFractionDigits: 0,
});

export default function InvestmentComparison({ products = [] }) {
  return (
    <div className="card">
      <div className="card-title">Comparación de alternativas</div>
      <div className="comparison-list">
        {products.map((product) => (
          <div className="comparison-row" key={product.productId || product.title}>
            <div><strong>{product.title}</strong><small>Riesgo {product.risk} · {product.rate}% anual</small></div>
            <span><b>{money(product.finalValue)}</b><small className="positive">+{money(product.estimatedGain)}</small></span>
          </div>
        ))}
        {!products.length && <div className="saved-empty">No hay productos para comparar.</div>}
      </div>
    </div>
  );
}
