import { useState } from "react";

export default function SharedExpenseList({ title, people = [], expenses = [], actions = [], onAction }) {
  const [newExpense, setNewExpense] = useState({ desc: "", amount: "", paidBy: people[0]?.name || "" });
  const fmt = (n) => (n ?? 0).toLocaleString("es-MX", { style: "currency", currency: "MXN" });

  const addExpense = () => {
    const addAction = actions.find((a) => a.tool === "add_shared_expense") || actions[0];
    if (addAction && onAction) {
      onAction({
        ...addAction,
        args: { ...addAction.args, desc: newExpense.desc, amount: Number(newExpense.amount), paid_by: newExpense.paidBy },
      });
      setNewExpense({ desc: "", amount: "", paidBy: people[0]?.name || "" });
    }
  };

  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
        {people.map((p, i) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5 }}>
            <span>{p.name}</span>
            <span style={{ color: p.owes - p.paid > 0 ? "#b3261e" : "var(--ok-600)", fontWeight: 600 }}>
              {p.owes - p.paid > 0 ? `Debe ${fmt(p.owes - p.paid)}` : "Al corriente"}
            </span>
          </div>
        ))}
      </div>

      {expenses.length > 0 && (
        <div style={{ marginTop: 12, borderTop: "1px solid var(--line-100)", paddingTop: 10 }}>
          <div style={{ fontSize: 12, color: "var(--ink-600)", marginBottom: 6 }}>Gastos registrados</div>
          {expenses.map((e, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "4px 0" }}>
              <span>{e.desc} <span style={{ color: "var(--ink-600)" }}>· pago {e.paidBy}</span></span>
              <span style={{ fontWeight: 600 }}>{fmt(e.amount)}</span>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
        <input
          placeholder="Descripcion del gasto" value={newExpense.desc}
          onChange={(e) => setNewExpense({ ...newExpense, desc: e.target.value })}
          style={{ padding: 10, borderRadius: 10, border: "1px solid var(--line-100)" }}
        />
        <div style={{ display: "flex", gap: 8 }}>
          <input
            type="number" placeholder="Monto" value={newExpense.amount}
            onChange={(e) => setNewExpense({ ...newExpense, amount: e.target.value })}
            style={{ flex: 1, padding: 10, borderRadius: 10, border: "1px solid var(--line-100)" }}
          />
          <select
            value={newExpense.paidBy}
            onChange={(e) => setNewExpense({ ...newExpense, paidBy: e.target.value })}
            style={{ flex: 1, padding: 10, borderRadius: 10, border: "1px solid var(--line-100)" }}
          >
            {people.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
          </select>
        </div>
        <button className="btn btn-secondary" onClick={addExpense}>Agregar gasto</button>
      </div>
    </div>
  );
}
