import { useState } from "react";

const money = (value) => (value ?? 0).toLocaleString("es-MX", {
  style: "currency", currency: "MXN", maximumFractionDigits: 2,
});

export default function SavingsGoalCard({
  title, targetAmount, savedAmount, progressPct, targetDate, term, tint,
  actions = [], onAction,
}) {
  const [amount, setAmount] = useState("");
  const progress = Math.max(0, Math.min(100, Number(progressPct) || 0));
  const contribute = () => {
    const action = actions[0];
    const numericAmount = Number(amount);
    if (action && onAction && numericAmount > 0) {
      onAction({ ...action, args: { ...action.args, amount: numericAmount } });
    }
  };

  return (
    <div className="card" style={{ borderTop: `4px solid ${tint || "var(--red-500)"}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "baseline" }}>
        <div className="card-title">{title}</div>
        <strong style={{ color: tint || "var(--red-500)" }}>{progress}%</strong>
      </div>
      {(term || targetDate) && (
        <div className="card-subtitle">
          {[term, targetDate && `Meta: ${targetDate}`].filter(Boolean).join(" · ")}
        </div>
      )}
      <div style={{ height: 10, borderRadius: 8, background: "#F0E6E8", overflow: "hidden", margin: "14px 0 10px" }}>
        <div style={{ width: `${progress}%`, height: "100%", borderRadius: 8, background: tint || "var(--red-500)" }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 12 }}>
        <span><small style={{ display: "block", color: "var(--ink-500)" }}>Ahorrado</small><strong>{money(savedAmount)}</strong></span>
        <span style={{ textAlign: "right" }}><small style={{ display: "block", color: "var(--ink-500)" }}>Objetivo</small><strong>{money(targetAmount)}</strong></span>
      </div>
      {actions[0] && (
        <div className="catalog-form" style={{ marginTop: 14 }}>
          <label>
            Nueva aportación
            <input
              type="number" min="0" step="100" value={amount}
              onChange={(event) => setAmount(event.target.value)}
              placeholder="Monto en MXN"
            />
          </label>
          <button className="btn btn-primary" onClick={contribute} disabled={Number(amount) <= 0}>
            {actions[0].label || "Aportar a la meta"}
          </button>
        </div>
      )}
    </div>
  );
}
