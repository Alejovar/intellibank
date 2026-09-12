import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";

export default function ExpenseChart({ chartType = "donut", data = [], total, centerLabel, insightText }) {
  const fmt = (n) => (n ?? 0).toLocaleString("es-MX", { style: "currency", currency: "MXN" });
  const palette = ["#C2002E", "#2D6FE0", "#8B5CF6", "#B9AFB2"];

  return (
    <div className="card">
      {chartType === "donut" ? (
        <>
          <div className="card-title">{centerLabel || "Tus gastos"}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ width: 118, height: 118, position: "relative", flexShrink: 0 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={data} dataKey="value" nameKey="label" innerRadius={39} outerRadius={59} paddingAngle={0}>
                    {data.map((d, i) => <Cell key={i} fill={d.color || palette[i % palette.length]} />)}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div style={{
                position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center", pointerEvents: "none",
              }}>
                <div style={{ fontSize: 10.5, color: "var(--ink-500)", fontWeight: 700 }}>Total</div>
                <div style={{ fontSize: 15, fontWeight: 800, letterSpacing: "-.02em" }}>{fmt(total)}</div>
              </div>
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 9 }}>
              {data.map((d, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ width: 9, height: 9, borderRadius: 9, background: d.color || palette[i % palette.length] }} />
                    {d.label}
                  </span>
                  <span style={{ fontWeight: 800, color: "var(--ink-600)" }}>{d.pct}%</span>
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
              <Tooltip formatter={(v) => fmt(v)} contentStyle={{ border: "1px solid #F0E6E8", borderRadius: 13, fontFamily: "Manrope" }} />
              <Line type="monotone" dataKey="y" stroke="var(--red-500)" strokeWidth={2.5} dot={{ r: 3, fill: "#C2002E" }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
      {insightText && (
        <div className="info-banner warning" style={{ marginTop: 10 }}>
          <span style={{ fontWeight: 800 }}>↗</span><span>{insightText}</span>
        </div>
      )}
    </div>
  );
}
