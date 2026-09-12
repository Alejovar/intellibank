const ICONS = { tip: "✓", warning: "!", info: "i", trend: "↗" };

export default function InfoBanner({ icon = "info", title, text }) {
  const cls = icon === "warning" ? "warning" : icon === "tip" ? "tip" : "";
  return (
    <div className={`info-banner ${cls}`}>
      <span style={{ width: 28, height: 28, flex: "none", display: "grid", placeItems: "center", borderRadius: 9, background: "rgba(255,255,255,.55)", fontWeight: 800 }}>{ICONS[icon] || "i"}</span>
      <span>{title && <strong>{title} </strong>}{text}</span>
    </div>
  );
}
