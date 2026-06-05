"""FastAPI app — wires routes to the CRUD layer.

Run it:  uvicorn app.main:app --reload   (from inside 17_fastapi_crud/)
Docs at: http://127.0.0.1:8000/docs  (interactive, auto-generated from the schemas)
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db

# Create tables on startup. Fine for a demo; real projects use Alembic migrations
# (see the teaching notebook's "Migrations" section).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notes API", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/notes", response_model=schemas.NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(data: schemas.NoteCreate, db: Session = Depends(get_db)):
    return crud.create_note(db, data)


@app.get("/notes", response_model=list[schemas.NoteRead])
def list_notes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_notes(db, skip=skip, limit=limit)


@app.get("/notes/{note_id}", response_model=schemas.NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@app.patch("/notes/{note_id}", response_model=schemas.NoteRead)
def update_note(note_id: int, data: schemas.NoteUpdate, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")
    return crud.update_note(db, note, data)


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")
    crud.delete_note(db, note)
