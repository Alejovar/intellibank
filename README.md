# Banorte AI — App bancaria con UI generativa (A2UI)

Hackathon Banorte x Tec de Monterrey. Backend FastAPI + orquestacion de LLM
que emite interfaces via el protocolo **A2UI**, y frontend React + Vite que
resuelve ese JSON contra un catalogo cerrado de componentes.

## Maquina de estados del flujo

Cada pantalla que el LLM emite (`emit_screen` / `emit_clarification`) trae
dos campos nuevos en el payload A2UI:

- `stage_kind`: una de 5 clases — `intent` (capturando intencion),
  `generated` (primera pantalla con datos reales), `interaction`
  (ajustar/comparar, puede repetirse varias veces), `confirmation` (revision
  antes de una accion irreversible), `result` (pantalla final).
- `stage_label`: texto corto y especifico al contexto (ej. "Opciones",
  "Ajusta tu pago", "Perfil", "Simulacion", "Resultado") — no son siempre las
  mismas 5 palabras, el modelo elige la etiqueta segun el flujo, igual que
  las leyendas bajo cada pantalla en los diagramas de referencia.

El **numero de pasos no esta fijo**: el system prompt (`llm/system_prompt.py`)
le explica esto al modelo y le deja decidir cuantas pantallas de
`interaction` hacen falta antes de pasar a `confirmation`, dependiendo de que
tan compleja sea la peticion del usuario.

En el frontend, `store/useAppStore.js` acumula estas etiquetas en
`flowTrace` (se reinicia automaticamente cuando arranca un flujo nuevo justo
despues de que el anterior termino en `result`), y `components/FlowTrace.jsx`
las dibuja como el listón de progreso horizontal — igual que "Intención · UI
generada · Interacción · Confirmación · Acción real" en tus imagenes, pero
creciendo en vivo pantalla por pantalla. Tocar un paso anterior salta a esa
pantalla dentro del hilo (no se pierde nada del historial).

## Diseño: Liquid Glass + paleta roja/blanca-gris/beige

El frontend (`src/styles/theme.css`) usa una interpretacion en CSS del
lenguaje visual Liquid Glass de Apple, minimalista y con la paleta pedida:

- **Superficies de vidrio**: `.card`, `.phone-shell`, `.app-header` y la
  barra de input usan `backdrop-filter: blur() saturate()` sobre fondos
  blancos semitransparentes, con un borde superior de realce especular
  (`--glass-border`) y sombras suaves — no bloques de color solido.
- **Fondo**: beige calido (`--beige-100/200`) con dos manchas de color
  desenfocadas (`.app-backdrop`) para que el vidrio tenga algo que
  refractar, en vez de un gradiente marron solido.
- **Rojo como acento, no como base**: botones primarios, selección activa,
  burbujas del usuario y el listón de progreso activo. El resto de la UI es
  blanco/gris/beige — minimalista.
- **Formas**: pastillas (`border-radius: 999px`) para botones, input flotante
  y chips de categoria; radios grandes (20-26px) en tarjetas, concéntricos
  con su contenedor, como pide el lenguaje Liquid Glass.

Como el catalogo de componentes ya trabaja con clases CSS globales (`.card`,
`.btn`, etc.) en vez de estilos embebidos, este cambio de diseño no toco la
logica de ningun componente — solo `theme.css`, `App.jsx` (fondo) y los dos
archivos nuevos de la maquina de estados.

## Que hay implementado

- **Protocolo A2UI de punta a punta**: el LLM nunca genera JSX/HTML. Emite
  JSON estructurado a traves de function-calling de OpenAI (`emit_screen` /
  `emit_clarification`), el backend lo valida con Pydantic contra un catalogo
  cerrado de 11 componentes, y solo entonces se manda al cliente envuelto
  como `{ mime_type: "application/a2ui+json", payload: {...} }`. El frontend
  jamas intenta parsear texto libre.
- **Loop de tools de dominio**: 26 funciones Python deterministas (saldo,
  movimientos, reestructura de credito, amortizacion, inversiones, limites de
  gasto, pagos programados, gastos compartidos) que el LLM llama para obtener
  datos reales antes de decidir que UI mostrar. El LLM elige la tool mediante
  function-calling nativo de OpenAI, pero su ejecucion cruza un cliente/servidor
  MCP real por stdio y ocurre en un proceso separado contra SQLite. Nunca
  inventa cifras. Las tools `emit_screen` / `emit_clarification` permanecen
  locales porque son el protocolo de emision de UI de la app.
