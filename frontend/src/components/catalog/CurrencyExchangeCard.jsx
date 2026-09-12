export default function CurrencyExchangeCard({
  fromCurrency, toCurrency, amount, rate, convertedAmount, note,
  actions = [], onAction,
}) {
  const format = (value, currency) => new Intl.NumberFormat("es-MX", {
    style: "currency", currency, maximumFractionDigits: 2,
  }).format(value ?? 0);
  const confirm = () => {
    const action = actions[0];
    if (action && onAction) {
      onAction({
        ...action,
        args: {
          ...action.args, from_currency: fromCurrency, to_currency: toCurrency,
          amount, rate, converted_amount: convertedAmount,
        },
      });
    }
  };

  return (
    <div className="card">
      <div className="card-title">Conversión de divisas</div>
      <div className="option-row" style={{ cursor: "default" }}>
        <div>
          <div style={{ fontSize: 11, color: "var(--ink-500)", fontWeight: 700 }}>ENTREGAS</div>
          <div style={{ fontSize: 18, fontWeight: 800 }}>{format(amount, fromCurrency)}</div>
        </div>
        <div style={{ color: "var(--red-500)", fontWeight: 800 }}>→</div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 11, color: "var(--ink-500)", fontWeight: 700 }}>RECIBES</div>
          <div style={{ fontSize: 18, fontWeight: 800 }}>{format(convertedAmount, toCurrency)}</div>
        </div>
      </div>
      <div className="card-subtitle">1 {fromCurrency} = {rate} {toCurrency}</div>
      {note && <div className="info-banner warning"><span>i</span><span>{note}</span></div>}
      {actions[0] && (
        <button className="btn btn-primary" style={{ width: "100%", marginTop: 12 }} onClick={confirm}>
          {actions[0].label || "Confirmar cambio"}
        </button>
      )}
    </div>
  );
}
