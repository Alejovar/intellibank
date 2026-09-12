import { create } from "zustand";

/**
 * Estado global minimo de la app. Guardamos:
 * - sesion (token/nombre)
 * - progreso de onboarding
 * - categorias activas elegidas por el usuario
 * - el "hilo" de la conversacion actual: mezcla de burbujas de chat
 *   (mime_type text/plain) y pantallas generadas (mime_type application/a2ui+json)
 */
export const useAppStore = create((set, get) => ({
  token: localStorage.getItem("banorte_token") || null,
  fullName: localStorage.getItem("banorte_name") || "",
  onboardingDone: localStorage.getItem("banorte_onboarding") === "1",

  activeCategories: [],
  thread: [], // [{kind:"chat", role, text} | {kind:"screen", envelope}]
  currentScreen: null, // la ultima A2UIScreen/Clarification mostrada a pantalla completa
  loading: false,
  error: null,

  // Máquina de estados del flujo actual: una entrada por pantalla generada,
  // en el orden en que fueron apareciendo. Se reinicia cuando arranca un
  // flujo nuevo (stage_kind "intent" justo despues de que el flujo anterior
  // termino en "result", o al inicio de la sesion). El largo es dinamico:
  // depende de cuantos pasos haya necesitado ese pedido en particular.
  flowTrace: [], // [{ stageKind, stageLabel, threadIndex }]

  login: (token, fullName, onboardingDone) => {
    localStorage.setItem("banorte_token", token);
    localStorage.setItem("banorte_name", fullName);
    localStorage.setItem("banorte_onboarding", onboardingDone ? "1" : "0");
    set({ token, fullName, onboardingDone });
  },

  logout: () => {
    localStorage.clear();
    set({ token: null, fullName: "", onboardingDone: false, thread: [], currentScreen: null });
  },

  completeOnboarding: () => {
    localStorage.setItem("banorte_onboarding", "1");
    set({ onboardingDone: true });
  },

  toggleCategory: (cat) => {
    const current = get().activeCategories;
    set({
      activeCategories: current.includes(cat)
        ? current.filter((c) => c !== cat)
        : [...current, cat],
    });
  },

  setLoading: (v) => set({ loading: v }),
  setError: (e) => set({ error: e }),

  pushChat: (role, text) =>
    set((s) => ({ thread: [...s.thread, { kind: "chat", role, text }] })),

  /**
   * Procesa la respuesta cruda del backend. Este es el UNICO lugar donde
   * se hace el switch sobre mime_type: nunca se intenta adivinar el tipo
   * a partir del contenido, siempre se confia en el campo explicito.
   */
  applyResponse: (response) => {
    if (response.mime_type === "application/a2ui+json") {
      const payload = response.payload;
      const stageKind = payload.stage_kind || "generated";
      const stageLabel = payload.stage_label || "Pantalla";
      set((s) => {
        const thread = [...s.thread, { kind: "screen", envelope: response }];
        const threadIndex = thread.length - 1;
        const lastStage = s.flowTrace[s.flowTrace.length - 1];
        const startsNewFlow =
          stageKind === "intent" && (!lastStage || lastStage.stageKind === "result");
        const flowTrace = startsNewFlow
          ? [{ stageKind, stageLabel, threadIndex }]
          : [...s.flowTrace, { stageKind, stageLabel, threadIndex }];
        return { thread, currentScreen: payload, flowTrace };
      });
    } else if (response.mime_type === "text/plain") {
      get().pushChat("assistant", response.payload);
    }
  },

  clearCurrentScreen: () => set({ currentScreen: null }),

  resetThread: () => set({ thread: [], currentScreen: null, flowTrace: [] }),
}));
