import { useRef, useState } from "react";

/**
 * Input siempre disponible debajo de la pantalla: texto + microfono.
 * Usa la Web Speech API con manejo de errores nativo para depuración en Android.
 */
export default function ChatInput({ onSend, disabled, navigation }) {
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  const startListening = () => {
    if (!SpeechRecognition) {
      alert("El reconocimiento de voz no está soportado en este entorno.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "es-MX";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        onSend(transcript, "voice");
      };

      recognition.onerror = (event) => {
        console.error("Error de reconocimiento de voz:", event.error);
        // Esto te dirá exactamente si es un problema de red, permisos o incompatibilidad del WebView
        alert(`Fallo en voz: ${event.error}`);
        setListening(false);
      };

      recognition.onnomatch = () => {
        console.warn("No se reconoció ninguna voz clara.");
        setListening(false);
      };

      recognition.onend = () => {
        setListening(false);
      };

      recognition.start();
      recognitionRef.current = recognition;
      setListening(true);
    } catch (err) {
      console.error("Excepción al iniciar el reconocimiento:", err);
      alert("No se pudo iniciar el micrófono.");
      setListening(false);
    }
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
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
            <i key={n} />
          ))}
          <span style={{ marginLeft: 8 }}>Escuchando…</span>
        </div>
      )}
      <div className="composer-row">
        <button
          className={`icon-btn ${listening ? "mic-active" : ""}`}
          onClick={startListening}
          disabled={disabled || !SpeechRecognition}
          title={SpeechRecognition ? "Hablar" : "Voz no soportada"}
          type="button"
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
        <button className="icon-btn send" onClick={submit} disabled={disabled} aria-label="Enviar" type="button">
          ▶
        </button>
      </div>
      {navigation}
    </div>
  );
}