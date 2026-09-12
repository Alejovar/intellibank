import { useEffect, useState } from "react";
import { api } from "../api/client";
import A2UIRenderer from "../components/A2UIRenderer";
import BottomNav from "../components/BottomNav";
import { Brand, StatusBar } from "../components/PhoneChrome";

const TINTS = ["#FBE9ED", "#EEF3FC", "#EAF6EE", "#FDF0E3"];

export default function SavedScreensScreen({ onNavigate }) {
  const [screens, setScreens] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listSavedScreens()
      .then(setScreens)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        {selected && <button className="back-btn" onClick={() => setSelected(null)} aria-label="Volver a guardadas">‹</button>}
        <div>
          <Brand compact />
          <div className="tagline">{selected ? "Pantalla guardada" : "Tu colección"}</div>
        </div>
        {selected && <span className="a2ui-pill" style={{ marginLeft: "auto" }}>A2UI</span>}
      </div>

      <main className="screen-body saved-screen">
        {selected ? (
          <A2UIRenderer envelope={selected.payload} />
        ) : (
          <>
            <div>
              <h1 className="screen-title">Mis pantallas guardadas</h1>
              <p className="screen-copy">Las interfaces que guardaste se vuelven a abrir con datos frescos.</p>
            </div>
            {loading && <div className="dashboard-loading">Cargando pantallas…</div>}
            {error && <div className="info-banner warning"><span>{error}</span></div>}
            {!loading && !error && screens.length === 0 && (
              <div className="saved-empty">Todavía no tienes pantallas guardadas.<br />Puedes guardar una desde el Asistente.</div>
            )}
            <div className="saved-list">
              {screens.map((screen, index) => {
                const generated = screen.payload?.payload;
                const meta = generated?.stage_label || generated?.subtitle || "Pantalla generada";
                return (
                  <button key={screen.id} className="saved-row" onClick={() => setSelected(screen)}>
                    <span className="saved-icon" style={{ background: TINTS[index % TINTS.length] }} />
                    <span className="saved-copy"><strong>{screen.title}</strong><small>{meta}</small></span>
                    <span className="saved-chevron">›</span>
                  </button>
                );
              })}
            </div>
          </>
        )}
      </main>
      <BottomNav activeTab="saved" onChange={onNavigate} />
    </div>
  );
}
