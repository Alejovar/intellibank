import { useState } from "react";
import BottomNav from "../components/BottomNav";
import ChatInput from "../components/ChatInput";
import { Brand, StatusBar } from "../components/PhoneChrome";
import { ASSISTANT_CATEGORIES } from "../data/assistantCategories";
import { useAppStore } from "../store/useAppStore";

export default function MoreScreen({ onNavigate, onStartAssistant }) {
  const [topicsOpen, setTopicsOpen] = useState(false);
  const fullName = useAppStore((s) => s.fullName);
  const activeCategories = useAppStore((s) => s.activeCategories);
  const toggleCategory = useAppStore((s) => s.toggleCategory);
  const logout = useAppStore((s) => s.logout);

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        <div><Brand compact /><div className="tagline">Cuenta y preferencias</div></div>
      </div>
      <main className="screen-body more-screen">
        <div><h1 className="screen-title">Más</h1><p className="screen-copy">Administra tu perfil y cómo te ayuda el asistente.</p></div>
        <section className="profile-card">
          <span className="profile-avatar">{fullName?.charAt(0) || "C"}</span>
          <div><strong>{fullName || "Cliente"}</strong><small>Sesión personal</small></div>
        </section>
        <section className={`settings-card topics-settings ${topicsOpen ? "open" : ""}`}>
          <button
            className="topics-toggle"
            type="button"
            onClick={() => setTopicsOpen((open) => !open)}
            aria-expanded={topicsOpen}
            aria-controls="assistant-topics"
          >
            <span className="topics-copy">
              <strong>Temas del asistente</strong>
              <small>
                {activeCategories.length
                  ? activeCategories.join(" · ")
                  : "Aún no elegiste temas"}
              </small>
            </span>
            <svg className="topics-chevron" viewBox="0 0 24 24" aria-hidden="true">
              <path d="m6.5 9 5.5 5.5L17.5 9" />
            </svg>
          </button>

          <div id="assistant-topics" className="assistant-topics-panel">
            <div className="assistant-topics-inner">
              <div className="topic-preference-list">
                {ASSISTANT_CATEGORIES.map((category) => {
                  const selected = activeCategories.includes(category.label);
                  return (
                    <button
                      key={category.id}
                      type="button"
                      className={`topic-preference ${selected ? "selected" : ""}`}
                      onClick={() => toggleCategory(category.label)}
                      aria-pressed={selected}
                    >
                      <span className="topic-preference-icon" style={{ background: category.tint }} />
                      <span className="topic-preference-copy">
                        <strong>{category.label}</strong>
                        <small>{category.hint}</small>
                      </span>
                      <span className="topic-preference-state" aria-hidden="true">
                        {selected ? "✓" : "+"}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </section>
        <button className="btn btn-ghost more-logout" onClick={logout}>Cerrar sesión</button>
      </main>
      <ChatInput
        onSend={(message) => onStartAssistant(message)}
        navigation={<BottomNav activeTab="more" onChange={onNavigate} />}
      />
    </div>
  );
}
