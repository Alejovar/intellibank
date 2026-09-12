"""
Esquema del protocolo A2UI (Agent-to-UI).

Reglas de diseno (ver reglas del hackathon):
1. El LLM NUNCA emite JSX/HTML. Solo emite este JSON declarativo.
2. Cada "component" debe ser uno de los nombres del catalogo cerrado
   (ver app/llm/catalog.py). El backend VALIDA esto con Pydantic antes
   de reenviarlo al frontend -> si el LLM alucina un componente o unas
   props invalidas, la validacion falla y forzamos un reintento/fallback
   en vez de mandar basura al cliente.
3. El frontend nunca parsea texto libre: solo interpreta payloads con
   mimeType "application/a2ui+json" (ver ChatResponse.mime_type).
4. Los botones de un componente declaran "action" con un "tool" -> al
   hacer click, el frontend llama POST /actions/execute con ese tool y
   sus args. El backend ejecuta la logica de negocio (deterministica,
   Python puro) y el resultado se inyecta como contexto al LLM para el
   siguiente turno.
"""
from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator

# Catalogo cerrado de componentes que el LLM puede usar.
# Si agregas un componente en el frontend, agregalo aqui tambien.
COMPONENT_CATALOG = {
    "BalanceCard",
    "MovementsTable",
    "ExpenseChart",
    "OptionsList",
    "PaymentSlider",
    "TransferForm",
    "SharedExpenseList",
    "ConfirmationSummary",
    "SuccessScreen",
    "InfoBanner",
    "TextBlock",
    "PortfolioSummaryCard",
    "InvestmentPositionCard",
    "PortfolioTable",
    "PerformanceChart",
    "CashflowTable",
    "InvestmentComparison",
    "InvestmentProductList",
    "RiskProfileSelector",
    "BeforeAfterPortfolio",
}


class ActionSpec(BaseModel):
    """Una accion invocable desde un componente (boton, seleccion, slider, etc)."""
    tool: str = Field(..., description="Nombre del tool de backend a invocar")
    label: Optional[str] = None
    style: Literal["primary", "secondary", "danger", "ghost"] = "primary"
    args: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    requires_biometric: bool = False


class A2UIComponent(BaseModel):
    id: str
    component: str
    props: dict[str, Any] = Field(default_factory=dict)
    actions: list[ActionSpec] = Field(default_factory=list)

    @field_validator("component")
    @classmethod
    def validate_component(cls, v: str) -> str:
        if v not in COMPONENT_CATALOG:
            raise ValueError(
                f"Componente '{v}' no existe en el catalogo cerrado. "
                f"Disponibles: {sorted(COMPONENT_CATALOG)}"
            )
        return v


# Maquina de estados del flujo. El numero de pantallas por flujo NO es fijo
# (depende de lo que pida el usuario), pero cada pantalla que el LLM emite
# pertenece a una de estas 5 "clases" de estado, igual que en los diagramas
# de referencia (Intencion -> UI generada -> Interaccion -> Confirmacion ->
# Accion real). El frontend usa stage_kind para el icono/color del listón de
# progreso y stage_label para el texto corto que se muestra en cada paso.
StageKind = Literal["intent", "generated", "interaction", "confirmation", "result"]


class A2UIScreen(BaseModel):
    type: Literal["a2ui.screen"] = "a2ui.screen"
    id: str
    title: str
    subtitle: Optional[str] = None
    layout: Literal["stack", "grid"] = "stack"
    components: list[A2UIComponent]
    footer_actions: list[ActionSpec] = Field(default_factory=list)
    saveable: bool = True
    stage_kind: StageKind = "generated"
    stage_label: str = Field(default="UI generada", max_length=24)


class A2UIClarification(BaseModel):
    type: Literal["a2ui.clarify"] = "a2ui.clarify"
    id: str
    question: str
    input_mode: Literal["choice", "free_text", "both"] = "both"
    options: list[str] = Field(default_factory=list)
    stage_kind: StageKind = "intent"
    stage_label: str = Field(default="Intencion", max_length=24)


class A2UIEnvelope(BaseModel):
    mime_type: Literal["application/a2ui+json"] = "application/a2ui+json"
    payload: A2UIScreen | A2UIClarification
