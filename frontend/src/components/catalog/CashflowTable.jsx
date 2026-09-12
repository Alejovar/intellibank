const money = (value) => (value ?? 0).toLocaleString("es-MX", {
  style: "currency", currency: "MXN", maximumFractionDigits: 0,
});

export default function CashflowTable({ transactions = [], totalDeposits = 0, totalWithdrawals = 0, totalGains = 0 }) {
  return (
    <div className="card table-card">
      <div className="card-title">Movimientos de inversión</div>
      <div className="investment-metrics cashflow-metrics"><span><small>Aportaciones</small><strong>{money(totalDeposits)}</strong></span><span><small>Retiros</small><strong>{money(totalWithdrawals)}</strong></span><span><small>Ganancias</small><strong className="positive">{money(totalGains)}</strong></span></div>
      <div className="cashflow-list">
        {transactions.map((row, index) => <div className="cashflow-row" key={row.id || index}><span><strong>{row.description}</strong><small>{row.date ? new Date(row.date).toLocaleDateString("es-MX") : ""}</small></span><b className={row.type === "withdrawal" ? "negative" : "positive"}>{row.type === "withdrawal" ? "-" : "+"}{money(Math.abs(row.amount))}</b></div>)}
        {!transactions.length && <div className="saved-empty">No hay movimientos de inversión.</div>}
      </div>
    </div>
  );
}
