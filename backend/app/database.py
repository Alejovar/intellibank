from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_sqlite_schema() -> None:
    """Agrega columnas nuevas en la DB local de la demo sin borrar datos."""
    if not settings.database_url.startswith("sqlite"):
        return
    additions = {
        "users": {
            "email": "VARCHAR",
            "phone": "VARCHAR",
            "card_number_hash": "VARCHAR",
            "card_last4": "VARCHAR",
            "biometric_enabled": "BOOLEAN NOT NULL DEFAULT 0",
            "created_at": "DATETIME",
        },
        "investments": {
            "product_id": "VARCHAR",
            "current_value": "FLOAT",
            "opened_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "session_states": {
            "active_module": "VARCHAR NOT NULL DEFAULT 'investments'",
            "flow_id": "VARCHAR",
            "active_intent": "VARCHAR",
            "current_state": "VARCHAR NOT NULL DEFAULT 'READY'",
            "context_json": "JSON",
        },
        "auth_devices": {
            "credential_public_key": "BLOB",
            "sign_count": "INTEGER NOT NULL DEFAULT 0",
            "transports": "JSON",
        },
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in additions.items():
            if table not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(text(
                        f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}'
                    ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
