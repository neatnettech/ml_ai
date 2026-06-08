"""CRUD functions — the data-access layer.

Pure database logic, no FastAPI here. Keeping it separate from the routes means
you can test it without a web server and reuse it anywhere.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas


def create_note(db: Session, data: schemas.NoteCreate) -> models.Note:
    note = models.Note(title=data.title, content=data.content)
    db.add(note)
    db.commit()
    db.refresh(note)  # reload server-generated fields (id, created_at)
    return note


def get_note(db: Session, note_id: int) -> models.Note | None:
    return db.get(models.Note, note_id)


def list_notes(db: Session, skip: int = 0, limit: int = 100) -> list[models.Note]:
    stmt = select(models.Note).offset(skip).limit(limit).order_by(models.Note.id)
    return list(db.scalars(stmt))


def update_note(db: Session, note: models.Note, data: schemas.NoteUpdate) -> models.Note:
    # exclude_unset: only overwrite fields the client actually sent (PATCH semantics).
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note: models.Note) -> None:
    db.delete(note)
    db.commit()
