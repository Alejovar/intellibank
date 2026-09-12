import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";

export default function ExpenseChart({ chartType = "donut", data = [], total, centerLabel, insightText }) {
  const fmt = (n) => (n ?? 0).toLocaleString("es-MX", { style: "currency", currency: "MXN" });

  return (
    <div className="card">
      {chartType === "donut" ? (
        <>
          <div className="card-title">{centerLabel || "Tus gastos"}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ width: 130, height: 130, position: "relative", flexShrink: 0 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={data} dataKey="value" nameKey="label" innerRadius={38} outerRadius={60} paddingAngle={2}>
                    {data.map((d, i) => <Cell key={i} fill={d.color || "#ccc"} />)}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div style={{
                position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center", pointerEvents: "none",
              }}>
                <div style={{ fontSize: 10, color: "var(--ink-600)" }}>Total</div>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{fmt(total)}</div>
              </div>
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
              {data.map((d, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 4, background: d.color }} />
                    {d.label}
                  </span>
                  <span style={{ fontWeight: 600 }}>{d.pct}%</span>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <>
          {centerLabel && <div className="card-title">{centerLabel}</div>}
          <div style={{ width: "100%", height: 160 }}>
            <ResponsiveContainer>
              <LineChart data={data.map((d) => ({ x: d.label ?? d.x, y: d.value ?? d.y }))}>
                <XAxis dataKey="x" tick={{ fontSize: 11 }} stroke="var(--ink-400)" />
                <YAxis hide />
                <Tooltip formatter={(v) => fmt(v)} />
                <Line type="monotone" dataKey="y" stroke="var(--banorte-red-500)" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
      {insightText && (
        <div className="info-banner warning" style={{ marginTop: 10 }}>
          <span>📈</span><span>{insightText}</span>
        </div>
      )}
    </div>
  );
}
