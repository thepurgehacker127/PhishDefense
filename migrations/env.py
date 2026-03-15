from __future__ import annotations
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import os, sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is on sys.path (…/PhishDefense)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load environment variables
load_dotenv()

# Import your metadata
from app.database import Base  # noqa: E402
from app import models         # noqa: F401,E402  (register models with Base)

# Alembic Config object
config = context.config
fileConfig(config.config_file_name)

def get_url():
    # Prefer DATABASE_URL if provided
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    user = os.getenv("POSTGRES_USER", "phish")
    pw   = os.getenv("POSTGRES_PASSWORD", "phishpw")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db   = os.getenv("POSTGRES_DB", "phishdb")
    return f"postgresql+psycopg://{user}:{pw}@{host}:{port}/{db}"

def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=Base.metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()