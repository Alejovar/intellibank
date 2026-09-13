"""
Definicion de tools en JSON schema (name/description/input_schema), agnostico
de proveedor. OPENAI_TOOLS al final del archivo las adapta al formato de
function-calling que espera la API de OpenAI (chat.completions).

Hay dos tipos de tools:
  1. Tools de DATOS/ACCION (get_credit_status, apply_credit_plan, etc.):
     el modelo las llama para leer/escribir datos reales antes de decidir
     que UI mostrar. Se ejecutan contra SQLite (ver tools.py).
  2. Tools de EMISION DE UI (emit_screen, emit_clarification): el modelo
     las llama para "hablar" con el frontend. Su "input" ES el JSON A2UI
     que se valida con Pydantic (schemas/a2ui.py) y se reenvia tal cual
     con mimeType application/a2ui+json.

Nunca se le pide al modelo texto libre para la UI: forzamos su salida
estructurada via tool_use, que es justamente el mecanismo que evita que
el cliente tenga que "parsear" nada.
"""

DOMAIN_TOOLS = [
    {
        "name": "get_credit_status",
        "description": "Obtiene el estado actual de la tarjeta/credito del usuario (saldo, limite, CAT).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_restructure_options",
        "description": "Calcula planes de reestructura (12/18/24 meses) para una cuenta de credito.",
        "input_schema": {
            "type": "object",
            "properties": {"credit_account_id": {"type": "integer"}},
            "required": ["credit_account_id"],
        },
    },
    {
        "name": "simulate_plan_payment",
        "description": "Recalcula pago mensual y CAT estimado para un plazo arbitrario en meses (6-36). Usar cuando el usuario mueve un slider de plazo/pago.",
        "input_schema": {
            "type": "object",
            "properties": {
                "credit_account_id": {"type": "integer"},
                "term_months": {"type": "integer"},
            },
            "required": ["credit_account_id", "term_months"],
        },
    },
    {
        "name": "apply_credit_plan",
        "description": "Aplica de forma real un plan de reestructura ya confirmado por el usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "credit_account_id": {"type": "integer"},
                "term_months": {"type": "integer"},
                "cat": {"type": "number"},
                "monthly_payment": {"type": "number"},
            },
            "required": ["credit_account_id", "term_months", "cat", "monthly_payment"],
        },
    },
    {
        "name": "set_investment_profile",
        "description": "Guarda el perfil de riesgo del usuario (conservador/moderado/dinamico).",
        "input_schema": {
            "type": "object",
            "properties": {"risk_profile": {"type": "string", "enum": ["conservador", "moderado", "dinamico"]}},
            "required": ["risk_profile"],
        },
    },
    {
        "name": "get_investment_profile",
        "description": "Obtiene el perfil de riesgo actual del usuario.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_investment_products",
        "description": "Lista productos de inversion activos y sus tasas definidas por el catalogo financiero.",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_profile": {
                    "type": "string",
                    "enum": ["conservador", "moderado", "dinamico"],
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_portfolio",
        "description": "Obtiene posiciones con costo base, valor actual y ganancia/perdida; es complementario al resumen de liquidez por categoria.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_investment_cashflows",
        "description": "Lista aportaciones, retiros, ganancias y cargos del portafolio.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 20}},
            "required": [],
        },
    },
    {
        "name": "calculate_performance",
        "description": "Calcula rendimiento total y por posicion del portafolio.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "compare_investments",
        "description": "Compara hasta cuatro productos de inversion para un monto y plazo dados.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_ids": {"type": "array", "items": {"type": "string"}, "minItems": 2},
                "amount": {"type": "number", "exclusiveMinimum": 0},
                "term_months": {"type": "integer", "exclusiveMinimum": 0},
            },
            "required": ["product_ids", "amount", "term_months"],
        },
    },
    {
        "name": "get_investment_history",
        "description": "Lista las interfaces generadas anteriormente con titulo, intencion y fecha.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 20}},
            "required": [],
        },
    },
    {
        "name": "get_investment_options",
        "description": "Regresa productos de inversion sugeridos segun perfil de riesgo y monto.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "risk_profile": {"type": "string", "enum": ["conservador", "moderado", "dinamico"]},
            },
            "required": ["amount", "risk_profile"],
        },
    },
    {
        "name": "simulate_investment",
        "description": "Simula el crecimiento de una inversion para graficarlo (curva monto vs tiempo).",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "amount": {"type": "number"},
                "term_months": {"type": "integer"},
            },
            "required": ["product_id", "amount", "term_months"],
        },
    },
    {
        "name": "confirm_investment",
        "description": "Confirma y registra una inversion real tras la simulacion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "product_title": {"type": "string"},
                "amount": {"type": "number"},
                "term_months": {"type": "integer"},
                "rate": {"type": "number"},
                "category": {"type": "string", "default": "general"},
                "details": {"type": "object"},
            },
            "required": ["product_id", "product_title", "amount", "term_months", "rate"],
        },
    },
    {
        "name": "get_portfolio_overview",
        "description": "Obtiene liquidez y portafolio total, agrupando inversiones por categoria. Usar para resumen, que tengo invertido o asignacion.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_fixed_income_products",
        "description": "Lista productos sinteticos de renta fija bancaria o deuda gubernamental.",
        "input_schema": {
            "type": "object",
            "properties": {"category": {"type": "string", "enum": ["renta_fija", "deuda"]}},
            "required": ["category"],
        },
    },
    {
        "name": "simulate_fixed_income",
        "description": "Simula crecimiento compuesto de un producto de renta fija o deuda.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "category": {"type": "string", "enum": ["renta_fija", "deuda"]},
                "amount": {"type": "number", "exclusiveMinimum": 0},
                "term_months": {"type": "integer", "minimum": 1},
            },
            "required": ["product_id", "category", "amount", "term_months"],
        },
    },
    {
        "name": "get_investment_funds",
        "description": "Permite explorar un catalogo detallado de fondos por categoria, rendimiento historico, riesgo y minimo.",
        "input_schema": {
            "type": "object",
            "properties": {"category": {"type": "string", "enum": ["renta_variable", "renta_fija", "balanceado"]}},
            "required": [],
        },
    },
    {
        "name": "get_market_watchlist",
        "description": "Obtiene precios sinteticos demo de acciones y ETFs mexicanos y estadounidenses.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "buy_market_position",
        "description": "Compra y registra una posicion de mercado por cantidad y precio, tras confirmacion del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "quantity": {"type": "number", "exclusiveMinimum": 0},
                "price": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["symbol", "quantity", "price"],
        },
    },
    {
        "name": "get_market_positions",
        "description": "Lista posiciones de acciones/ETF del usuario valuadas con la watchlist sintetica actual.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_fx_rates",
        "description": "Obtiene tipos de cambio sinteticos demo para pares USD/MXN, EUR/MXN y USD/EUR.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "quote_fx_exchange",
        "description": "Cotiza una conversion de divisas usando la tasa sintetica disponible, sin persistirla.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string"},
                "to_currency": {"type": "string"},
                "amount": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["from_currency", "to_currency", "amount"],
        },
    },
    {
        "name": "confirm_fx_exchange",
        "description": "Confirma y registra un cambio de divisas previamente cotizado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string"},
                "to_currency": {"type": "string"},
                "amount": {"type": "number", "exclusiveMinimum": 0},
                "rate": {"type": "number", "exclusiveMinimum": 0},
                "converted_amount": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["from_currency", "to_currency", "amount", "rate", "converted_amount"],
        },
    },
    {
        "name": "get_structured_notes",
        "description": "Lista notas estructuradas sinteticas con subyacente, proteccion, retorno potencial y plazo.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_insurance_products",
        "description": "Regresa productos sinteticos de seguro disponibles con prima, cobertura y deducible.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "quote_insurance",
        "description": "Calcula una cotizacion deterministica para un producto y nivel de cobertura.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "enum": ["auto", "vida", "hogar"]},
                "coverage_level": {"type": "string", "enum": ["basica", "amplia", "premium"]},
            },
            "required": ["product_id", "coverage_level"],
        },
    },
    {
        "name": "confirm_insurance_policy",
        "description": "Confirma y registra una poliza de seguro despues de que el usuario revisa la cotizacion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "enum": ["auto", "vida", "hogar"]},
                "product_title": {"type": "string"},
                "monthly_premium": {"type": "number", "exclusiveMinimum": 0},
                "coverage_level": {"type": "string", "enum": ["basica", "amplia", "premium"]},
            },
            "required": ["product_id", "product_title", "monthly_premium", "coverage_level"],
        },
    },
    {
        "name": "get_insurance_claims_info",
        "description": "Regresa pasos, documentos y canales para reportar un siniestro, junto con las polizas activas del usuario.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "file_insurance_claim",
        "description": "Registra un reporte de siniestro contra una poliza activa del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "integer"},
                "description": {"type": "string", "minLength": 1},
            },
            "required": ["policy_id", "description"],
        },
    },
    {
        "name": "get_financial_diagnosis",
        "description": "Calcula un diagnostico de salud financiera con datos reales de saldo, movimientos y credito del usuario.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_financial_goal",
        "description": "Crea una meta financiera con monto y fecha objetivo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal_name": {"type": "string"},
                "target_amount": {"type": "number", "exclusiveMinimum": 0},
                "target_date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                "term": {"type": "string", "enum": ["corto", "mediano", "largo"]},
            },
            "required": ["goal_name", "target_amount", "target_date"],
        },
    },
    {
        "name": "get_financial_goals",
        "description": "Lista las metas financieras del usuario con plazo, monto ahorrado y porcentaje de avance.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "preview_goal_contribution",
        "description": "Previsualiza el efecto de una aportacion a una meta sin registrarla. Usa esto como accion del boton Aportar de SavingsGoalCard antes de mostrar la confirmacion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "integer"},
                "amount": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["goal_id", "amount"],
        },
    },
    {
        "name": "contribute_to_goal",
        "description": "Registra una aportacion a una meta financiera sin exceder su monto objetivo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "integer"},
                "amount": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["goal_id", "amount"],
        },
    },
    {
        "name": "get_habit_tips",
        "description": "Regresa consejos breves, sinteticos y deterministas para ahorro, gasto o deuda.",
        "input_schema": {
            "type": "object",
            "properties": {
                "focus_area": {"type": "string", "enum": ["ahorro", "gasto", "deuda"]},
            },
            "required": ["focus_area"],
        },
    },
    {
        "name": "get_expenses_summary",
        "description": "Regresa el desglose de gastos por categoria del mes actual, con insights.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_movements",
        "description": "Regresa los ultimos movimientos de la cuenta principal.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}},
            "required": [],
        },
    },
    {
        "name": "search_movements",
        "description": "Busca movimientos por categoria exacta sin distinguir mayusculas y por rango opcional de fechas ISO.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "date_from": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "get_balance",
        "description": "Regresa el saldo de la cuenta principal.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_transfer_recipients",
        "description": "Lista los destinatarios guardados del usuario para poblar el formulario de transferencia.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_transfer_recipient",
        "description": "Guarda un nuevo destinatario de transferencia con nombre y cuenta enmascarada.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "masked_account": {"type": "string"},
            },
            "required": ["label", "masked_account"],
        },
    },
    {
        "name": "quote_transfer",
        "description": "Valida y previsualiza una transferencia (destinatario, monto, saldo disponible) sin moverla. Usa esto como accion del TransferForm antes de mostrar la confirmacion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "amount": {"type": "number", "exclusiveMinimum": 0},
                "concept": {"type": "string"},
            },
            "required": ["to", "amount"],
        },
    },
    {
        "name": "execute_transfer",
        "description": "Ejecuta una transferencia confirmada, descuenta el saldo y registra el movimiento.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "amount": {"type": "number", "exclusiveMinimum": 0},
                "concept": {"type": "string"},
            },
            "required": ["to", "amount", "concept"],
        },
    },
    {
        "name": "create_expense_limit",
        "description": "Crea o actualiza un limite de gasto mensual para una categoria.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "monthly_limit": {"type": "number"},
                "alert_threshold_pct": {"type": "integer", "default": 80},
            },
            "required": ["category", "monthly_limit"],
        },
    },
    {
        "name": "get_card_payment_info",
        "description": "Regresa pago minimo, pago recomendado y fecha limite de la tarjeta.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "schedule_payment",
        "description": "Programa un pago real a la tarjeta de credito.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
            },
            "required": ["amount", "date"],
        },
    },
    {
        "name": "create_shared_expense_group",
        "description": "Crea un grupo de gasto compartido con una lista de personas (incluye al usuario si aplica).",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "people": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "people"],
        },
    },
    {
        "name": "add_shared_expense",
        "description": "Agrega un gasto a un grupo de gasto compartido existente y recalcula deudas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {"type": "integer"},
                "desc": {"type": "string"},
                "amount": {"type": "number"},
                "paid_by": {"type": "string"},
            },
            "required": ["group_id", "desc", "amount", "paid_by"],
        },
    },
]

