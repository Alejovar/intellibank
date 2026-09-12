import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import ChatInput from "../components/ChatInput";
import { Brand, StatusBar } from "../components/PhoneChrome";

const CATEGORIES = [
  { id: "banca_personal", label: "Banca personal", hint: "Cuentas, movimientos, control de gasto", tint: "#FBE9ED", subtemas: ["Mis cuentas", "Movimientos", "Control de gasto"] },
  { id: "inversiones", label: "Inversiones", hint: "Perfilamiento, portafolios, simulación", tint: "#EEF3FC", subtemas: ["Perfilamiento", "Portafolios", "Simulación"] },
  { id: "credito", label: "Crédito", hint: "Precalificación, amortización, refinanciamiento", tint: "#FDF0E3", subtemas: ["Precalificación", "Amortización", "Refinanciamiento"] },
  { id: "pagos", label: "Pagos", hint: "Transferencias, cobros, conciliación", tint: "#EAF6EE", subtemas: ["Transferencias", "Cobros", "Conciliación"] },
  { id: "seguros", label: "Seguros", hint: "Cotización, coberturas, siniestros", tint: "#F6F2FA", subtemas: ["Cotización", "Coberturas", "Siniestros"] },
  { id: "educacion", label: "Educación financiera", hint: "Diagnóstico, metas, hábitos", tint: "#F2ECED", subtemas: ["Diagnóstico", "Metas", "Hábitos"] },
];

/**
 * Seleccion de categoria base con revelacion progresiva: en vez de mostrar
 * de una vez todos los subtemas de las 6 categorias (saturando al usuario
 * como una app bancaria tradicional), solo se expanden los subtemas de la
 * categoria que se toca. El usuario tambien puede saltarse todo esto
 * describiendo lo que quiere por texto o voz.
 */
export default function CategorySelection({ onContinue }) {
  const [expanded, setExpanded] = useState(null);
  const [selectedSubtemas, setSelectedSubtemas] = useState([]);
  const toggleCategory = useAppStore((s) => s.toggleCategory);
  const activeCategories = useAppStore((s) => s.activeCategories);

  const handleChipClick = (cat) => {
    toggleCategory(cat.label);
    setExpanded(expanded === cat.id ? null : cat.id);
  };

  const toggleSubtema = (sub) => {
    setSelectedSubtemas((prev) =>
      prev.includes(sub) ? prev.filter((s) => s !== sub) : [...prev, sub]
    );
  };

  const handleFreeInput = (text) => {
    onContinue(text);
  };

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        <button className="back-btn" aria-label="Volver">‹</button>
        <div>
          <Brand compact />
          <div className="tagline">Dime qué necesitas</div>
        </div>
        <span className="a2ui-pill" style={{ marginLeft: "auto" }}>A2UI</span>
      </div>
      <div className="screen-body">
        <div>
          <h1 className="screen-title">¿Sobre qué quieres trabajar?</h1>
          <p className="screen-copy">Elige uno o varios temas, o descríbelo con tus palabras abajo.</p>
        </div>
        <div className="category-list">
          {CATEGORIES.map((cat) => (
            <div key={cat.id} className={`category-item ${expanded === cat.id ? "open" : ""}`}>
              <button className="category-row" onClick={() => handleChipClick(cat)}>
                <span className="category-icon" style={{ background: cat.tint }} />
                <span style={{ flex: 1 }}>
                  <strong style={{ display: "block", fontSize: 14.5 }}>{cat.label}</strong>
                  <span style={{ display: "block", marginTop: 1, color: "var(--ink-500)", fontSize: 12 }}>{cat.hint}</span>
                </span>
                <span className="category-chevron">›</span>
              </button>
              {expanded === cat.id && (
                <div className="category-subs">
                  {cat.subtemas.map((sub) => (
                    <button key={sub} className={`category-chip ${selectedSubtemas.includes(sub) ? "selected" : ""}`} onClick={() => toggleSubtema(sub)}>{sub}</button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        {(activeCategories.length > 0 || selectedSubtemas.length > 0) && (
          <button
            className="btn btn-primary"
            onClick={() =>
              onContinue(
                [...activeCategories, ...selectedSubtemas].join(", ")
              )
            }
          >
            Continuar
          </button>
        )}
        <div style={{ border: "1px dashed #E7D4D8", borderRadius: 16, padding: "13px 14px", background: "#FDFAFA", color: "var(--ink-600)", fontSize: 12, lineHeight: 1.5 }}>
          O dilo tú: <strong style={{ color: "var(--red-500)" }}>“quiero pagar menos intereses de mi tarjeta”</strong>
        </div>
      </div>
      <ChatInput onSend={handleFreeInput} />
    </div>
  );
}
