export function StatusBar() {
  return (
    <div className="status-bar" aria-hidden="true">
      <span>9:41</span>
      <span className="status-icons"><i /><i /><i /></span>
    </div>
  );
}

export function Brand({ compact = false }) {
  return compact ? (
    <div className="brand">Banca <span className="brand-accent">AI</span></div>
  ) : (
    <strong>Banca <span className="brand-accent">AI</span></strong>
  );
}