- **Acciones = tool calls reales**: un click en un boton/slider/opcion de una
  pantalla generada llega a `POST /actions/execute`, se ejecuta por la misma
  ruta MCP contra SQLite, y el resultado se reinyecta a la conversacion para
  que el LLM decida el siguiente paso (nunca es un mensaje de chat nuevo).
- **Los 3 flujos de las imagenes de referencia**, funcionando de extremo a
  extremo con datos sinteticos:
  1. **Credito inteligente**: intencion ambigua ("quiero pagar menos
     intereses") -> clarificacion -> opciones de reestructura -> slider de
     plazo/pago con grafica -> confirmacion con biometria simulada -> accion
     real aplicada -> pantalla de exito.
  2. **Inversiones personalizadas**: perfilamiento por opciones -> productos
     sugeridos segun perfil y monto -> simulador con curva de crecimiento ->
     confirmar inversion -> resultado guardado.
  3. **Control de gastos y pagos**: resumen de gastos por categoria (donut +
     insight) -> crear limite inteligente -> pago de tarjeta (minimo vs
     recomendado por IA) -> pago programado -> confirmacion.
  4. Caso abierto adicional ya soportado por las tools: **dividir la cuenta
     de un bar entre amigos**, con una interfaz editable (`SharedExpenseList`)
     donde se pueden seguir agregando gastos y personas despues.
- **Guia activa cuando la idea es ambigua o "imposible"**: el system prompt
  (`backend/app/llm/system_prompt.py`) instruye al modelo a **nunca saltar**
  de una peticion abierta directo a una pantalla — primero pregunta lo minimo
  necesario (`emit_clarification`, idealmente con opciones), y antes de
  cualquier accion irreversible siempre pasa por una `ConfirmationSummary`
  con `requires_biometric`. Asi, un pedido como "reduce lo que pago de
  credito" se va desglosando pantalla por pantalla en vez de fallar.
- Login con clave bancaria + password, onboarding de 4 pantallas fijas,
  seleccion de categoria con **revelacion progresiva** (no se muestran todos
  los subtemas de una vez), input de texto + voz (Web Speech API) siempre
  visible, y guardar/descartar al cerrar cualquier pantalla generada.

## Estructura

```
backend/
  app/
    main.py                 FastAPI app, CORS, seed al iniciar
    mcp_server.py           Servidor MCP stdio; ejecuta tools de dominio contra SQLite
    models.py                SQLAlchemy (datos 100% sinteticos)
    seed.py                   Carga datos demo si la DB esta vacia
    auth.py                    Login simple (clave + password) -> token
    schemas/
      a2ui.py                  *** Esquema del protocolo A2UI (Pydantic) ***
      chat.py                   Requests/responses de chat y acciones
    llm/
      catalog.py               Descripcion del catalogo para el prompt
      tool_specs.py             Tools en JSON schema, adaptadas a function-calling de OpenAI
      tools.py                  Logica de negocio real (SQLite)
      system_prompt.py          Instrucciones de orquestacion/guia
      client.py                 Wrapper del SDK de OpenAI
      mcp_client.py             Cliente MCP persistente (thread + subprocess stdio)
      orchestrator.py          *** Loop de tool-use + validacion A2UI ***
    routers/
      auth.py, chat.py, actions.py

frontend/
  src/
    components/
      catalog/                *** Los 11 componentes del catalogo cerrado ***
      A2UIRenderer.jsx          Resuelve el JSON del backend contra el catalogo
      ChatInput.jsx             Texto + microfono, siempre visible
    screens/
      LoginScreen, OnboardingScreen (fijo), CategorySelection (progresivo),
      AssistantScreen (chat + pantallas generadas + guardar/descartar)
    store/useAppStore.js        Estado global (zustand)
    api/client.js               Cliente HTTP
```

## Como correrlo

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edita .env y agrega tu OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

La DB SQLite (`banorte_demo.db`) se crea y se llena sola con un usuario demo
en el primer arranque:

- **Clave bancaria:** `4152`
- **Password:** `demo1234`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`. El `vite.config.js` ya tiene un proxy de
`/api` -> `http://localhost:8000`, asi que no hay que configurar CORS a mano
en desarrollo (aunque el backend tambien trae CORS habilitado por si se sirve
por separado).

## Notas sobre el LLM

- El modelo usado es configurable via `OPENAI_MODEL` en `.env` (por defecto
  `gpt-4o`, elegido sobre `gpt-4o-mini` por su seguimiento mas consistente
  de instrucciones multi-paso de tool-calling; `gpt-4o-mini` funciona pero
  falla con mas frecuencia en flujos largos).
- El historial de conversacion se persiste en la tabla `ConversationTurn`
  (SQLite) por usuario, y sobrevive reinicios del proceso backend. Cada
  mensaje/tool-call/tool-result de OpenAI se guarda serializado en JSON.
- Ademas del historial, `SessionState` guarda una maquina de estados real
  por usuario (`current_stage`, la ultima pantalla mostrada, y una accion
  pendiente de confirmacion). El LLM elige libremente el `stage_kind` de
  cada pantalla, pero el backend valida esa transicion contra
  `ALLOWED_STAGE_TRANSITIONS` en `orchestrator.py` antes de aceptarla — si
  el LLM intenta un salto no permitido, se degrada a una aclaracion en vez
  de mandar la pantalla al cliente.
- Las tools de dominio (`DOMAIN_TOOLS`) NO se ejecutan en el mismo proceso:
  el LLM las llama via function-calling de OpenAI, pero la ejecucion real
  cruza un cliente/servidor MCP (`mcp_client.py`/`mcp_server.py`) por stdio
  contra SQLite. Las tools de emision de UI (`emit_screen`/
  `emit_clarification`) se quedan locales, ya que son el protocolo propio
  de la app, no acceso a un sistema externo.
- El orquestador limita a `MAX_TOOL_ITERATIONS = 6` llamadas de tool por
  turno para evitar loops infinitos; si el modelo no logra emitir una
  pantalla valida en ese margen, se degrada a un mensaje de texto plano
  pidiendo reformular.
- Si `emit_screen`/`emit_clarification` regresa algo que no pasa la
  validacion Pydantic (p.ej. un nombre de componente inventado), el backend
  **nunca** reenvia esa salida rota al cliente: cae a una pantalla de
  aclaracion generica (`_fallback_envelope`) y lo registra en logs.

## Extender el catalogo

1. Agrega el componente React en `frontend/src/components/catalog/` y
   registralo en `catalog/index.js`.
2. Agrega el nombre a `COMPONENT_CATALOG` en `backend/app/schemas/a2ui.py`.
3. Describe sus props en `backend/app/llm/catalog.py` (esto es lo que el LLM
   "lee" para saber cuando y como usarlo) y en el `_COMPONENT_SCHEMA` de
   `tool_specs.py` si quieres que OpenAI tambien valide su forma en el
   momento de la llamada.
4. Si el componente necesita datos reales, agrega la tool correspondiente en
   `tools.py` + `tool_specs.py`.

## Limitaciones conocidas de esta demo

- Datos 100% sinteticos/hardcodeados (sin conexion a sistemas reales de
  Banorte), como pide el stack del hackathon.
- Autenticacion simplificada (token de sesion en memoria, no JWT firmado) —
  suficiente para demo, no para produccion; el login sigue viviendo en
  `_SESSIONS` (dict en memoria) en `auth.py`, asi que un reinicio del
  backend invalida los tokens activos (el frontend detecta el 401 y
  regresa a login automaticamente).
- La "biometria" en `ConfirmationSummary` sigue siendo solo visual (no
  integra un sensor real), pero el backend ya no confia ciegamente en el
  boton: `POST /actions/execute` exige que la tool este realmente ofrecida
  en la ultima pantalla, que el `screen_id` coincida, y que las tools
  irreversibles (`apply_credit_plan`, `confirm_investment`,
  `schedule_payment`, `confirm_insurance_policy`, `file_insurance_claim`,
  `contribute_to_goal`) solo se ejecuten si el usuario paso por una
  pantalla real de `stage_kind="confirmation"`.
- Con gpt-4o-mini se observo inconsistencia real en flujos de varios
  pasos (saltos de estado invalidos, texto plano en vez de una tool call,
  pantallas sin acciones de seguimiento); `gpt-4o` reduce esto pero no lo
  elimina del todo — sigue siendo un modelo no determinista.
