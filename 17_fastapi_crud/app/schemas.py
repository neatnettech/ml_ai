"""Pydantic schemas — the API's data contract (validation + serialization).

Keep these SEPARATE from the ORM models. ORM models = how data is stored;
schemas = how data crosses the wire. NoteCreate is what a client sends;
NoteRead is what the API returns.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None


class NoteRead(BaseModel):
    # from_attributes lets Pydantic read straight off an ORM object.
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
