"""
Veritabanı arka ucu — Supabase (PostgreSQL, kalıcı) veya SQLite (yerel yedek).

Streamlit Secrets'ta [supabase] db_url varsa Supabase kullanılır, yoksa SQLite.
Secrets formatı (.streamlit/secrets.toml veya Cloud → Settings → Secrets):
    [supabase]
    db_url = "postgresql://postgres:PAROLA@db.xxxx.supabase.co:5432/postgres"
"""
from pathlib import Path

_ENGINE = None
_MODE = None


def _secret_url():
    try:
        import streamlit as st
        if "supabase" in st.secrets and "db_url" in st.secrets["supabase"]:
            u = str(st.secrets["supabase"]["db_url"]).strip()
            return u or None
    except Exception:
        pass
    return None


def get_engine(sqlite_path="data/arakonak.db"):
    global _ENGINE, _MODE
    if _ENGINE is not None:
        return _ENGINE, _MODE
    from sqlalchemy import create_engine
    url = _secret_url()
    if url:
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        _ENGINE = create_engine(url, pool_pre_ping=True, pool_recycle=300,
                                connect_args={"connect_timeout": 10})
        _MODE = "supabase"
    else:
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        _ENGINE = create_engine(f"sqlite:///{sqlite_path}")
        _MODE = "sqlite"
    return _ENGINE, _MODE


def is_postgres():
    return _MODE == "supabase"


def current_mode():
    return _MODE or "sqlite"
