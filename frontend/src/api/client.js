import { useAppStore } from "../store/useAppStore";

const BASE = "http://127.0.0.1:8080/api";
function authHeaders() {
  const token = localStorage.getItem("banorte_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    // Un 401 en cualquier endpoint autenticado (no el login en si, donde un
    // 401 solo significa credenciales incorrectas) indica una sesion
    // invalida/expirada (p.ej. el backend se reinicio y perdio las sesiones
    // en memoria). Regresamos a login en vez de dejar al usuario atorado
    // viendo "Token invalido o expirado" sin poder avanzar.
    if (res.status === 401 && path !== "/auth/login") {
      useAppStore.getState().logout();
    }
    throw new Error(body.detail || `Error ${res.status}`);
  }
  return res.json();
}

export const api = {
  login: (clave_bancaria, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ clave_bancaria, password }) }),

  completeOnboarding: () => request("/auth/onboarding-complete", { method: "POST" }),

  /**
   * Manda un mensaje de chat (texto, voz transcrita, o boton de categoria).
   * La respuesta SIEMPRE viene envuelta como { response: { mime_type, payload } }.
   * Nunca se debe intentar parsear "payload" como texto libre cuando
   * mime_type es application/a2ui+json: ya viene como JSON estructurado.
   */
  sendMessage: (message, { inputMode = "text", activeCategories = [] } = {}) =>
    request("/chat/message", {
      method: "POST",
      body: JSON.stringify({ message, input_mode: inputMode, active_categories: activeCategories }),
    }),

  /**
   * Unico canal por el que una interaccion con un componente generado
   * (boton, slider, seleccion) llega al backend. Nunca se manda como
   * mensaje de chat nuevo.
   */
  executeAction: (tool, args = {}, screenId = null) =>
    request("/actions/execute", {
      method: "POST",
      body: JSON.stringify({ tool, args, screen_id: screenId }),
    }),

  saveScreen: (title, a2uiPayload) =>
    request("/actions/save-screen", {
      method: "POST",
      body: JSON.stringify({ title, a2ui_payload: a2uiPayload }),
    }),

  listSavedScreens: () => request("/actions/saved-screens"),

  getHomeSummary: () => request("/accounts/home-summary"),
};
