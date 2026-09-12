const STAGE_ICON = {
  intent: "💬",
  generated: "🧩",
  interaction: "🎚️",
  confirmation: "🔐",
  result: "✅",
};

/**
 * Visualiza la maquina de estados del flujo actual: una pantalla generada
 * = un paso. El largo NO es fijo (depende de lo que pida el usuario en ese
 * momento), se va extendiendo en vivo conforme el LLM emite mas pantallas.
 * Tocar un paso anterior salta a esa pantalla dentro del hilo (no destruye
 * nada; el historial completo sigue disponible arriba).
 */
export default function FlowTrace({ steps, onJump }) {
  if (!steps || steps.length < 2) return null;

  return (
    <div className="flow-trace">
      {steps.map((step, i) => {
        const isLast = i === steps.length - 1;
        return (
          <div key={i} className={`flow-step ${isLast ? "active" : "done"}`}>
            <div className="dot-wrap" onClick={() => onJump && onJump(step.threadIndex)}>
              <div style={{ fontSize: 13, lineHeight: 1 }}>{STAGE_ICON[step.stageKind] || "•"}</div>
              <div className="dot" />
              <div className="label">{step.stageLabel}</div>
            </div>
            {!isLast && <div className="connector" />}
          </div>
        );
      })}
    </div>
  );
}
