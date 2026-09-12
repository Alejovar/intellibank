import { Brand, StatusBar } from "./PhoneChrome";
import BottomNav from "./BottomNav";
import ChatInput from "./ChatInput";
import { useAppStore } from "../store/useAppStore";

const PAGE_COPY = {
  history: "Historial de interfaces",
  home: "Inversiones inteligentes",
  profile: "Tu perfil seguro",
};

export default function InvestmentShell({ page, onNavigate, onSend, children }) {
  const fullName = useAppStore((state) => state.fullName);
  const loading = useAppStore((state) => state.loading);
  const initial = (fullName || "Cliente").trim().charAt(0).toUpperCase();

  return (
    <div className="phone-shell investment-shell">
      <StatusBar />
      <header className="app-header shell-header">
        <div>
          <Brand compact />
          <div className="tagline">{PAGE_COPY[page] || PAGE_COPY.home}</div>
        </div>
        <div className="header-actions">
          <span className="live-agent-dot" title="Agente de inversiones disponible" />
          <button
            className="profile-mini"
            onClick={() => onNavigate("profile")}
            aria-label="Abrir perfil"
          >
            {initial}
          </button>
        </div>
      </header>

      {children}

      <ChatInput
        onSend={onSend}
        disabled={loading}
        navigation={<BottomNav activeTab={page} onChange={onNavigate} />}
      />
    </div>
  );
}
