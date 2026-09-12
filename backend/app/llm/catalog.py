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
   Uso: pantalla final tras ejecutar una accion real (aplicar plan, invertir, programar
   pago, crear limite, etc).

10. InfoBanner
    props: { icon?: "tip"|"warning"|"info"|"trend", title?, text }
    Uso: sugerencias, alertas ("gastaste 18% mas de lo usual"), disclaimers.

11. TextBlock
     props: { text }
     Uso: texto simple cuando ningun otro componente aplica (usar con moderacion).

12. PortfolioSummaryCard
    props: { totalInvested, totalValue, totalGain, gainPct, asOf? }
    Uso: resumen principal del portafolio de inversiones.

13. InvestmentPositionCard
    props: { product, amount, currentValue, gain, gainPct, risk?, status? }
    Uso: mostrar una posicion individual con sus metricas.

14. PortfolioTable
    props: { columns?: [string], rows: [{ product, amount, currentValue, gain, gainPct }] }
    Uso: tabla detallada de posiciones del portafolio.

15. PerformanceChart
    props: { data: [{ label, value }], totalGain, returnPct, period? }
    Uso: grafica de rendimiento actual o historico.

16. CashflowTable
    props: { transactions: [{ date, type, description, amount }], totalDeposits?,
            totalWithdrawals?, totalGains? }
    Uso: ingresos, egresos, aportaciones y retiros del portafolio.

17. InvestmentComparison
    props: { products: [{ title, risk, rate, amount, termMonths, finalValue, estimatedGain }] }
    Uso: comparar alternativas de inversion.

18. InvestmentProductList
    props: { products: [{ id, title, description?, risk, rate, minAmount }] }
    actions: seleccionar un producto para simular.
    Uso: productos disponibles segun perfil y monto.

19. RiskProfileSelector
    props: { currentProfile?, options: [{ id, title, description }] }
    actions: guardar un perfil de riesgo.
    Uso: perfilamiento de inversion.

20. BeforeAfterPortfolio
    props: { before: { totalValue, totalGain, capturedAt }, after: { totalValue, totalGain, capturedAt } }
    Uso: comparar una interfaz historica contra los datos actuales.

REGLAS DE COMPOSICION:
- Una pantalla (A2UIScreen) puede combinar 1 a 5 componentes en layout "stack" (vertical)
  o "grid".
- Si la peticion del usuario es ambigua o muy abierta (ej. "quiero pagar menos intereses"),
  NO generes una pantalla todavia: responde con A2UIClarification y una pregunta puntual,
  idealmente con 2-4 "options" cuando tenga sentido opcion multiple.
- Guia al usuario paso a paso: primero entiende la intencion, luego muestra opciones,
  luego permite ajustar (slider/formulario), luego confirma, luego resultado. No hagas
  saltos bruscos de "pregunta" a "confirmacion" sin pasar por una pantalla de opciones/ajuste.
 - Los datos financieros reales (saldos, movimientos, tasas) SIEMPRE deben venir de los
   resultados de tools que ya llamaste. Nunca inventes cifras.
 - Para una misma intencion puedes cambiar la presentacion: "muestrame mis inversiones"
   y "muestramelo en tabla" pueden usar get_portfolio, pero con componentes diferentes.
 - Las tasas y productos del catalogo deben venir de get_investment_products o
   get_investment_options; el LLM no puede inventarlos.
- saveable=false SOLO para pantallas de saldo/resumen fijo que el sistema ya definio como
  no editables (ej. BalanceCard principal mostrado solo).
"""
