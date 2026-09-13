import { useEffect, useState } from "react";
import { api } from "../api/client";
import BottomNav from "../components/BottomNav";
import ChatInput from "../components/ChatInput";
import { Brand, StatusBar } from "../components/PhoneChrome";
import { useAppStore } from "../store/useAppStore";

const money = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

const HOME_ACTIONS = [
  { key: "transfer", label: "Transferir" },
  { key: "card", label: "Prender / apagar tarjeta" },
  { key: "withdraw", label: "Retiro sin tarjeta" },
  { key: "statement", label: "Estado de cuenta" },
];

function ActionIcon({ type }) {
  if (type === "transfer") {
    return <svg viewBox="0 0 24 24"><path d="M4 7.5h13m0 0-3.25-3.25M17 7.5l-3.25 3.25M20 16.5H7m0 0 3.25-3.25M7 16.5l3.25 3.25" /></svg>;
  }
  if (type === "card") {
    return <svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3 9h18M12 12.25v3.5M9.8 13.2a3 3 0 1 0 4.4 0" /></svg>;
  }
  if (type === "withdraw") {
    return <svg viewBox="0 0 24 24"><rect x="4" y="3" width="16" height="18" rx="3" /><path d="M8 7h8M12 10v7m0 0-3-3m3 3 3-3" /></svg>;
  }
  return <svg viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6zM15 3v4h4M9 11h6M9 15h6" /></svg>;
}

export default function HomeScreen({ onNavigate, onStartAssistant }) {
  const storedName = useAppStore((s) => s.fullName);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getHomeSummary().then(setSummary).catch((err) => setError(err.message));
  }, []);

  const credit = summary?.creditStatus;
  const investments = summary?.investmentStats;
  const firstName = (summary?.user?.fullName || storedName || "Cliente").split(" ")[0];
  const investmentYield = investments?.gainPct ?? 0;

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header plain-header">
        <div>
          <Brand compact />
          <div className="tagline">El banco fuerte de México</div>
        </div>
        <span className="powered-pill">Powered by Nort<span>AI</span></span>
      </div>

      <main className="screen-body home-screen">
        <h1 className="screen-title">Bienvenido, {firstName}</h1>

        {error && <div className="info-banner warning"><span>{error}</span></div>}
        {!summary && !error && <div className="dashboard-loading">Cargando tus cuentas…</div>}

        {summary && (
          <section className="credit-summary">
            <div className="credit-overview">
              <div className="credit-account">
                <div className="credit-identity">
                  <span className="mini-card" />
                  <div><strong>{credit.label}</strong><span>{credit.maskedNumber}</span></div>
                </div>
                <div className="credit-balance">
                  <span>Saldo actual</span>
                  <strong>{money.format(credit.balance)}</strong>
                </div>
              </div>

              <div className="financial-overview">
                <div className="overview-metric investment-overview">
                  <span>Estadísticas de inversiones</span>
                  <strong>{money.format(investments.totalValue)}</strong>
                  <small className={investmentYield >= 0 ? "positive" : "negative"}>
                    {investmentYield >= 0 ? "+" : ""}{investmentYield.toFixed(1)}% de rendimiento
                  </small>
                </div>
              </div>
            </div>
          </section>
        )}

        <section className="home-start">
          <div className="section-label">Empieza por aquí</div>
          <div className="home-actions">
            {HOME_ACTIONS.map((action) => (
              <div className="home-action" key={action.key}>
                <span className="home-action-main">
                  <span className="home-action-icon" aria-hidden="true"><ActionIcon type={action.key} /></span>
                  <strong>{action.label}</strong>
                </span>
                <span className="home-action-arrow" aria-hidden="true">›</span>
              </div>
            ))}
          </div>
        </section>
      </main>
      <ChatInput
        onSend={(message) => onStartAssistant(message)}
        navigation={<BottomNav activeTab="home" onChange={onNavigate} />}
      />
    </div>
  );
}
