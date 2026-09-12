const TABS = [
  { key: "history", label: "Historial" },
  { key: "home", label: "Inicio" },
  { key: "profile", label: "Perfil" },
];

function NavIcon({ tab }) {
  if (tab === "home") {
    return <svg viewBox="0 0 24 24"><path d="M3.5 11.1 12 4l8.5 7.1v8.4h-6v-5h-5v5h-6z" /></svg>;
  }
  if (tab === "history") {
    return <svg viewBox="0 0 24 24"><path d="M12 5a7 7 0 1 1-6.3 4H3l3.6-3.7L10.2 9H7.7A4.8 4.8 0 1 0 12 7.2V5Zm-1 3h2v4.1l2.8 1.7-1 1.7-3.8-2.3V8Z" /></svg>;
  }
  return <svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.5" /><path d="M5.5 20c.7-3.2 3-5 6.5-5s5.8 1.8 6.5 5z" /></svg>;
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
