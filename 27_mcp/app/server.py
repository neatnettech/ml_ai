"""A runnable MCP server — the thing Claude (or any MCP host) connects to.

Built on `FastMCP`, the high-level server in the official `mcp` Python SDK. It
exposes the three MCP primitives:

  * **tools**     — functions the model may *call*   (`add`, `sql_safe_lookup`)
  * **resources** — data the host may *read*         (`notes://{note_id}`)
  * **prompts**   — reusable templates the host may *insert*  (`review_note`)

Transport is **stdio**: the host launches this file as a subprocess and talks
to it over stdin/stdout. No network, no ports — runs anywhere.

Run standalone (it will just wait for a client on stdio):
    cd 27_mcp && python -m app.server

Normally you don't run it directly — a host launches it. See `app/client.py`
for a minimal host, and `app/README.md` for wiring it into Claude.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# The server's name shows up in the host's tool list. Keep it stable — hosts
# key their config off it.
mcp = FastMCP("module27-demo")


# --- A tiny notes store, tying back to Module 17 -----------------------------
# If you ran Module 17's API it left a `notes.db` SQLite file. We reuse it when
# present so the two modules connect; otherwise we fall back to a seeded dict so
# this server always works on its own.
_NOTES_DB = Path(__file__).resolve().parents[2] / "17_fastapi_crud" / "notes.db"
_SEED_NOTES = {
    1: "MCP gives an LLM tools, resources, and prompts over one protocol.",
    2: "stdio transport = the host launches the server as a subprocess.",
}


def _read_note(note_id: int) -> str | None:
    """Return a note's content by id, from Module 17's DB or the seed fallback."""
    if _NOTES_DB.exists():
        # read-only; never trust the path beyond our own file
        con = sqlite3.connect(f"file:{_NOTES_DB}?mode=ro", uri=True)
        try:
            row = con.execute(
                "SELECT content FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            if row:
                return row[0]
        except sqlite3.Error:
            pass  # table shape differs — fall through to the seed
        finally:
            con.close()
    return _SEED_NOTES.get(note_id)


# --- Tools: functions the model may call -------------------------------------
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum.

    Type hints are not decoration — FastMCP turns them into the tool's JSON
    Schema, so the host knows `a` and `b` must be numbers. This is the same
    Pydantic-style validation you used for request bodies in Module 17.
    """
    return a + b


@mcp.tool()
def note_lookup(note_id: int) -> str:
    """Look up a note by integer id (reuses Module 17's `notes.db` if present).

    Note inputs are **untrusted** (Modules 18/23): we accept only an `int` id
    and use a *parameterized* query — never string-formatted SQL — so a crafted
    id can't inject. Compare to the SQLi lessons in Module 23.
    """
    content = _read_note(note_id)
    if content is None:
        raise ValueError(f"no note with id {note_id}")
    return content


# --- Resource: data the host may read ----------------------------------------
@mcp.resource("notes://{note_id}")
def note_resource(note_id: str) -> str:
    """Expose a note as a readable *resource* (addressed by a URI).

    Tools *do* things; resources *are* context the host can pull in. Same data,
    different primitive — pick resources for "here is content to read."
    """
    content = _read_note(int(note_id))
    return content if content is not None else f"(no note {note_id})"


# --- Prompt: a reusable template the host may insert -------------------------
@mcp.prompt()
def review_note(note_id: int) -> str:
    """A ready-made prompt asking the model to review a given note."""
    return (
        f"Read note #{note_id} via the note_lookup tool, then summarize it in one "
        f"sentence and flag anything unclear."
    )


if __name__ == "__main__":
    # Default transport is stdio. `mcp.run("sse")` would serve over HTTP instead.
    mcp.run()
