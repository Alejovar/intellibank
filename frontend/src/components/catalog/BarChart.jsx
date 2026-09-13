import {
  BarChart as RechartsBarChart, Bar, Cell, XAxis, YAxis, Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function BarChart({ title, data = [], yLabel, insightText }) {
  const format = (value) => (value ?? 0).toLocaleString("es-MX", {
    style: "currency", currency: "MXN", maximumFractionDigits: 2,
  });

  return (
    <div className="card">
      {title && <div className="card-title">{title}</div>}
      <div style={{ width: "100%", height: 190, marginTop: title ? 8 : 0 }}>
        <ResponsiveContainer>
          <RechartsBarChart data={data} margin={{ top: 8, right: 4, bottom: 4, left: 4 }}>
            <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="var(--ink-400)" />
            <YAxis
              tick={{ fontSize: 10 }} stroke="var(--ink-400)" width={54}
              label={yLabel ? { value: yLabel, angle: -90, position: "insideLeft", fontSize: 10 } : undefined}
            />
            <Tooltip
              formatter={(value) => format(value)}
              contentStyle={{ border: "1px solid #F0E6E8", borderRadius: 13, fontFamily: "Manrope" }}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} fill="var(--red-500)">
              {data.map((item, index) => (
                <Cell key={`${item.label}-${index}`} fill={item.color || "var(--red-500)"} />
              ))}
            </Bar>
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
      {insightText && (
        <div className="info-banner warning" style={{ marginTop: 10 }}>
          <span style={{ fontWeight: 800 }}>↗</span><span>{insightText}</span>
        </div>
      )}
    </div>
  );
}
