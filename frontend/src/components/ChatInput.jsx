import { useRef, useState } from "react";
import { api } from "../api/client";

/**
 * Compositor persistente del shell: texto, dictado y envio. Usa la API
 * de voz nativa cuando existe y recurre a la transcripcion del backend.
 */
export default function ChatInput({ onSend, disabled, navigation }) {
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const canRecordAudio = Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);

  const startListening = async () => {
    if (!SpeechRecognition && !canRecordAudio) return;
    if (listening) {
      recognitionRef.current?.stop?.();
      recorderRef.current?.stop?.();
      return;
    }
    if (!SpeechRecognition) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        chunksRef.current = [];
        recorder.ondataavailable = (event) => event.data.size && chunksRef.current.push(event.data);
        recorder.onstop = async () => {
          stream.getTracks().forEach((track) => track.stop());
          setListening(false);
          try {
            const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
            const result = await api.transcribeAudio(blob);
            if (result.text) onSend(result.text, "voice");
          } catch { /* El usuario puede volver a intentar; no interrumpimos el chat. */ }
        };
        recorder.start();
        recorderRef.current = recorder;
        setListening(true);
      } catch { setListening(false); }
      return;
    }
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
        <input
          placeholder="Habla con tu asistente…"
          value={text}
          disabled={disabled}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button
          className={`icon-btn mic ${listening ? "mic-active" : ""}`}
          onClick={startListening}
          disabled={disabled || (!SpeechRecognition && !canRecordAudio)}
          title={SpeechRecognition || canRecordAudio ? "Dictado rápido" : "Voz no soportada en este navegador"}
          aria-label={listening ? "Detener dictado" : "Iniciar dictado rápido"}
        >
          <span className="mic-glyph" />
        </button>
        <button className="icon-btn send" onClick={submit} disabled={disabled || !text.trim()} aria-label="Enviar">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 4 17 8-17 8 3.2-7H14v-2H7.2L4 4Z" /></svg>
        </button>
      </div>
      {navigation}
    </div>
  );
}
