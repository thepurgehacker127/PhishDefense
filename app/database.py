# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Prefer explicit DATABASE_URL if present; otherwise build from POSTGRES_* envs
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    DB_USER = os.getenv("POSTGRES_USER", "phish")
    DB_PW = os.getenv("POSTGRES_PASSWORD", "phishpw")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "phishdb")
    DB_URL = f"postgresql+psycopg://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine/session + declarative Base
if DB_URL.startswith("sqlite"):
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DB_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# <-- THIS is the symbol Alembic needs to import
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()