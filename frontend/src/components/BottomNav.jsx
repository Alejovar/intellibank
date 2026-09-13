import { useEffect, useRef, useState } from "react";

const TABS = [
  { key: "home", label: "Inicio" },
  { key: "saved", label: "Historial" },
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
  const activeIndex = Math.max(TABS.findIndex((tab) => tab.key === activeTab), 0);
  const [indicatorIndex, setIndicatorIndex] = useState(activeIndex);
  const navigationTimer = useRef(null);

  useEffect(() => {
    setIndicatorIndex(activeIndex);
  }, [activeIndex]);

  useEffect(() => () => window.clearTimeout(navigationTimer.current), []);

  const navigate = (tab) => {
    const targetIndex = TABS.findIndex((item) => item.key === tab);
    if (targetIndex < 0 || targetIndex === indicatorIndex) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      onChange(tab);
      return;
    }

    window.clearTimeout(navigationTimer.current);
    setIndicatorIndex(targetIndex);
    navigationTimer.current = window.setTimeout(() => {
      onChange(tab);
    }, 380);
  };

  return (
    <nav className="bottom-nav" aria-label="Navegación principal">
      <div className="bottom-nav-items" style={{ "--active-index": indicatorIndex }}>
        <span className="nav-active-indicator" aria-hidden="true" />
        {TABS.map((tab, index) => (
          <button
            key={tab.key}
            className={`nav-item ${indicatorIndex === index ? "active" : ""}`}
            onClick={() => navigate(tab.key)}
            aria-label={tab.label}
            aria-current={activeTab === tab.key ? "page" : undefined}
            title={tab.label}
          >
            <span className="nav-icon"><NavIcon tab={tab.key} /></span>
          </button>
        ))}
      </div>
      <div className="home-indicator" aria-hidden="true" />
    </nav>
  );
}
