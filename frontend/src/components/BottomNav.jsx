const TABS = [
  { key: "home", label: "Inicio" },
  { key: "saved", label: "Guardadas" },
  { key: "assistant", label: "Asistente" },
  { key: "more", label: "Más" },
];

function NavIcon({ tab }) {
  if (tab === "home") {
    return <svg viewBox="0 0 24 24"><path d="M3.5 11.1 12 4l8.5 7.1v8.4h-6v-5h-5v5h-6z" /></svg>;
  }
  if (tab === "saved") {
    return <svg viewBox="0 0 24 24"><path d="M6 3.5h12v17l-6-3.8-6 3.8z" /></svg>;
  }
  if (tab === "assistant") {
    return <svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z" /></svg>;
  }
  return <svg viewBox="0 0 24 24"><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" /></svg>;
}

export default function BottomNav({ activeTab, onChange }) {
  return (
    <nav className="bottom-nav" aria-label="Navegación principal">
      <div className="bottom-nav-items">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`nav-item ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => onChange(tab.key)}
            aria-current={activeTab === tab.key ? "page" : undefined}
          >
            <span className="nav-icon"><NavIcon tab={tab.key} /></span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
      <div className="home-indicator" aria-hidden="true" />
    </nav>
  );
}
