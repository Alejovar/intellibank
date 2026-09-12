import { useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { StatusBar } from "../components/PhoneChrome";

// Pantallas FIJAS, no generadas por el LLM (regla del flujo #2).
const SLIDES = [
  {
    title: "Dime qué necesitas",
    text: "Escríbelo o dilo con tu voz. No tienes que buscar entre menús interminables.",
    art: "linear-gradient(150deg,#FBE9ED,#F4DDE3)",
    artLabel: "ilustración · voz e intención",
  },
  {
    title: "La pantalla se arma sola",
    text: "El asistente elige los módulos correctos —tablas, gráficas, simuladores— y los acomoda para tu caso.",
    art: "linear-gradient(150deg,#F1E9FA,#E7EDFA)",
    artLabel: "ilustración · UI generativa",
  },
  {
    title: "Guarda lo que te sirve",
    text: "Refina la pantalla hablando con ella y guárdala para volver cuando quieras. Tus saldos siempre están fijos.",
    art: "linear-gradient(150deg,#EAF6EE,#F3F7EC)",
    artLabel: "ilustración · pantallas guardadas",
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
      <StatusBar />
      <div className="screen-body onboarding">
        <div className="onboarding-progress">
          {SLIDES.map((_, i) => (
            <i key={i} className={i <= step ? "complete" : ""} />
          ))}
        </div>
        <div className="onboarding-art" style={{ background: slide.art }}><span>{slide.artLabel}</span></div>
        <h1>{slide.title}</h1>
        <p>{slide.text}</p>
        <div className="onboarding-actions">
          {!isLast && <button className="btn btn-ghost" onClick={finish}>
            Saltar
          </button>}
          <button className="btn btn-primary" onClick={() => (isLast ? finish() : setStep(step + 1))}>
            {isLast ? "Empezar" : "Siguiente"}
          </button>
        </div>
      </div>
    </div>
  );
}
