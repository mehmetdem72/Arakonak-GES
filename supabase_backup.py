"""
Supabase otomatik yedek — Yol B.

SQLite ana veritabanı olarak çalışır (hızlı, mevcut kod korunur).
Her veri değişiminde tüm veri tek JSON olarak Supabase'e yedeklenir.
Uygulama açılışında (SQLite boşsa) Supabase'den son yedek geri yüklenir.

Secrets formatı (.streamlit/secrets.toml veya Cloud → Settings → Secrets):
    [supabase]
    db_url = "postgresql://postgres:PAROLA@db.xxxx.supabase.co:5432/postgres"

Veri kaybolmaz: Streamlit yeniden başlasa/uyusa bile Supabase'de son hal durur.
"""
import json
from datetime import datetime, timezone

_ENGINE = None
_ENABLED = None  # None=denenmedi, True/False


def _get_url():
    try:
        import streamlit as st
        if "supabase" in st.secrets and "db_url" in st.secrets["supabase"]:
            u = str(st.secrets["supabase"]["db_url"]).strip()
            return u or None
    except Exception:
        pass
    return None


def _engine():
    """Supabase (PostgreSQL) engine — yalnızca yedek tablosu için."""
    global _ENGINE, _ENABLED
    if _ENABLED is False:
        return None
    if _ENGINE is not None:
        return _ENGINE
    url = _get_url()
    if not url:
        _ENABLED = False
        return None
    try:
        from sqlalchemy import create_engine, text
        import re
        from urllib.parse import quote_plus
        # şifredeki özel karakterleri URL-encode et (*, @, / vb. sorun çıkarmasın)
        m = re.match(r'^(postgresql(?:\+psycopg2)?://[^:]+:)([^@]+)(@.+)$', url)
        if m:
            url = m.group(1) + quote_plus(m.group(2)) + m.group(3)
        if url.startswith("postgresql://") and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        eng = create_engine(url, pool_pre_ping=True, pool_recycle=300,
                            connect_args={"connect_timeout": 10})
        with eng.begin() as c:
            c.execute(text("""CREATE TABLE IF NOT EXISTS app_backup(
                id INTEGER PRIMARY KEY DEFAULT 1,
                data TEXT,
                updated_at TIMESTAMPTZ DEFAULT now())"""))
        _ENGINE = eng
        _ENABLED = True
        return eng
    except Exception:
        _ENABLED = False
        return None


def is_enabled():
    """Supabase yedeği aktif mi (bağlantı çalışıyor mu)."""
    return _engine() is not None


def push(data: dict) -> bool:
    """Tüm veriyi (export_all sözlüğü) Supabase'e yaz. Başarılıysa True."""
    eng = _engine()
    if eng is None:
        return False
    try:
        from sqlalchemy import text
        payload = json.dumps(data, ensure_ascii=False, default=str)
        with eng.begin() as c:
            c.execute(text("""INSERT INTO app_backup(id, data, updated_at)
                VALUES (1, :d, now())
                ON CONFLICT (id) DO UPDATE SET data=:d, updated_at=now()"""),
                {"d": payload})
        return True
    except Exception:
        return False


def pull():
    """Supabase'deki son yedeği (dict) döndür. Yoksa None."""
    eng = _engine()
    if eng is None:
        return None
    try:
        from sqlalchemy import text
        with eng.connect() as c:
            row = c.execute(text("SELECT data FROM app_backup WHERE id=1")).fetchone()
        if row and row[0]:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def last_updated():
    """Son yedek zamanı (str) veya None."""
    eng = _engine()
    if eng is None:
        return None
    try:
        from sqlalchemy import text
        with eng.connect() as c:
            row = c.execute(text("SELECT updated_at FROM app_backup WHERE id=1")).fetchone()
        return str(row[0]) if row else None
    except Exception:
        return None
