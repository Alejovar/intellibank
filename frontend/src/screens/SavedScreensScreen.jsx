import { useEffect, useState } from "react";
import { api } from "../api/client";
import A2UIRenderer from "../components/A2UIRenderer";
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
  const [view, setView] = useState("saved");
  const [savedScreens, setSavedScreens] = useState([]);
  const [history, setHistory] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState({ saved: true, history: true });
  const [errors, setErrors] = useState({ saved: null, history: null });
  const activeCategories = useAppStore((s) => s.activeCategories);
  const resetThread = useAppStore((s) => s.resetThread);
  const applyResponse = useAppStore((s) => s.applyResponse);
  const setAssistantLoading = useAppStore((s) => s.setLoading);
  const setAssistantError = useAppStore((s) => s.setError);

  useEffect(() => {
    api.listInterfaceHistory()
      .then(setHistory)
      .catch((err) => setErrors((current) => ({ ...current, history: err.message })))
      .finally(() => setLoading((current) => ({ ...current, history: false })));

    api.listSavedScreens()
      .then(setSavedScreens)
      .catch((err) => setErrors((current) => ({ ...current, saved: err.message })))
      .finally(() => setLoading((current) => ({ ...current, saved: false })));
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

  const screens = view === "saved" ? savedScreens : history;
  const isLoading = loading[view];
  const error = errors[view];

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        {selected && <button className="back-btn" onClick={() => setSelected(null)} aria-label="Volver a guardadas">‹</button>}
        <div>
          <Brand compact />
          <div className="tagline history-powered">
            {selected ? "Pantalla guardada" : <>Powered by Nort<span>AI</span></>}
          </div>
        </div>
        {selected && <span className="a2ui-pill" style={{ marginLeft: "auto" }}>A2UI</span>}
      </div>

      <main className="screen-body saved-screen">
        {selected ? (
          <A2UIRenderer envelope={selected.payload} />
        ) : (
          <>
            <div>
              <h1 className="screen-title">Guardadas</h1>
              <p className="screen-copy">
                {view === "saved"
                  ? "Abre exactamente las interfaces que elegiste conservar."
                  : "Repite una consulta anterior para generar la interfaz con datos actuales."}
              </p>
            </div>
            <div className="saved-tabs" role="tablist" aria-label="Pantallas guardadas e historial">
              <button type="button" role="tab" aria-selected={view === "saved"} className={view === "saved" ? "active" : ""} onClick={() => setView("saved")}>Guardadas</button>
              <button type="button" role="tab" aria-selected={view === "history"} className={view === "history" ? "active" : ""} onClick={() => setView("history")}>Historial</button>
            </div>
            {isLoading && <div className="dashboard-loading">Cargando {view === "saved" ? "pantallas" : "historial"}…</div>}
            {error && <div className="info-banner warning"><span>{error}</span></div>}
            {!isLoading && !error && screens.length === 0 && (
              <div className="saved-empty">
                {view === "saved" ? (
                  <>Todavía no tienes pantallas guardadas.<br />Puedes guardar una desde el Asistente.</>
                ) : (
                  <>Todavía no hay interfaces en tu historial.<br />Consulta algo desde el Asistente para crear la primera.</>
                )}
              </div>
            )}
            <div className="saved-list">
              {screens.map((screen, index) => {
                const generated = screen.payload?.payload;
                const meta = generated?.stage_label || generated?.subtitle || "Interfaz generada";
                const tint = TINTS[index % TINTS.length];
                const open = view === "saved" ? () => setSelected(screen) : () => reopenInterface(screen);
                return (
                  <button key={screen.id} className="saved-row" onClick={open}>
                    <span className="saved-icon" style={tint} aria-hidden="true"><HistoryIcon screen={screen} /></span>
                    <span className="saved-copy"><strong>{screen.title}</strong><small>{meta}</small></span>
                    <span className="saved-chevron">›</span>
                  </button>
                );
              })}
            </div>
          </>
        )}
      </main>
      <ChatInput
        onSend={(message) => onStartAssistant(message)}
        navigation={<BottomNav activeTab="saved" onChange={onNavigate} />}
      />
    </div>
  );
}
