export default function MarketWatchlist({ title, items = [], actions = [], onAction }) {
  const select = (item) => {
    const action = actions[0];
    if (action && onAction) {
      onAction({ ...action, args: { ...action.args, symbol: item.symbol } });
    }
  };

  const formatPrice = (item) => new Intl.NumberFormat("es-MX", {
    style: item.currency ? "currency" : "decimal",
    currency: item.currency || "MXN",
    maximumFractionDigits: item.price < 10 ? 4 : 2,
  }).format(item.price ?? 0);

  return (
    <div className="card">
      {title && <div className="card-title" style={{ marginBottom: 10 }}>{title}</div>}
      {items.map((item) => {
        const change = Number(item.changePct || 0);
        return (
          <div
            key={item.symbol}
            className="option-row"
            role={actions[0] ? "button" : undefined}
            tabIndex={actions[0] ? 0 : undefined}
            onClick={() => select(item)}
            onKeyDown={(event) => event.key === "Enter" && select(item)}
          >
            <div>
              <div style={{ fontSize: 15, fontWeight: 800 }}>{item.symbol}</div>
              <div style={{ fontSize: 12, color: "var(--ink-500)", marginTop: 1 }}>{item.name}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 15, fontWeight: 800 }}>{formatPrice(item)}</div>
              <div style={{ fontSize: 12, fontWeight: 800, color: change >= 0 ? "var(--ok-600)" : "var(--red-500)" }}>
                {change >= 0 ? "+" : ""}{change.toFixed(2)}%
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
