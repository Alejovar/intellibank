import { useEffect, useRef, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { api } from "../api/client";
import A2UIRenderer from "../components/A2UIRenderer";
import ChatInput from "../components/ChatInput";
import FlowTrace from "../components/FlowTrace";
import { Brand, StatusBar } from "../components/PhoneChrome";
import BottomNav from "../components/BottomNav";

export default function AssistantScreen({ initialMessage, onInitialMessageConsumed, onNavigate }) {
  const thread = useAppStore((s) => s.thread);
  const flowTrace = useAppStore((s) => s.flowTrace);
  const pushChat = useAppStore((s) => s.pushChat);
  const applyResponse = useAppStore((s) => s.applyResponse);
  const activeCategories = useAppStore((s) => s.activeCategories);
  const loading = useAppStore((s) => s.loading);
  const setLoading = useAppStore((s) => s.setLoading);
  const error = useAppStore((s) => s.error);
  const setError = useAppStore((s) => s.setError);
  const fullName = useAppStore((s) => s.fullName);

  const [toast, setToast] = useState(null);
  const chatBodyRef = useRef(null);
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
      onInitialMessageConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage]);

  useEffect(() => {
    const chatBody = chatBodyRef.current;
    if (!chatBody) return;
    chatBody.scrollTo({ top: chatBody.scrollHeight, behavior: "smooth" });
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
      <div className="app-header assistant-header">
        <span className="assistant-header-balance" aria-hidden="true" />
        <Brand compact />
        <strong className="nortai-wordmark">Nort<span>AI</span></strong>
      </div>

      {flowTrace.length >= 2 && (
        <div style={{ padding: "10px 16px 0" }}>
          <FlowTrace steps={flowTrace} onJump={jumpToStep} />
        </div>
      )}

      <div ref={chatBodyRef} className="screen-body assistant-chat-body">
        {thread.length === 0 && !loading && (
          <div className="assistant-empty-state">
            <div className="assistant-spark" aria-hidden="true">
              <svg viewBox="0 0 32 32"><path d="M16 3c1.2 7.4 5.6 11.8 13 13-7.4 1.2-11.8 5.6-13 13C14.8 21.6 10.4 17.2 3 16 10.4 14.8 14.8 10.4 16 3Z" /></svg>
            </div>
            <span className="assistant-empty-kicker">Nort<span>AI</span></span>
            <h1>Hola, {fullName?.split(" ")[0] || "Alejo"}</h1>
            <p>¿En qué puedo ayudarte hoy?</p>
            <small>Escribe o usa el micrófono. Te responderé con mensajes e interfaces interactivas.</small>
          </div>
        )}

        {thread.map((item, i) => (
          <div key={i} ref={(el) => (itemRefs.current[i] = el)}>
            {item.kind === "chat" ? (
              <div className={`chat-row ${item.role}`}>
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
          <div className="chat-row assistant">
            <div className="chat-bubble assistant">Construyendo tu pantalla…</div>
          </div>
        )}
        {error && (
          <div className="info-banner warning">
            <span>{error}</span>
          </div>
        )}
        {toast && (
          <div className="info-banner tip"><span>{toast}</span></div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput
        onSend={send}
        disabled={loading}
        navigation={<BottomNav activeTab="assistant" onChange={onNavigate} />}
      />
    </div>
  );
}
