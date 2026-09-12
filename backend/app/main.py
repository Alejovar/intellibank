import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .seed import seed_if_empty
from .llm import mcp_client
from .routers import accounts, actions, auth, chat

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(
    title="Banorte AI - Backend generativo (A2UI)",
    description="Backend de demo para hackathon: orquesta un LLM que emite "
                 "pantallas via el protocolo A2UI sobre un catalogo cerrado "
                 "de componentes React.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    seed_if_empty()
    mcp_client.start()


@app.on_event("shutdown")
def on_shutdown():
    mcp_client.shutdown()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(actions.router)
app.include_router(accounts.router)
