import { useEffect, useState } from "react";
import { api } from "../api/client";
import BottomNav from "../components/BottomNav";
import { Brand, StatusBar } from "../components/PhoneChrome";
import { useAppStore } from "../store/useAppStore";

const money = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

export default function HomeScreen({ onNavigate, onStartAssistant }) {
  const storedName = useAppStore((s) => s.fullName);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getHomeSummary().then(setSummary).catch((err) => setError(err.message));
  }, []);

  const credit = summary?.creditStatus;
  const balance = summary?.balance;
  const spent = summary?.expensesSummary?.total;
  const firstName = (summary?.user?.fullName || storedName || "Cliente").split(" ")[0];
  const creditUse = credit?.creditLimit
    ? Math.min(100, Math.round((credit.balance / credit.creditLimit) * 100))
    : 0;
  const month = new Intl.DateTimeFormat("es-MX", { month: "long" }).format(new Date());

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        <div>
          <Brand compact />
          <div className="tagline">Tu banca de todos los días</div>
        </div>
        <span className="fixed-pill">Vista personal</span>
      </div>

      <main className="screen-body home-screen">
        <div className="fixed-label"><span className="eyebrow fixed">Pantalla fija</span><span>No se adapta</span></div>
        <h1 className="screen-title">Hola {firstName},<br />¿en qué te puedo ayudar hoy?</h1>

        {error && <div className="info-banner warning"><span>{error}</span></div>}
        {!summary && !error && <div className="dashboard-loading">Cargando tus cuentas…</div>}

        {summary && (
          <>
            <section className="credit-summary">
              <div className="credit-topline">
                <div className="credit-identity">
                  <span className="mini-card" />
                  <div><strong>{credit.label}</strong><span>{credit.maskedNumber}</span></div>
                </div>
                <div className="credit-balance"><span>Saldo actual</span><strong>{money.format(credit.balance)}</strong></div>
              </div>
              <div className="progress-bar"><div style={{ width: `${creditUse}%` }} /></div>
              <div className="credit-meta"><span>Límite: {money.format(credit.creditLimit)}</span><span>Disponible: {money.format(credit.available)}</span></div>
            </section>

            <div className="home-stats">
              <div><span>{balance.accountLabel}</span><strong>{money.format(balance.balance)}</strong></div>
              <div><span>Gasto de {month}</span><strong>{money.format(spent)}</strong></div>
            </div>
          </>
        )}

        <section className="home-start">
          <div className="section-label">Empieza por aquí</div>
          <button className="adapt-card" onClick={() => onStartAssistant()}>
            <span><strong>Adapta tu interfaz</strong><small>Elige un tema o dime qué necesitas</small></span>
            <i>›</i>
          </button>
          <div className="quick-actions">
            {["Ver movimientos", "Controlar mis gastos", "Pagar mi tarjeta"].map((label) => (
              <button key={label} onClick={() => onStartAssistant(label)}>{label}</button>
            ))}
          </div>
        </section>
      </main>
      <BottomNav activeTab="home" onChange={onNavigate} />
    </div>
  );
}
