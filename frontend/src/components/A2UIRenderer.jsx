import { COMPONENT_REGISTRY } from "./catalog";
import { useAppStore } from "../store/useAppStore";
import { api } from "../api/client";

/**
 * Este componente es el corazon de la regla #1 y #3 del protocolo A2UI:
 * nunca interpreta texto libre, solo un objeto ya validado por el backend
 * (schemas/a2ui.py). Para cada item en `components`, busca la funcion
 * React correspondiente en el catalogo cerrado y le pasa las props tal
 * cual llegaron. Si el nombre no existe en el catalogo, se muestra un
 * aviso de error en vez de intentar adivinar que hacer.
 */
export default function A2UIRenderer({ envelope, onSaveOrDiscard }) {
  const setLoading = useAppStore((s) => s.setLoading);
  const setError = useAppStore((s) => s.setError);
  const applyResponse = useAppStore((s) => s.applyResponse);
  const activeCategories = useAppStore((s) => s.activeCategories);
  const pushChat = useAppStore((s) => s.pushChat);

  const payload = envelope.payload;

  const handleAction = async (action) => {
    if (!action?.tool) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.executeAction(action.tool, action.args || {}, payload.id);
      applyResponse(result.response);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClarificationChoice = async (optionText) => {
    setLoading(true);
    try {
      pushChat("user", optionText);
      const result = await api.sendMessage(optionText, { activeCategories });
      applyResponse(result.response);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (payload.type === "a2ui.clarify") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
          <span style={{ width: 26, height: 26, flex: "none", borderRadius: 9, background: "var(--red-500)", transform: "rotate(45deg)" }} />
          <div className="chat-bubble assistant" style={{ maxWidth: "none" }}>{payload.question}</div>
        </div>
        {payload.options?.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {payload.options.map((opt, i) => (
              <button key={i} className="btn btn-secondary" style={{ textAlign: "left", justifyContent: "flex-start", padding: "13px 14px" }} onClick={() => handleClarificationChoice(opt)}>
                {opt}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // payload.type === "a2ui.screen"
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14, animation: "riseIn .22s ease" }}>
      <div className="eyebrow">Generada por IA</div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", padding: "0 2px", gap: 10 }}>
        <div>
          <div className="screen-title">{payload.title}</div>
          {payload.subtitle && (
            <div className="screen-copy">{payload.subtitle}</div>
          )}
        </div>
        {payload.stage_label && <span className="badge" style={{ flexShrink: 0 }}>{payload.stage_label}</span>}
      </div>

      {payload.components.map((comp) => {
        const Component = COMPONENT_REGISTRY[comp.component];
        if (!Component) {
          return (
            <div key={comp.id} className="card" style={{ borderColor: "var(--red-500)" }}>
              Componente no reconocido en el catalogo: {comp.component}
            </div>
          );
        }
        return (
          <Component
            key={comp.id}
            {...comp.props}
            actions={comp.actions || []}
            onAction={handleAction}
          />
        );
      })}

      {payload.footer_actions?.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {payload.footer_actions.map((a, i) => (
            <button key={i} className={`btn btn-${a.style || "primary"}`} onClick={() => handleAction(a)}>
              {a.label || "Continuar"}
            </button>
          ))}
        </div>
      )}

      {payload.saveable && onSaveOrDiscard && (
        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <button className="btn btn-ghost" onClick={() => onSaveOrDiscard("discard")}>Descartar</button>
          <button className="btn btn-secondary" onClick={() => onSaveOrDiscard("save")}>Guardar pantalla</button>
        </div>
      )}
    </div>
  );
}
