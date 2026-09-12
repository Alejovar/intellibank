const ICONS = { tip: "💡", warning: "⚠️", info: "ℹ️", trend: "📈" };

export default function InfoBanner({ icon = "info", title, text }) {
  const cls = icon === "warning" ? "warning" : icon === "tip" ? "tip" : "";
  return (
    <div className={`info-banner ${cls}`}>
      <span>{ICONS[icon] || "ℹ️"}</span>
      <span>{title && <strong>{title} </strong>}{text}</span>
    </div>
  );
}
