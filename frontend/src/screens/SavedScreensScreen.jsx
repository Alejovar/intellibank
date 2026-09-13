import { useEffect, useState } from "react";
import { api } from "../api/client";
import BottomNav from "../components/BottomNav";
import ChatInput from "../components/ChatInput";
import { Brand, StatusBar } from "../components/PhoneChrome";
import { useAppStore } from "../store/useAppStore";

const TINTS = [
  { background: "#FBE9ED", color: "#C2002E" },
  { background: "#EEF3FC", color: "#3869B2" },
  { background: "#EAF6EE", color: "#268358" },
  { background: "#FDF0E3", color: "#B66B20" },
];

function HistoryIcon({ screen }) {
  const type = `${screen.intent || ""} ${screen.title || ""}`.toLowerCase();

  if (type.includes("invest") || type.includes("portfolio")) {
    return <svg viewBox="0 0 24 24"><path d="M4 19V5M4 19h16M7 15l4-4 3 2 5-6M16 7h3v3" /></svg>;
  }
  if (type.includes("credit") || type.includes("tarjeta")) {
    return <svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3 9h18M7 15h4" /></svg>;
  }
  if (type.includes("movement") || type.includes("expense") || type.includes("gasto")) {
    return <svg viewBox="0 0 24 24"><path d="M6 3h12v18l-2-1.5L14 21l-2-1.5L10 21l-2-1.5L6 21zM9 8h6M9 12h6M9 16h4" /></svg>;
  }
  return <svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="14" rx="3" /><path d="M8 9h3v3H8zM14.5 9h1.5M14.5 12h1.5M8 15h8M18.5 2.5v3M17 4h3" /></svg>;
}

export default function SavedScreensScreen({ onNavigate, onStartAssistant }) {
  const [screens, setScreens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const activeCategories = useAppStore((s) => s.activeCategories);
  const resetThread = useAppStore((s) => s.resetThread);
  const applyResponse = useAppStore((s) => s.applyResponse);
  const setAssistantLoading = useAppStore((s) => s.setLoading);
  const setAssistantError = useAppStore((s) => s.setError);

  useEffect(() => {
    api.listInterfaceHistory()
      .then(setScreens)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const reopenInterface = async (screen) => {
    resetThread();
    setAssistantError(null);
    setAssistantLoading(true);
    onNavigate("assistant");

    try {
      const result = await api.replayInterfaceHistory(screen.id, activeCategories);
      applyResponse(result.response);
    } catch (err) {
      setAssistantError(err.message);
    } finally {
      setAssistantLoading(false);
    }
  };

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        <div>
          <Brand compact />
          <div className="tagline history-powered">Powered by Nort<span>AI</span></div>
        </div>
      </div>

      <main className="screen-body saved-screen">
        <div>
          <h1 className="screen-title">Historial</h1>
          <p className="screen-copy">Abre una consulta anterior para que NortAI vuelva a generar la interfaz con datos actuales.</p>
        </div>
        {loading && <div className="dashboard-loading">Cargando historial…</div>}
        {error && <div className="info-banner warning"><span>{error}</span></div>}
        {!loading && !error && screens.length === 0 && (
          <div className="saved-empty">Todavía no hay interfaces en tu historial.<br />Consulta algo desde el Asistente para crear la primera.</div>
        )}
        <div className="saved-list">
          {screens.map((screen, index) => {
            const generated = screen.payload?.payload;
            const meta = generated?.stage_label || generated?.subtitle || "Interfaz generada";
            const tint = TINTS[index % TINTS.length];
            return (
              <button key={screen.id} className="saved-row" onClick={() => reopenInterface(screen)}>
                <span className="saved-icon" style={tint} aria-hidden="true"><HistoryIcon screen={screen} /></span>
                <span className="saved-copy"><strong>{screen.title}</strong><small>{meta}</small></span>
                <span className="saved-chevron">›</span>
              </button>
            );
          })}
        </div>
      </main>
      <ChatInput
        onSend={(message) => onStartAssistant(message)}
        navigation={<BottomNav activeTab="saved" onChange={onNavigate} />}
      />
    </div>
  );
}
