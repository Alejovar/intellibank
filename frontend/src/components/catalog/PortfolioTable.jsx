const money = (value) => (value ?? 0).toLocaleString("es-MX", {
  style: "currency", currency: "MXN", maximumFractionDigits: 0,
});

export default function PortfolioTable({ columns = ["Producto", "Valor", "Rendimiento"], rows = [] }) {
  return (
    <div className="card">
      <div className="card-title">Detalle de inversiones</div>
      <div className="investment-table">
        <div className="investment-table-row investment-table-head">{columns.map((column) => <span key={column}>{column}</span>)}</div>
        {rows.map((row, index) => (
          <div className="investment-table-row" key={row.id || row.productId || index}>
            <span><strong>{row.product}</strong><small>{row.status || "Activa"}</small></span>
            <span>{money(row.currentValue ?? row.amount)}</span>
            <span className={Number(row.gain ?? 0) >= 0 ? "positive" : "negative"}>{Number(row.gain ?? 0) >= 0 ? "+" : ""}{money(row.gain ?? 0)}<small>{row.gainPct ?? 0}%</small></span>
          </div>
        ))}
        {!rows.length && <div className="saved-empty">Todavía no tienes posiciones activas.</div>}
      </div>
    </div>
  );
}
