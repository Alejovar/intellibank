import { useState } from "react";
import BottomNav from "../components/BottomNav";
import ChatInput from "../components/ChatInput";
import { Brand, StatusBar } from "../components/PhoneChrome";
import { ASSISTANT_CATEGORIES } from "../data/assistantCategories";
import { useAppStore } from "../store/useAppStore";

export default function ThemeSelectionScreen({ onContinue, onSkip, onFreeInput, onNavigate }) {
  const [expanded, setExpanded] = useState(null);
  const activeCategories = useAppStore((state) => state.activeCategories);
  const activeSubtopics = useAppStore((state) => state.activeSubtopics);
  const toggleCategory = useAppStore((state) => state.toggleCategory);
  const toggleSubtopic = useAppStore((state) => state.toggleSubtopic);

  const handleCategoryClick = (category) => {
    const isSelected = activeCategories.includes(category.label);
    toggleCategory(category.label);
    setExpanded(isSelected && expanded === category.id ? null : category.id);
  };

  const handleSubtopicClick = (category, subtopic) => {
    if (!activeCategories.includes(category.label)) toggleCategory(category.label);
    toggleSubtopic(category.label, subtopic);
  };

  const hasSelection = activeCategories.length > 0;

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        <div>
          <Brand compact />
          <div className="tagline">Personaliza tu experiencia</div>
        </div>
        <span className="a2ui-pill" style={{ marginLeft: "auto" }}>A2UI</span>
      </div>

      <main className="screen-body theme-selection-screen">
        <div>
          <h1 className="screen-title">¿Qué quieres priorizar?</h1>
          <p className="screen-copy">Elige uno o varios temas. Puedes cambiarlos después desde Más.</p>
        </div>

        <div className="category-list">
          {ASSISTANT_CATEGORIES.map((category) => {
            const selected = activeCategories.includes(category.label);
            const open = expanded === category.id;
            const selectedSubtopics = activeSubtopics[category.label] || [];

            return (
              <div key={category.id} className={`category-item ${open ? "open" : ""} ${selected ? "selected" : ""}`}>
                <button
                  type="button"
                  className="category-row"
                  onClick={() => handleCategoryClick(category)}
                  aria-expanded={open}
                  aria-pressed={selected}
                  aria-controls={`subtopics-${category.id}`}
                >
                  <span className="category-icon" style={{ background: category.tint }} />
                  <span className="category-copy">
                    <strong>{category.label}</strong>
                    <small>{category.hint}</small>
                  </span>
                  <span className="category-state" aria-hidden="true">{selected ? "✓" : "+"}</span>
                  <span className="category-chevron" aria-hidden="true">›</span>
                </button>

                {open && (
                  <div id={`subtopics-${category.id}`} className="category-subs">
                    {category.subtemas.map((subtopic) => {
                      const subtopicSelected = selectedSubtopics.includes(subtopic);
                      return (
                        <button
                          key={subtopic}
                          type="button"
                          className={`category-chip ${subtopicSelected ? "selected" : ""}`}
                          onClick={() => handleSubtopicClick(category, subtopic)}
                          aria-pressed={subtopicSelected}
                        >
                          {subtopic}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="theme-selection-actions">
          {hasSelection && (
            <button type="button" className="btn btn-primary" onClick={onContinue}>
              Continuar
            </button>
          )}
          {!hasSelection && (
            <button type="button" className="theme-skip" onClick={onSkip}>Ahora no</button>
          )}
        </div>

        <div className="theme-free-input">
          O dilo tú: <strong>“quiero pagar menos intereses de mi tarjeta”</strong>
        </div>
      </main>

      <ChatInput
        onSend={onFreeInput}
        navigation={<BottomNav activeTab="assistant" onChange={onNavigate} />}
      />
    </div>
  );
}
