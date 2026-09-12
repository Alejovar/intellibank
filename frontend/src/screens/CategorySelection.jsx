import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import ChatInput from "../components/ChatInput";

const CATEGORIES = [
  { id: "banca_personal", label: "Banca personal", subtemas: ["Cuentas", "Movimientos", "Control de gasto"] },
  { id: "inversiones", label: "Inversiones", subtemas: ["Perfilamiento", "Portafolios", "Simulacion"] },
  { id: "credito", label: "Credito", subtemas: ["Precalificacion", "Amortizacion", "Refinanciamiento"] },
  { id: "pagos", label: "Pagos", subtemas: ["Transferencias", "Cobros", "Conciliacion"] },
  { id: "seguros", label: "Seguros", subtemas: ["Cotizacion", "Coberturas", "Siniestros"] },
  { id: "educacion", label: "Educacion financiera", subtemas: ["Diagnostico", "Metas", "Habitos"] },
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
      <div className="app-header">
        <div>
          <div className="brand">Banorte AI</div>
          <div className="tagline">¿Como quieres que se adapte tu app hoy?</div>
        </div>
      </div>
      <div className="screen-body">
        <div style={{ fontSize: 13, color: "var(--ink-600)" }}>
          Elige una o varias areas, o simplemente cuentame que necesitas abajo.
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              className={`category-chip ${activeCategories.includes(cat.label) ? "selected" : ""}`}
              onClick={() => handleChipClick(cat)}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {expanded && (
          <div className="card">
            <div className="card-subtitle" style={{ marginBottom: 8 }}>
              ¿Algo en particular dentro de {CATEGORIES.find((c) => c.id === expanded).label.toLowerCase()}?
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {CATEGORIES.find((c) => c.id === expanded).subtemas.map((sub) => (
                <button
                  key={sub}
                  className={`category-chip ${selectedSubtemas.includes(sub) ? "selected" : ""}`}
                  onClick={() => toggleSubtema(sub)}
                >
                  {sub}
                </button>
              ))}
            </div>
          </div>
        )}

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
      </div>
      <ChatInput onSend={handleFreeInput} />
    </div>
  );
}
