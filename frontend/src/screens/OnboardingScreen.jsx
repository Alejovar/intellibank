import { useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";

// Pantallas FIJAS, no generadas por el LLM (regla del flujo #2).
const SLIDES = [
  {
    title: "Tu banco se adapta a ti",
    text: "En vez de menus fijos, describe lo que necesitas y la app construye la pantalla justo para eso.",
    icon: "✨",
  },
  {
    title: "Habla, escribe o toca",
    text: "Puedes usar botones, texto o tu voz en cualquier momento. Todo vive en el mismo lugar.",
    icon: "🎙️",
  },
  {
    title: "Preguntas antes de actuar",
    text: "Si algo no esta claro, te preguntamos primero. Nunca se ejecuta un cambio real sin tu confirmacion.",
    icon: "🤝",
  },
  {
    title: "Guarda lo que te sirve",
    text: "Cualquier pantalla que armes se puede guardar para reutilizarla despues, o descartar si ya no la necesitas.",
    icon: "💾",
  },
];

export default function OnboardingScreen() {
  const [step, setStep] = useState(0);
  const completeOnboarding = useAppStore((s) => s.completeOnboarding);

  const finish = async () => {
    try { await api.completeOnboarding(); } catch { /* demo: no bloquear si falla */ }
    completeOnboarding();
  };

  const slide = SLIDES[step];
  const isLast = step === SLIDES.length - 1;

  return (
    <div className="phone-shell">
      <div className="app-header">
        <div className="brand">Banorte AI</div>
      </div>
      <div className="screen-body" style={{ justifyContent: "center", alignItems: "center", textAlign: "center" }}>
        <div style={{ fontSize: 56 }}>{slide.icon}</div>
        <div style={{ fontSize: 20, fontWeight: 700, marginTop: 12 }}>{slide.title}</div>
        <div style={{ fontSize: 14, color: "var(--ink-600)", marginTop: 8, maxWidth: 300 }}>{slide.text}</div>

        <div style={{ display: "flex", gap: 6, marginTop: 22 }}>
          {SLIDES.map((_, i) => (
            <div key={i} style={{
              width: i === step ? 20 : 7, height: 7, borderRadius: 4,
              background: i === step ? "var(--banorte-red-500)" : "var(--line-100)",
              transition: "width 0.2s",
            }} />
          ))}
        </div>
      </div>
      <div style={{ padding: 18 }}>
        <button className="btn btn-primary" onClick={() => (isLast ? finish() : setStep(step + 1))}>
          {isLast ? "Empezar" : "Siguiente"}
        </button>
        {!isLast && (
          <button className="btn btn-ghost" style={{ marginTop: 6 }} onClick={finish}>
            Saltar
          </button>
        )}
      </div>
    </div>
  );
}
