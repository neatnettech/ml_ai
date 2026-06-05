# Notes API — runnable FastAPI + SQLAlchemy project

A small CRUD service backing the Module 17 teaching notebook.

## Run

```bash
cd 17_fastapi_crud
uvicorn app.main:app --reload
```

- Interactive docs: http://127.0.0.1:8000/docs
- A `notes.db` SQLite file is created on first run.

## Example calls

```bash
# health
curl http://127.0.0.1:8000/health

# create
curl -X POST http://127.0.0.1:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "First note", "content": "hello"}'

# list
curl http://127.0.0.1:8000/notes

# read one
curl http://127.0.0.1:8000/notes/1

# update (PATCH — send only what changes)
curl -X PATCH http://127.0.0.1:8000/notes/1 \
  -H "Content-Type: application/json" \
  -d '{"content": "edited"}'

# delete
curl -X DELETE http://127.0.0.1:8000/notes/1 -i
```

## Layout

| File | Role |
|------|------|
| `database.py` | engine, `SessionLocal`, `Base`, `get_db` dependency |
| `models.py` | SQLAlchemy ORM model (`Note` table) |
| `schemas.py` | Pydantic request/response contracts |
| `crud.py` | data-access functions (no web code) |
| `main.py` | FastAPI routes wiring schemas → crud |

Use Postgres instead of SQLite by setting `DATABASE_URL`.