# Tools de emision de UI. El "input_schema" espeja schemas/a2ui.py a proposito
# (misma forma) para que la validacion Pydantic post-hoc casi siempre pase.
_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {"type": "string"},
        "label": {"type": "string"},
        "style": {"type": "string", "enum": ["primary", "secondary", "danger", "ghost"]},
        "args": {"type": "object"},
        "requires_confirmation": {"type": "boolean"},
        "requires_biometric": {"type": "boolean"},
    },
    "required": ["tool"],
}

_COMPONENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "component": {
            "type": "string",
            "enum": [
                "BalanceCard", "MovementsTable", "ExpenseChart", "OptionsList",
                "BarChart", "PaymentSlider", "TransferForm", "SharedExpenseList",
                "ConfirmationSummary", "SuccessScreen", "InfoBanner", "TextBlock",
                "MarketWatchlist", "CurrencyExchangeCard",
                "PortfolioSummaryCard", "InvestmentPositionCard", "PortfolioTable",
                "PerformanceChart", "CashflowTable", "InvestmentComparison",
                "InvestmentProductList", "RiskProfileSelector", "BeforeAfterPortfolio",
                "SavingsGoalCard",
            ],
        },
        "props": {"type": "object"},
        "actions": {"type": "array", "items": _ACTION_SCHEMA},
    },
    "required": ["id", "component"],
}

