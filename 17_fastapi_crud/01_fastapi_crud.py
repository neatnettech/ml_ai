# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Module 17 — FastAPI + SQLAlchemy: Build a REST API
#
# Welcome to the **Practical End-to-End** track. So far you have trained models
# *inside* notebooks. Now you learn to **expose code to the outside world** as a
# web service — the foundation of shipping anything real.
#
# This module teaches the backend trio every Python service is built on:
#
# 1. **FastAPI** — turn Python functions into HTTP endpoints
# 2. **Pydantic** — validate and serialize data crossing the wire
# 3. **SQLAlchemy 2.0** — talk to a database with Python objects, not raw SQL
#
# You will build a small **Notes API** with full CRUD (Create, Read, Update,
# Delete). A complete, runnable version lives in the `app/` folder next to this
# notebook — this notebook explains every piece and has `# TODO` exercises.
#
# > **You can run the cells here** to learn the concepts. To run the *server*,
# > use `app/` (see `app/README.md`): `uvicorn app.main:app --reload`.

# %% [markdown]
# ## Step 1: REST in 90 seconds
#
# A REST API maps **HTTP verbs** onto **resources** (here, "notes"):
#
# | Verb | Path | Meaning |
# |------|------|---------|
# | `POST` | `/notes` | create a note |
# | `GET` | `/notes` | list notes |
# | `GET` | `/notes/{id}` | read one note |
# | `PATCH` | `/notes/{id}` | update a note |
# | `DELETE` | `/notes/{id}` | delete a note |
#
# The server returns a **status code** (`200` ok, `201` created, `404` not found,
# `422` validation error) and usually a **JSON body**. That is the whole contract.

# %%
# Imports for this module. If these fail, install the backend deps:
#   pip install -r ../requirements.txt
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient  # lets us call the API without a real server
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Integer, String, Text, DateTime, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

print("Imports OK — FastAPI, Pydantic, SQLAlchemy ready.")

# %% [markdown]
# ## Step 2: Pydantic — the data contract
#
# Pydantic models declare *what valid data looks like*. FastAPI uses them to
# **validate input automatically** (bad input → `422` with a helpful message)
# and to **serialize output** to JSON.
#
# Notice we keep **input** and **output** schemas separate: a client should not
# send an `id` or `created_at` (the server assigns those), but the response
# includes them.

# %%
class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # read straight off ORM objects
    id: int
    title: str
    content: str
    created_at: datetime


# Validation in action: Pydantic rejects bad data before it reaches your logic.
good = NoteCreate(title="Shopping list", content="milk, eggs")
print("Valid:", good)

try:
    NoteCreate(title="")  # min_length=1 violated
except Exception as e:
    print("\nRejected empty title (this is good!):")
    print(type(e).__name__)

# %% [markdown]
# ### Exercise 2.1 — Add an update schema
#
# `PATCH` updates should let the client send **only the fields they want to
# change**. That means every field is optional. Define `NoteUpdate` with optional
# `title` and `content`.

# %%
# TODO: Define NoteUpdate with optional title and content.
# - title: str | None = None  (keep the min_length=1, max_length=200 when provided)
# - content: str | None = None
# Hint: Field(default=None, min_length=1, max_length=200)


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None


# Only the sent field appears — that is how PATCH knows what to change:
print(NoteUpdate(content="new text").model_dump(exclude_unset=True))

# %% [markdown]
# ## Step 3: SQLAlchemy — the database as Python objects
#
# An **ORM** (Object-Relational Mapper) lets you work with rows as Python objects
# instead of writing SQL strings. SQLAlchemy 2.0 uses typed `Mapped[...]` columns.
#
# Three pieces:
# - **`Base`** — the declarative base all models inherit from
# - **`engine`** — the connection to the database (SQLite here, zero setup)
# - **`SessionLocal`** — a factory for sessions (one short-lived session per request)

# %%
class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


# In-memory SQLite so the notebook stays self-contained and repeatable.
# StaticPool keeps ONE shared connection: an in-memory DB lives inside its
# connection, and FastAPI's TestClient runs routes on worker threads — without
# this they would each get a separate empty database.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)  # CREATE TABLE notes (...)

# Insert + query with objects, not SQL.
with SessionLocal() as db:
    db.add(Note(title="Hello", content="from SQLAlchemy"))
    db.commit()
    rows = db.scalars(select(Note)).all()
    print("Rows in DB:", [(r.id, r.title) for r in rows])

