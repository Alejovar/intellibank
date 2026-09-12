import { useEffect, useRef, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { api } from "../api/client";
import A2UIRenderer from "../components/A2UIRenderer";
import ChatInput from "../components/ChatInput";
import FlowTrace from "../components/FlowTrace";
import { Brand, StatusBar } from "../components/PhoneChrome";

export default function AssistantScreen({ initialMessage }) {
  const thread = useAppStore((s) => s.thread);
  const flowTrace = useAppStore((s) => s.flowTrace);
  const pushChat = useAppStore((s) => s.pushChat);
  const applyResponse = useAppStore((s) => s.applyResponse);
  const activeCategories = useAppStore((s) => s.activeCategories);
  const loading = useAppStore((s) => s.loading);
  const setLoading = useAppStore((s) => s.setLoading);
  const error = useAppStore((s) => s.error);
  const setError = useAppStore((s) => s.setError);
  const logout = useAppStore((s) => s.logout);

  const [toast, setToast] = useState(null);
  const bottomRef = useRef(null);
  const sentInitial = useRef(false);
  const itemRefs = useRef({});

  const jumpToStep = (threadIndex) => {
    itemRefs.current[threadIndex]?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const send = async (message, inputMode = "text") => {
    setError(null);
    pushChat("user", message);
    setLoading(true);
    try {
      const result = await api.sendMessage(message, { inputMode, activeCategories });
      applyResponse(result.response);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialMessage && !sentInitial.current) {
      sentInitial.current = true;
      send(initialMessage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread]);

  const handleSaveOrDiscard = async (action, envelope) => {
    if (action === "save") {
      try {
        await api.saveScreen(envelope.payload.title, envelope);
        setToast("Pantalla guardada. Podras reutilizarla despues.");
      } catch (e) {
        setError(e.message);
      }
    } else {
      setToast("Pantalla descartada.");
    }
    setTimeout(() => setToast(null), 2500);
  };

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        <button className="back-btn" aria-label="Volver">‹</button>
        <div>
          <Brand compact />
          <div className="tagline">Pantalla generada</div>
        </div>
        <span className="a2ui-pill" style={{ marginLeft: "auto" }}>A2UI</span>
        <button className="back-btn" onClick={logout} title="Cerrar sesión" aria-label="Cerrar sesión">⎋</button>
      </div>

      {flowTrace.length >= 2 && (
        <div style={{ padding: "10px 16px 0" }}>
          <FlowTrace steps={flowTrace} onJump={jumpToStep} />
        </div>
      )}

      <div className="screen-body">
        {thread.length === 0 && !loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <span className="eyebrow" style={{ color: "var(--ink-600)", background: "#F2ECED" }}>Pantalla fija</span>
            <h1 className="screen-title">Hola Daniela,<br />¿en qué te puedo ayudar hoy?</h1>
            <div className="card" style={{ background: "var(--red-050)" }}>
              <div className="card-title">Adapta tu interfaz</div>
              <div className="card-subtitle" style={{ marginBottom: 0 }}>Dime qué necesitas y armaré la pantalla adecuada.</div>
            </div>
          </div>
        )}

        {thread.map((item, i) => (
          <div key={i} ref={(el) => (itemRefs.current[i] = el)}>
            {item.kind === "chat" ? (
              <div style={{ display: "flex" }}>
                <div className={`chat-bubble ${item.role}`}>{item.text}</div>
              </div>
            ) : (
              <A2UIRenderer
                envelope={item.envelope}
                onSaveOrDiscard={(action) => handleSaveOrDiscard(action, item.envelope)}
              />
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex" }}>
            <div className="chat-bubble assistant">Construyendo tu pantalla…</div>
          </div>
        )}
        {error && (
          <div className="info-banner warning">
            <span>⚠️</span><span>{error}</span>
          </div>
        )}
        {toast && (
          <div className="info-banner tip"><span>✅</span><span>{toast}</span></div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={send} disabled={loading} />
    </div>
  );
}
