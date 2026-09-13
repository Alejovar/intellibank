import { useState } from "react";

/**
 * Lista de opciones seleccionables (planes de credito, perfiles de riesgo,
 * productos de inversion, respuestas de opcion multiple en clarificaciones).
 * Al seleccionar, dispara la accion declarada por el LLM via onAction.
 */
export default function OptionsList({ options = [], selectionMode = "single", helperText, actions = [], onAction }) {
  const [selected, setSelected] = useState(
    options.find((o) => o.highlighted)?.id || null
  );

  const select = (opt, index) => {
    setSelected(opt.id);
    const action = actions.length === options.length ? actions[index] : actions[0];
    if (action && onAction) {
      onAction({ ...action, args: { ...action.args, optionId: opt.id, optionTitle: opt.title } });
    }
  };

  return (
    <div className="card">
      {helperText && <div className="card-subtitle" style={{ marginBottom: 10 }}>{helperText}</div>}
      {options.map((opt, index) => {
        const isSelected = selected === opt.id;
        return (
          <div
            key={opt.id}
            className={`option-row ${isSelected || opt.highlighted ? "highlighted" : ""}`}
            onClick={() => select(opt, index)}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div className="radio" />
              <div>
                <div style={{ fontSize: 15, fontWeight: 800 }}>
                  {opt.icon ? `${opt.icon} ` : ""}{opt.title}
                </div>
                {opt.subtitle && <div style={{ fontSize: 12, color: "var(--ink-500)", marginTop: 1 }}>{opt.subtitle}</div>}
              </div>
            </div>
            {opt.badge && <span className="badge">{opt.badge}</span>}
          </div>
        );
      })}
    </div>
  );
}
