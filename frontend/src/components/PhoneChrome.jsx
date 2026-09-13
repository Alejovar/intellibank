export function StatusBar() {
  return (
    <div className="status-bar" aria-hidden="true">
      <span>9:41</span>
      <span className="status-icons"><i /><i /><i /></span>
    </div>
  );
}

export function Brand({ compact = false }) {
  const className = compact ? "brand brand-lockup compact" : "brand-lockup";
  return (
    <div className={className} aria-label="Banorte">
      <img className="brand-logo" src="/logobanorte.webp" alt="" />
      <strong>Banorte</strong>
    </div>
  );
}