_STAGE_KIND_ENUM = ["intent", "generated", "interaction", "confirmation", "result"]

UI_TOOLS = [
    {
        "name": "emit_screen",
        "description": (
            "Emite una pantalla A2UI al usuario combinando componentes del catalogo. "
            "Usar SOLO cuando ya tienes suficiente contexto/datos (via las otras tools) "
            "para construir algo util. No inventes datos: usalos de resultados de tools."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "layout": {"type": "string", "enum": ["stack", "grid"]},
                "components": {"type": "array", "items": _COMPONENT_SCHEMA, "minItems": 1},
                "footer_actions": {"type": "array", "items": _ACTION_SCHEMA},
                "saveable": {"type": "boolean"},
                "stage_kind": {
                    "type": "string", "enum": _STAGE_KIND_ENUM,
                    "description": "En que paso de la maquina de estados del flujo cae esta pantalla.",
                },
                "stage_label": {
                    "type": "string",
                    "description": "Texto corto (2-3 palabras) para el listón de progreso, ej. 'Opciones', 'Simulacion', 'Resultado'.",
                },
            },
            "required": ["id", "title", "components", "stage_kind", "stage_label"],
        },
    },
    {
        "name": "emit_clarification",
        "description": (
            "Pide una aclaracion al usuario ANTES de generar una pantalla, cuando la "
            "solicitud es ambigua, muy abierta, o le falta un dato clave (monto, plazo, "
            "categoria, con quien, etc.)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "question": {"type": "string"},
                "input_mode": {"type": "string", "enum": ["choice", "free_text", "both"]},
                "options": {"type": "array", "items": {"type": "string"}},
                "stage_label": {
                    "type": "string",
                    "description": "Texto corto para el listón de progreso, normalmente 'Intencion' o similar.",
                },
            },
            "required": ["id", "question", "stage_label"],
        },
    },
]

ALL_TOOLS = DOMAIN_TOOLS + UI_TOOLS


def _to_openai_tool(spec: dict) -> dict:
    return {
        "type": "function",
        "function": {
            "name": spec["name"],
            "description": spec["description"],
            "parameters": spec["input_schema"],
        },
    }


OPENAI_TOOLS = [_to_openai_tool(t) for t in ALL_TOOLS]
