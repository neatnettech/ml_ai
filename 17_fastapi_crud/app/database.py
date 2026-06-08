"""Database setup — engine, session factory, and the declarative Base.

SQLite by default so this runs anywhere with zero setup. Point DATABASE_URL at
Postgres (e.g. postgresql+psycopg://user:pass@host/db) and nothing else changes —
that is the whole point of an ORM.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")

# check_same_thread is a SQLite-only quirk: FastAPI uses multiple threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base all ORM models inherit from."""


def get_db():
    """FastAPI dependency: yield a session, always close it.

    Used as `db: Session = Depends(get_db)` in path operations. The try/finally
    guarantees the connection returns to the pool even if the request errors.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
