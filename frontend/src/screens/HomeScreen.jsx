import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import InvestmentPositionCard from "../components/catalog/InvestmentPositionCard";
import A2UIRenderer from "../components/A2UIRenderer";

const money = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

export default function HomeScreen({ onStartAssistant }) {
  const storedName = useAppStore((s) => s.fullName);
  const currentEnvelope = useAppStore((s) => s.currentEnvelope);
  const thread = useAppStore((s) => s.thread);
  const loading = useAppStore((s) => s.loading);
  const error = useAppStore((s) => s.error);
  const [summary, setSummary] = useState(null);
  const [summaryError, setSummaryError] = useState(null);
  const [balanceCollapsed, setBalanceCollapsed] = useState(false);

  useEffect(() => {
    api.getInvestmentSummary().then(setSummary).catch((err) => setSummaryError(err.message));
  }, []);

  const firstName = (summary?.user?.fullName || storedName || "Cliente").split(" ")[0];
  const portfolio = summary?.portfolio;
  const performance = summary?.performance;
  const latestPrompt = [...thread].reverse().find((item) => item.kind === "chat" && item.role === "user")?.text;
  const latestAssistant = [...thread].reverse().find((item) => item.kind === "chat" && item.role === "assistant")?.text;

  return (
    <main className="screen-body home-screen">
      <section className={`balance-glass-card ${balanceCollapsed ? "collapsed" : ""}`}>
        <div className="balance-card-content" aria-hidden={balanceCollapsed}>
          <div className="balance-card-heading">
            <span>Saldo total de inversiones</span>
            {summary && <span className="trend-pill">{(performance.returnPct || 0) >= 0 ? "↗" : "↘"} {performance.returnPct || 0}%</span>}
          </div>
          <strong className="balance-total">{summary ? money.format(portfolio.totalValue || 0) : "—"}</strong>
          <div className="balance-stats">
            <span><small>Invertido</small><b>{summary ? money.format(portfolio.totalInvested || 0) : "—"}</b></span>
            <span><small>Ganancia</small><b>{summary ? money.format(portfolio.totalGain || 0) : "—"}</b></span>
            <span><small>Posiciones</small><b>{portfolio?.positions?.length || 0}</b></span>
          </div>
        </div>
        <button
          className="balance-notch"
          onClick={() => setBalanceCollapsed((value) => !value)}
          aria-expanded={!balanceCollapsed}
          aria-label={balanceCollapsed ? "Mostrar saldo total" : "Ocultar saldo total"}
        >
          <span className="notch-eye" />
          <span>{balanceCollapsed ? "Mostrar saldo" : "Ocultar"}</span>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d={balanceCollapsed ? "m5 12 5-5 5 5" : "m5 8 5 5 5-5"} /></svg>
        </button>
      </section>

      {(summaryError || error) && <div className="info-banner warning"><span>{summaryError || error}</span></div>}

      <section className={`generative-surface ${currentEnvelope ? "has-interface" : ""}`}>
        <div className="surface-heading">
          <div>
            <span className="eyebrow">Interfaz inteligente</span>
            <h1>{currentEnvelope ? "Creada para tu consulta" : `Hola ${firstName}, ¿qué quieres hacer?`}</h1>
          </div>
          <span className="a2ui-orbit" aria-label="A2UI conectado"><i />A2UI</span>
        </div>

        {latestPrompt && currentEnvelope && <p className="surface-prompt">“{latestPrompt}”</p>}

        {loading && (
          <div className="generating-state">
            <span className="agent-loader"><i /><i /><i /></span>
            <div><strong>Diseñando tu interfaz</strong><small>Consultando herramientas MCP y tu portafolio…</small></div>
          </div>
        )}

        {!loading && currentEnvelope && <A2UIRenderer envelope={currentEnvelope} />}

        {!loading && !currentEnvelope && (
          <div className="surface-empty">
            {latestAssistant && <div className="assistant-fallback-card">{latestAssistant}</div>}
            <div className="surface-visual"><i /><i /><i /></div>
            <strong>Tu espacio cambia según lo que pidas</strong>
            <p>El agente consulta tus inversiones y elige componentes seguros del catálogo.</p>
            <div className="quick-actions surface-actions">
              {["Ver mis inversiones", "¿Cuánto he ganado?", "Ingresos y egresos", "Quiero invertir"].map((label) => (
                <button key={label} onClick={() => onStartAssistant(label)}>{label}</button>
              ))}
            </div>
            {summary?.portfolio?.positions?.length > 0 && (
              <div className="default-positions">
                <div className="section-label">Vista rápida</div>
                {summary.portfolio.positions.slice(0, 2).map((position) => <InvestmentPositionCard key={position.id} {...position} />)}
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
