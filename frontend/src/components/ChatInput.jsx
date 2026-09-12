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
    <div className="input-bar">
      <button
        className={`icon-btn ${listening ? "mic-active" : ""}`}
        onClick={startListening}
        disabled={disabled || !SpeechRecognition}
        title={SpeechRecognition ? "Hablar" : "Voz no soportada en este navegador"}
      >
        🎤
      </button>
      <input
        placeholder="Cuentame lo que necesitas..."
        value={text}
        disabled={disabled}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
      />
      <button className="icon-btn send" onClick={submit} disabled={disabled}>➤</button>
    </div>
  );
}
