"""
Descripcion del catalogo de componentes que se le da al LLM como
contexto (no como codigo, solo como "menu" de que puede usar y con
que props). Esto es lo unico que el LLM "ve" del frontend: nombres +
forma de las props. Nunca ve ni genera JSX/HTML.
"""

CATALOG_DESCRIPTION = """
CATALOGO CERRADO DE COMPONENTES (usa EXACTAMENTE estos nombres en "component"):

1. BalanceCard
   props: { accountLabel, maskedNumber, balance, limit?, available?, progressPercent? }
   Uso: mostrar saldo de cuenta o tarjeta. Es una pantalla FIJA cuando se usa como
   resumen principal (ver reglas de "saveable").

2. MovementsTable
   props: { movements: [{ date, description, category, amount }] }
   Uso: listar movimientos/transacciones.

3. ExpenseChart
   props: { chartType: "donut"|"line", data: [{label, value, color?}], total?, centerLabel?,
            insightText? }
   Uso: graficas de gasto por categoria (donut) o proyecciones/simulaciones (line).

4. OptionsList
   props: { options: [{ id, title, subtitle?, badge?, highlighted?, icon? }],
            selectionMode: "single"|"multi", helperText? }
   actions en cada componente: usa "actions" del componente para el tool que se dispara
   al seleccionar una opcion (manda { optionId } como arg dinamico).
   Uso: planes de reestructura, perfiles de riesgo, productos de inversion, preguntas
   de opcion multiple para clarificacion.

5. PaymentSlider
   props: { label, min, max, step?, value, unit?, helperText?,
            chart?: { data: [{x,y}], xLabel?, yLabel? } }
   actions: tool que se dispara al soltar el slider (manda { value } como arg dinamico).
   Uso: ajustar plazo/pago mensual con feedback visual inmediato.

6. TransferForm
   props: { fromAccountLabel, toLabel?, amount?, concept?, availableAccounts?: [string] }
   Uso: formularios de transferencia/pago.

7. SharedExpenseList
   props: { title, people: [{name, paid, owes}], expenses: [{desc, amount, paidBy}] }
   actions: tools para agregar persona / agregar gasto.
   Uso: dividir cuentas entre amigos, control de deudas compartidas.

8. ConfirmationSummary
   props: { title, rows: [{label, value, highlighted?}], note? }
   actions: normalmente 2 acciones (confirmar con requires_biometric=true, y volver).
   Uso: pantalla de "revisa antes de confirmar" previa a una accion irreversible.

9. SuccessScreen
   props: { title, message, details?: [{label, value}] }
   actions: incluye AL MENOS UNA accion de seguimiento con un tool real y relevante
   cuando exista un siguiente paso sensato (continuar, consultar lo creado, iniciar un
   flujo relacionado, etc.).
   Uso: es el componente preferido para una pantalla stage_kind="result" tras completar
   exitosamente una accion real (aplicar plan, invertir, programar pago, crear limite,
   etc.). Resume los datos clave en "details"; NO sustituyas esa lista con varios
   TextBlock separados ni conviertas la confirmacion en una pila de texto de solo lectura.

10. InfoBanner
    props: { icon?: "tip"|"warning"|"info"|"trend", title?, text }
    Uso: sugerencias, alertas ("gastaste 18% mas de lo usual"), disclaimers.

11. TextBlock
    props: { text }
    Uso: texto simple cuando ningun otro componente aplica (usar con moderacion).

12. MarketWatchlist
    props: { title?, items: [{ symbol, name, price, changePct, currency? }] }
    actions: al seleccionar una fila manda { symbol } como arg dinamico.
    Uso: listas compactas de precios sinteticos para acciones, ETFs y pares de divisas;
    muestra variaciones positivas en verde y negativas en rojo.

13. CurrencyExchangeCard
    props: { fromCurrency, toCurrency, amount, rate, convertedAmount, note? }
    actions: la primera accion confirma el cambio y recibe dinamicamente
    { from_currency, to_currency, amount, rate, converted_amount }.
    Uso: mostrar una cotizacion de divisas y su boton "Confirmar cambio".

14. PortfolioSummaryCard
    props: { totalInvested, totalValue, totalGain, gainPct, asOf? }
    Uso: resumen de costo base, valor actual y rendimiento del portafolio.

15. InvestmentPositionCard
    props: { product, amount, currentValue, gain, gainPct, risk?, status? }
    Uso: mostrar una posicion individual con sus metricas.

16. PortfolioTable
    props: { columns?: [string], rows: [{ product, amount, currentValue, gain, gainPct }] }
    Uso: tabla detallada de posiciones del portafolio.

17. PerformanceChart
    props: { data: [{ label, value, returnPct? }], totalGain, returnPct, period? }
    Uso: visualizar rendimiento agregado y por posicion.

18. CashflowTable
    props: { transactions: [{ date, type, description, amount }], totalDeposits?,
             totalWithdrawals?, totalGains? }
    Uso: aportaciones, retiros, ganancias y cargos del portafolio.

19. InvestmentComparison
    props: { products: [{ title, risk, rate, amount, termMonths, finalValue, estimatedGain }] }
    Uso: comparar hasta cuatro alternativas de inversion.

20. InvestmentProductList
    props: { products: [{ id, title, description?, risk, rate, minAmount }] }
    actions: seleccionar un producto para simular.
    Uso: productos disponibles segun perfil y monto.

21. RiskProfileSelector
    props: { currentProfile?, options: [{ id, title, description }] }
    actions: guardar un perfil de riesgo.
    Uso: perfilamiento de inversion.

22. BeforeAfterPortfolio
    props: { before: { totalValue, totalGain, capturedAt? },
             after: { totalValue, totalGain, capturedAt? } }
    Uso: comparar una interfaz historica contra los datos actuales.

REGLAS DE COMPOSICION:
- Una pantalla (A2UIScreen) puede combinar 1 a 4 componentes en layout "stack" (vertical)
  o "grid".
- TODA pantalla generada debe dejar al usuario al menos una forma significativa de seguir
  actuando mediante "actions" de un componente o "footer_actions", usando un tool real
  y relevante disponible para el flujo/categoria, siempre que exista un siguiente paso
  sensato (consultar, continuar, ajustar o iniciar algo relacionado). Una pantalla que
  deja al usuario sin nada que hacer es incompleta y no es aceptable. Solo omite acciones
  si es una lectura informativa que realmente no tiene un siguiente paso aplicable; aun
  entonces, prefiere ofrecer volver o una accion relacionada si existe un tool adecuado.
- Si la peticion del usuario es ambigua o muy abierta (ej. "quiero pagar menos intereses"),
  NO generes una pantalla todavia: responde con A2UIClarification y una pregunta puntual,
  idealmente con 2-4 "options" cuando tenga sentido opcion multiple.
- Guia al usuario paso a paso: primero entiende la intencion, luego muestra opciones,
  luego permite ajustar (slider/formulario), luego confirma, luego resultado. No hagas
  saltos bruscos de "pregunta" a "confirmacion" sin pasar por una pantalla de opciones/ajuste.
- Los datos financieros reales (saldos, movimientos, tasas) SIEMPRE deben venir de los
  resultados de tools que ya llamaste. Nunca inventes cifras.
- Para posiciones, rendimiento y flujos usa get_portfolio, calculate_performance y
  get_investment_cashflows; no los confundas con get_portfolio_overview, que incluye
  liquidez y agrupacion por categoria.
- Para historial usa get_investment_history; las tasas y productos deben venir de
  get_investment_products o get_investment_options.
- saveable=false SOLO para pantallas de saldo/resumen fijo que el sistema ya definio como
  no editables (ej. BalanceCard principal mostrado solo).
"""
