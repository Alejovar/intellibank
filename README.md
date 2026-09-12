# IntelliBank — Inversiones con UI generativa (A2UI)

Prototipo del modulo de inversiones. Backend FastAPI + orquestacion de LLM
que emite interfaces via el protocolo **A2UI**, y frontend React + Vite que
resuelve ese JSON contra un catalogo cerrado de componentes de inversiones.

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

El renderer mantiene el catalogo cerrado como frontera de seguridad: el agente
solo puede pedir componentes registrados y el cliente nunca ejecuta codigo
recibido desde el modelo.

## Alcance actual: inversiones

- **Shell único**: saldo y rendimiento arriba, superficie A2UI reemplazable al
  centro y compositor de IA persistente sobre una navegación simétrica de tres
  destinos: Historial, Inicio y Perfil.
- **Acceso progresivo**: la primera entrada solicita nombre, correo, teléfono,
  contraseña y CLABE o tarjeta dentro de una sola interfaz. En visitas
  posteriores muestra directamente biometría o el acceso alternativo por
  contraseña, sin pestañas de registro/login.
- **Biometría real para la demo web**: WebAuthn/passkeys solicita el autenticador
  de plataforma (Face ID, huella o Windows Hello), verifica la firma en FastAPI
  y guarda únicamente clave pública, contador e identificador de credencial.

- **LLM + MCP + A2UI**: el agente descubre exclusivamente tools de inversiones.
  El LLM interpreta la intención y elige herramientas; MCP ejecuta lógica
  determinista; A2UI describe la pantalla y React la renderiza.
- **Portafolio**: consulta de posiciones, valor total, rendimiento,
  aportaciones, retiros y comparación de productos.
- **Flujo de inversión**: perfil de riesgo -> productos -> simulación ->
  confirmación con `requires_biometric` -> inversión registrada.
- **Historial reproducible**: cada pantalla generada guarda prompt, intención,
  tools, argumentos, datos y payload A2UI. Al abrirla se reproduce sin llamar
  nuevamente al LLM y se compara el antes contra el estado actual.
- **Registro**: nombre, correo, teléfono, contraseña y CLABE o tarjeta. Las
  cuentas nuevas usan hash PBKDF2; la tarjeta se guarda solo como hash y últimos
  cuatro dígitos.
- **Voz**: el navegador usa reconocimiento nativo cuando está disponible y
  el backend ofrece `/voice/transcribe` como fallback con
  `gpt-4o-mini-transcribe`.

## Estructura

```
backend/
  app/
    main.py                 FastAPI app, CORS, seed al iniciar
    mcp_server.py           Servidor MCP stdio; ejecuta tools de dominio contra SQLite
    models.py                SQLAlchemy (usuarios, inversiones, snapshots, historial)
    seed.py                  Carga datos demo y catalogo de productos
    auth.py                  Registro/login y sesiones firmadas
    passkeys.py              Registro y autenticación WebAuthn/passkeys
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
      auth.py, chat.py, actions.py, investments.py, voice.py

frontend/
  src/
    auth/passkeys.js         Adaptador WebAuthn del navegador
    components/
      catalog/                *** Componentes genericos + catalogo de inversiones ***
      A2UIRenderer.jsx          Resuelve el JSON del backend contra el catalogo
      InvestmentShell.jsx       Saldo/superficie/dock persistentes
      ChatInput.jsx             Texto + microfono, siempre visible
    screens/
      LoginScreen, HomeScreen, SavedScreensScreen, MoreScreen
    store/useAppStore.js        Estado global (zustand)
    api/client.js               Cliente HTTP
```

## Como correrlo

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Si backend/.env no existe, créalo con OPENAI_API_KEY y OPENAI_MODEL=gpt-4o-mini
python -m uvicorn app.main:app --reload --port 8001
```

La DB SQLite (`banorte_demo.db`) se crea y se llena sola con un usuario demo
en el primer arranque:

- **Clave bancaria:** `4152`
- **Password:** `demo1234`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173` (usa `localhost`, no la IP, para que WebAuthn
coincida con el RP ID configurado). El `vite.config.js` ya tiene un proxy de
`/api` -> `http://127.0.0.1:8001`, asi que no hay que configurar CORS a mano
en desarrollo (aunque el backend tambien trae CORS habilitado por si se sirve
por separado).

## Notas sobre el LLM

- El modelo usado es configurable via `OPENAI_MODEL` en `.env` (por defecto `gpt-4o-mini`).
- GPT-4o Mini se usa para texto, function calling y salidas estructuradas. El
  dictado puede usar el reconocimiento del dispositivo o el fallback
  `OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe`.
- Las conversaciones viven en `ConversationTurn` y las interfaces en
  `InterfaceHistory`; el login ya no borra el historial.
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
- El token de la demo se firma con `JWT_SECRET` y expira en 24 horas. Para
  producción se deben usar access/refresh tokens, rotación, revocación y un
  proveedor de identidad bancario.
- Los retos WebAuthn viven cinco minutos en memoria. En producción deben vivir
  en Redis u otro almacén compartido; las credenciales públicas sí persisten en
  la base de datos. La biometría nunca se guarda ni se envía al servidor.
- La misma API y contrato A2UI están listos para un cliente React Native. En
  iOS/Android el renderer será nativo y utilizará la passkey/biometría de la
  plataforma; este repositorio conserva la web como demo ejecutable del flujo.
- SQLite y tasas sintéticas son adecuados para presentar el flujo, no para
  operar inversiones reales.