# %% [markdown]
# ## Step 4: The session dependency
#
# Every request needs a database session that is **opened, used, then closed** —
# even if the request errors. FastAPI's dependency injection makes this clean: a
# generator that `yield`s the session in a `try/finally`.

# %%
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# A route declares `db: Session = Depends(get_db)` and FastAPI runs this for you,
# injecting the session and closing it afterward. You never call get_db yourself.
print("get_db ready — FastAPI will inject a fresh session per request.")

# %% [markdown]
# ## Step 5: Wire up the API
#
# Now combine all three: routes take Pydantic input, use the injected session,
# and return ORM objects (auto-serialized via `NoteRead`). We build a mini app
# right here and exercise it with `TestClient` (no server process needed).

# %%
app = FastAPI(title="Notes API (notebook demo)")


@app.post("/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(data: NoteCreate, db: Session = Depends(get_db)):
    note = Note(title=data.title, content=data.content)
    db.add(note)
    db.commit()
    db.refresh(note)  # reload id + created_at the DB assigned
    return note


@app.get("/notes", response_model=list[NoteRead])
def list_notes(db: Session = Depends(get_db)):
    return list(db.scalars(select(Note).order_by(Note.id)))


@app.get("/notes/{note_id}", response_model=NoteRead)
def read_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


client = TestClient(app)

r = client.post("/notes", json={"title": "Buy milk", "content": "2L"})
print("POST  /notes      ->", r.status_code, r.json())

r = client.get("/notes")
print("GET   /notes      ->", r.status_code, r.json())

r = client.get("/notes/999")
print("GET   /notes/999  ->", r.status_code, r.json())  # 404 — note does not exist

# %% [markdown]
# ### Exercise 5.1 — Implement UPDATE and DELETE
#
# The app above only has Create/Read. Add the two missing operations:
#
# - `PATCH /notes/{note_id}` — update a note (use `NoteUpdate`, `exclude_unset`)
# - `DELETE /notes/{note_id}` — delete a note, return `204 No Content`
#
# Both must `404` if the note does not exist.

# %%
# TODO: Add update_note (PATCH) and delete_note (DELETE) routes to `app`.
#
# update_note:
#   - look up the note with db.get(Note, note_id); 404 if missing
#   - for field, value in data.model_dump(exclude_unset=True).items(): setattr(note, field, value)
#   - db.commit(); db.refresh(note); return note
#
# delete_note:
#   - look up the note; 404 if missing
#   - db.delete(note); db.commit()
#   - decorate with status_code=status.HTTP_204_NO_CONTENT


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
@app.patch("/notes/{note_id}", response_model=NoteRead)
def update_note(note_id: int, data: NoteUpdate, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")
    db.delete(note)
    db.commit()


# Exercise the full lifecycle:
client = TestClient(app)
created = client.post("/notes", json={"title": "Draft", "content": "v1"}).json()
nid = created["id"]
print("created:", created)

patched = client.patch(f"/notes/{nid}", json={"content": "v2"})
print("PATCH ->", patched.status_code, patched.json())

deleted = client.delete(f"/notes/{nid}")
print("DELETE ->", deleted.status_code, "(204 = success, empty body)")

missing = client.get(f"/notes/{nid}")
print("GET after delete ->", missing.status_code, "(404 expected)")

# %% [markdown]
# ## Step 6: Migrations (when the schema changes)
#
# `Base.metadata.create_all()` creates tables that do not exist yet — great for a
# demo, useless once you have live data and need to *add a column*. Real projects
# use **Alembic** to version the schema, like git for your database:
#
# ```bash
# alembic init migrations              # one-time setup
# alembic revision --autogenerate -m "add notes table"
# alembic upgrade head                 # apply pending migrations
# ```
#
# Each `revision` is a Python file with `upgrade()` / `downgrade()`. You do not
# need Alembic for this notebook — just know that `create_all` is the toy version
# and Alembic is what ships.

# %% [markdown]
# ## What you built
#
# - A **REST API** mapping HTTP verbs to a resource
# - **Pydantic** schemas validating input and serializing output (separate
#   create / update / read contracts)
# - **SQLAlchemy 2.0** ORM models + a per-request **session dependency**
# - Full **CRUD** wired together and tested with `TestClient`
#
# The runnable version is in `app/`. Launch it with
# `uvicorn app.main:app --reload` and open `/docs` for an interactive UI.
#
# **Next:** Module 18 — the cryptography that authentication is built on, so that
# in Module 19 you can lock these endpoints down.
