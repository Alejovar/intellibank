import { useRef, useState } from "react";

/**
 * Input siempre disponible debajo de la pantalla: texto + microfono.
 * Usa la Web Speech API cuando esta disponible (Chrome/Edge); si no,
 * cae de forma silenciosa a solo-texto (el boton de mic se deshabilita).
 */
export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  const startListening = () => {
    if (!SpeechRecognition) return;
    const recognition = new SpeechRecognition();
    recognition.lang = "es-MX";
    recognition.interimResults = false;
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      onSend(transcript, "voice");
    };
    recognition.onend = () => setListening(false);
    recognition.start();
    recognitionRef.current = recognition;
    setListening(true);
  };

  const submit = () => {
    if (!text.trim()) return;
    onSend(text.trim(), "text");
    setText("");
  };

  return (
    <div className={`input-bar ${listening ? "listening" : ""}`}>
      {listening && (
        <div className="listening-bars">
          {[0,1,2,3,4,5,6,7,8].map((n) => <i key={n} />)}
          <span style={{ marginLeft: 8 }}>Escuchando…</span>
        </div>
      )}
      <div className="composer-row">
        <button
          className={`icon-btn ${listening ? "mic-active" : ""}`}
          onClick={startListening}
          disabled={disabled || !SpeechRecognition}
          title={SpeechRecognition ? "Hablar" : "Voz no soportada en este navegador"}
        >
          <span className="mic-glyph" />
        </button>
        <input
          placeholder="Cuéntame lo que necesitas…"
          value={text}
          disabled={disabled}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button className="icon-btn send" onClick={submit} disabled={disabled} aria-label="Enviar">▶</button>
      </div>
      <div className="dock-nav" aria-hidden="true">
        {["Inicio", "Guardadas", "Asistente", "Más"].map((label, i) => (
          <span key={label} className={i === 2 ? "active" : ""}><i />{label}</span>
        ))}
      </div>
      <div className="home-indicator" aria-hidden="true" />
    </div>
  );
}
