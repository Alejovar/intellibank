import { useState } from "react";
import { SpeechRecognition } from "@capacitor-community/speech-recognition";
import { Capacitor } from "@capacitor/core";

/**
 * Input con soporte nativo de Capacitor para Android/iOS y respaldo web.
 */
export default function ChatInput({ onSend, disabled, navigation }) {
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);

  const startListening = async () => {
    try {
      const isNative = Capacitor.isNativePlatform();

      if (isNative) {
        // Pedir permisos nativos explícitamente al sistema Android
        const permissionStatus = await SpeechRecognition.requestPermissions();
        if (permissionStatus.speechRecognition !== "granted") {
          alert("Se requieren permisos de micrófono para usar la voz.");
          return;
        }

        setListening(true);

        // Iniciar reconocimiento nativo de la comunidad Capacitor
        const result = await SpeechRecognition.start({
          language: "es-MX",
          maxResults: 1,
          prompt: "Habla ahora...",
          popup: true, // true muestra un diálogo nativo flotante muy confiable en Android
          partialResults: false,
        });

        if (result && result.matches && result.matches.length > 0) {
          const transcript = result.matches[0];
          onSend(transcript, "voice");
        }
        setListening(false);
      } else {
        // Respaldo por si se prueba en navegador web de escritorio
        const WebSpeech = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!WebSpeech) {
          alert("El reconocimiento de voz no está soportado en este navegador.");
          return;
        }
        const recognition = new WebSpeech();
        recognition.lang = "es-MX";
        recognition.onresult = (e) => {
          onSend(e.results[0][0].transcript, "voice");
          setListening(false);
        };
        recognition.onerror = (ev) => {
          alert(`Fallo en voz web: ${ev.error}`);
          setListening(false);
        };
        recognition.onend = () => setListening(false);
        setListening(true);
        recognition.start();
      }
    } catch (err) {
      console.error("Error al iniciar el reconocimiento de voz:", err);
      alert("No se pudo inicializar el micrófono.");
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
          disabled={disabled}
          title="Hablar"
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