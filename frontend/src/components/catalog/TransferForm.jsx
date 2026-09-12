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
      <div className="catalog-form">
        <label>
          Destinatario
          <select
            value={form.to}
            onChange={(e) => setForm({ ...form, to: e.target.value })}
          >
            {availableAccounts.length > 0
              ? availableAccounts.map((a) => <option key={a} value={a}>{a}</option>)
              : <option value={form.to}>{form.to || "Escribe clave/CLABE"}</option>}
          </select>
        </label>
        <label>
          Monto
          <input
            type="number" value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
          />
        </label>
        <label>
          Concepto
          <input
            type="text" value={form.concept}
            onChange={(e) => setForm({ ...form, concept: e.target.value })}
          />
        </label>
        <button className="btn btn-primary" onClick={submit}>Continuar</button>
      </div>
    </div>
  );
}
