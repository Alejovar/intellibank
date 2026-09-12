import { useEffect, useState } from "react";
import { api } from "../api/client";
import A2UIRenderer from "../components/A2UIRenderer";
import BeforeAfterPortfolio from "../components/catalog/BeforeAfterPortfolio";

const TINTS = ["#FBE9ED", "#EEF3FC", "#EAF6EE", "#FDF0E3"];

export default function SavedScreensScreen() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [replay, setReplay] = useState(null);
  const [loading, setLoading] = useState(true);
  const [replaying, setReplaying] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listInvestmentHistory()
      .then(setItems)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const openItem = async (item) => {
    setSelected(item);
    setReplay(null);
    setReplaying(true);
    try { setReplay(await api.replayInvestmentHistory(item.id)); }
    catch (err) { setError(err.message); }
    finally { setReplaying(false); }
  };

  return (
      <main className="screen-body saved-screen shell-page">
        {selected ? (
          <>
            <div className="page-title-row"><button className="inline-back" onClick={() => { setSelected(null); setReplay(null); }} aria-label="Volver al historial">‹</button><div><h1 className="screen-title">{selected.title}</h1><p className="screen-copy">“{selected.prompt || "Consulta de inversiones"}”</p></div></div>
            <A2UIRenderer envelope={selected.payload} />
            {replaying && <div className="dashboard-loading">Comparando con tus datos actuales…</div>}
            {replay?.comparison && <BeforeAfterPortfolio before={{ totalValue: replay.comparison.beforeTotalValue, totalGain: replay.comparison.beforeTotalGain }} after={{ totalValue: replay.comparison.afterTotalValue, totalGain: replay.comparison.afterTotalGain }} />}
            <div className="info-banner tip"><span>Esta interfaz se abrió sin volver a preguntar al modelo.</span></div>
          </>
        ) : (
          <>
            <div><h1 className="screen-title">Historial de interfaces</h1><p className="screen-copy">Retoma una vista anterior y compárala con tu portafolio actual.</p></div>
            {loading && <div className="dashboard-loading">Cargando historial…</div>}
            {error && <div className="info-banner warning"><span>{error}</span></div>}
            {!loading && !error && items.length === 0 && <div className="saved-empty">Todavía no hay interfaces en tu historial.<br />Pídele algo al asistente de inversiones.</div>}
            <div className="saved-list">{items.map((item, index) => <button key={item.id} className="saved-row" onClick={() => openItem(item)}><span className="saved-icon" style={{ background: TINTS[index % TINTS.length] }} /><span className="saved-copy"><strong>{item.title}</strong><small>{item.intent || "Consulta"} · {item.createdAt ? new Date(item.createdAt).toLocaleDateString("es-MX") : ""}</small></span><span className="saved-chevron">›</span></button>)}</div>
          </>
        )}
      </main>
  );
}
