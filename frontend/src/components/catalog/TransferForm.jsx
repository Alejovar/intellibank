import { useState } from "react";

export default function TransferForm({ fromAccountLabel, toLabel, amount, concept, availableAccounts = [], actions = [], onAction }) {
  const [form, setForm] = useState({
    to: toLabel || (availableAccounts[0] || ""),
    amount: amount || "",
    concept: concept || "",
  });

  const submit = () => {
    const action = actions[0];
    if (action && onAction) onAction({ ...action, args: { ...action.args, ...form } });
  };

  return (
    <div className="card">
      <div className="card-title">Nueva transferencia</div>
      <div className="card-subtitle">Desde {fromAccountLabel}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 6 }}>
        <label style={{ fontSize: 12, color: "var(--ink-600)" }}>
          Destinatario
          <select
            value={form.to}
            onChange={(e) => setForm({ ...form, to: e.target.value })}
            style={{ width: "100%", padding: 10, borderRadius: 10, border: "1px solid var(--line-100)", marginTop: 4 }}
          >
            {availableAccounts.length > 0
              ? availableAccounts.map((a) => <option key={a} value={a}>{a}</option>)
              : <option value={form.to}>{form.to || "Escribe clave/CLABE"}</option>}
          </select>
        </label>
        <label style={{ fontSize: 12, color: "var(--ink-600)" }}>
          Monto
          <input
            type="number" value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            style={{ width: "100%", padding: 10, borderRadius: 10, border: "1px solid var(--line-100)", marginTop: 4 }}
          />
        </label>
        <label style={{ fontSize: 12, color: "var(--ink-600)" }}>
          Concepto
          <input
            type="text" value={form.concept}
            onChange={(e) => setForm({ ...form, concept: e.target.value })}
            style={{ width: "100%", padding: 10, borderRadius: 10, border: "1px solid var(--line-100)", marginTop: 4 }}
          />
        </label>
        <button className="btn btn-primary" onClick={submit}>Continuar</button>
      </div>
    </div>
  );
}
