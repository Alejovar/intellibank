import { useCallback, useEffect, useRef, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { api } from "../api/client";
import A2UIRenderer from "../components/A2UIRenderer";
import ChatInput from "../components/ChatInput";
import FlowTrace from "../components/FlowTrace";
import { StatusBar } from "../components/PhoneChrome";
import BottomNav from "../components/BottomNav";

function AnimatedAssistantText({ text, animate, onProgress }) {
  const words = text.trim().split(/\s+/);
  const [visibleWords, setVisibleWords] = useState(animate ? 0 : words.length);

  useEffect(() => {
    if (!animate) {
      setVisibleWords(words.length);
      return undefined;
    }

    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setVisibleWords(words.length);
      return undefined;
    }

    setVisibleWords(0);
    const interval = window.setInterval(() => {
      setVisibleWords((current) => {
        if (current >= words.length) {
          window.clearInterval(interval);
          return current;
        }
        return current + 1;
      });
    }, 72);

    return () => window.clearInterval(interval);
  }, [animate, text, words.length]);

  useEffect(() => {
    onProgress?.();
  }, [onProgress, visibleWords]);

  return (
    <span className="assistant-typed-response" aria-label={text}>
      <span aria-hidden="true">{words.slice(0, visibleWords).join(" ")}</span>
      {visibleWords < words.length && <span className="typing-caret response-caret" aria-hidden="true" />}
    </span>
  );
}

function AssistantLoading() {
  return (
    <div className="assistant-loader" role="status" aria-label="Generando tu interfaz">
      <span className="assistant-loader-mark" aria-hidden="true">
        <img src="/logobanorte.webp" alt="" />
      </span>
      <span className="assistant-loader-copy" aria-hidden="true">
        <span style={{ "--word-delay": "0ms" }}>Generando</span>{" "}
        <span style={{ "--word-delay": "180ms" }}>tu</span>{" "}
        <span style={{ "--word-delay": "330ms" }}>interfaz</span>
        <span className="assistant-loader-dots"><i /><i /><i /></span>
      </span>
    </div>
  );
}

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
  const [typedLength, setTypedLength] = useState(0);
  const chatBodyRef = useRef(null);
  const sentInitial = useRef(false);
  const itemRefs = useRef({});
  const initialThreadLength = useRef(thread.length);
  const firstName = fullName?.split(" ")[0] || "Alejo";
  const greeting = `Hola, ${firstName}`;
  const question = "¿En qué puedo ayudarte hoy?";
  const typewriterLength = greeting.length + question.length;

  const scrollChatToBottom = useCallback((behavior = "auto") => {
    const chatBody = chatBodyRef.current;
    if (!chatBody) return;
    chatBody.scrollTo({ top: chatBody.scrollHeight, behavior });
  }, []);

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
    scrollChatToBottom("smooth");
  }, [scrollChatToBottom, thread]);

  useEffect(() => {
    if (thread.length > 0 || loading) return undefined;

    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setTypedLength(typewriterLength);
      return undefined;
    }

    setTypedLength(0);
    const interval = window.setInterval(() => {
      setTypedLength((current) => {
        if (current >= typewriterLength) {
          window.clearInterval(interval);
          return current;
        }
        return current + 1;
      });
    }, 58);

    return () => window.clearInterval(interval);
  }, [greeting, loading, question, thread.length, typewriterLength]);

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
        <div className="assistant-brand-lockup" aria-label="Banorte NortAI">
          <img className="assistant-brand-logo" src="/logobanorte.webp" alt="" />
          <strong className="nortai-wordmark">Nort<span>AI</span></strong>
        </div>
      </div>

      {flowTrace.length >= 2 && (
        <div style={{ padding: "10px 16px 0" }}>
          <FlowTrace steps={flowTrace} onJump={jumpToStep} />
        </div>
      )}

      <div ref={chatBodyRef} className="screen-body assistant-chat-body">
        {thread.length === 0 && !loading && (
          <div className="assistant-empty-state" aria-label={`${greeting}. ${question}`}>
            <span className="assistant-empty-kicker">Nort<span>AI</span></span>
            <h1 aria-hidden="true">
              {greeting.slice(0, typedLength)}
              {typedLength <= greeting.length && <span className="typing-caret" />}
            </h1>
            <p aria-hidden="true">
              {question.slice(0, Math.max(0, typedLength - greeting.length))}
              {typedLength > greeting.length && typedLength < typewriterLength && <span className="typing-caret" />}
            </p>
          </div>
        )}

        {thread.map((item, i) => (
          <div key={i} ref={(el) => (itemRefs.current[i] = el)}>
            {item.kind === "chat" ? (
              <div className={`chat-row ${item.role}`}>
                <div className={`chat-bubble ${item.role}`}>
                  {item.role === "assistant"
                    ? (
                      <AnimatedAssistantText
                        text={item.text}
                        animate={i >= initialThreadLength.current}
                        onProgress={scrollChatToBottom}
                      />
                    )
                    : item.text}
                </div>
              </div>
            ) : (
              <div className="generated-interface-entry">
                <A2UIRenderer
                  envelope={item.envelope}
                  onSaveOrDiscard={(action) => handleSaveOrDiscard(action, item.envelope)}
                />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-row assistant">
            <AssistantLoading />
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
      </div>

      <ChatInput
        onSend={send}
        disabled={loading}
        navigation={<BottomNav activeTab="assistant" onChange={onNavigate} />}
      />
    </div>
  );
}
