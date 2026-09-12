import { useState } from "react";
import { LineChart, Line, XAxis, ResponsiveContainer, Tooltip, Dot } from "recharts";

export default function PaymentSlider({ label, min, max, step = 1, value, unit = "", helperText, chart, actions = [], onAction }) {
  const [val, setVal] = useState(value);

  const commit = (v) => {
    const action = actions[0];
    if (action && onAction) {
      onAction({ ...action, args: { ...action.args, value: v } });
    }
  };

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div className="card-title">{label}</div>
        <div style={{ fontSize: 18, fontWeight: 700 }}>{unit}{val}</div>
      </div>
      {helperText && <div className="card-subtitle">{helperText}</div>}
      <input
        type="range" min={min} max={max} step={step} value={val}
        onChange={(e) => setVal(Number(e.target.value))}
        onMouseUp={(e) => commit(Number(e.target.value))}
        onTouchEnd={(e) => commit(Number(e.target.value))}
        style={{ width: "100%", accentColor: "var(--banorte-red-500)", marginTop: 10 }}
      />
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--ink-600)" }}>
        <span>{min}</span><span>{max}</span>
      </div>
      {chart?.data?.length > 0 && (
        <div style={{ width: "100%", height: 140, marginTop: 12 }}>
          <ResponsiveContainer>
            <LineChart data={chart.data}>
              <XAxis dataKey="x" tick={{ fontSize: 10 }} stroke="var(--ink-400)" label={{ value: chart.xLabel, position: "insideBottom", fontSize: 10, dy: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="y" stroke="var(--banorte-red-500)" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
