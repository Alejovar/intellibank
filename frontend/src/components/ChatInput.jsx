import { useRef, useState } from "react";
import { Capacitor } from "@capacitor/core";
import { SpeechRecognition as NativeSpeechRecognition } from "@capacitor-community/speech-recognition";
import { api } from "../api/client";

/**
 * Input siempre disponible debajo de la pantalla: texto + microfono.
 * En Android nativo usa el plugin de Capacitor (el WebView no trae Web
 * Speech API). En navegador usa Web Speech API cuando esta disponible;
 * si no, graba el audio y recurre a la transcripcion del backend.
 */
export default function ChatInput({ onSend, disabled, navigation }) {
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  const isNative = Capacitor.isNativePlatform();
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const canRecordAudio = Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
  const voiceSupported = isNative || Boolean(SpeechRecognition) || canRecordAudio;

  const startNativeListening = async () => {
    try {
      const permission = await NativeSpeechRecognition.requestPermissions();
      if (permission.speechRecognition !== "granted") {
        setListening(false);
        return;
      }
      setListening(true);
      const { matches } = await NativeSpeechRecognition.start({
        language: "es-MX",
        maxResults: 1,
        prompt: "Habla ahora…",
        popup: false,
        partialResults: false,
      });
      if (matches?.[0]) onSend(matches[0], "voice");
    } catch {
      /* El usuario puede volver a intentar; no interrumpimos el chat. */
    } finally {
      setListening(false);
    }
  };

  const startListening = async () => {
    if (isNative) {
      await startNativeListening();
      return;
    }
    if (!SpeechRecognition) {
      if (!canRecordAudio) return;
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        chunksRef.current = [];
        recorder.ondataavailable = (event) => event.data.size && chunksRef.current.push(event.data);
        recorder.onstop = async () => {
          stream.getTracks().forEach((track) => track.stop());
          recorderRef.current = null;
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
        <button
          className={`icon-btn ${listening ? "mic-active" : ""}`}
          onClick={startListening}
          disabled={disabled || !voiceSupported}
          title={voiceSupported ? "Hablar" : "Voz no soportada en este navegador"}
          aria-label={voiceSupported ? "Hablar" : "Voz no disponible"}
        >
          <svg className="mic-glyph" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="8" y="2.75" width="8" height="12" rx="4" />
            <path d="M5.75 11.25v.75a6.25 6.25 0 0 0 12.5 0v-.75M12 18.25v3M8.75 21.25h6.5" />
          </svg>
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
      {navigation}
    </div>
  );
}
