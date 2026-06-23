# Demo MCP server — runnable Model Context Protocol project

A small `FastMCP` server (tools + resource + prompt) backing the Module 27
teaching notebook, plus a minimal client that drives it over **stdio**.

## Run the client (which launches the server for you)

```bash
cd 27_mcp
python -m app.client
```

Expected output:

```
tools: ['add', 'note_lookup']
add(2, 3) -> 5.0
note_lookup(1) -> MCP gives an LLM tools, resources, and prompts over one protocol.
```

The server is normally not run by hand — a **host** launches it as a subprocess.
`app/client.py` is the smallest possible host. To run the server alone (it will
wait on stdio for a client):

```bash
cd 27_mcp && python -m app.server
```

## Connect it to Claude

Register the server with Claude Code so the model can call its tools:

```bash
# from the 27_mcp folder so the relative path resolves
claude mcp add module27-demo -- python -m app.server
```

Or add it to a host config (e.g. `claude_desktop_config.json`) by hand:

```json
{
  "mcpServers": {
    "module27-demo": {
      "command": "python",
      "args": ["-m", "app.server"],
      "cwd": "/absolute/path/to/27_mcp"
    }
  }
}
```

Restart the host, then ask Claude to "add 2 and 3 with the module27-demo tool" —
it will discover and call `add`. This is the same mechanism that loads the
session's own MCP servers (dev-assistant, stripe, supabase).

## Layout

| File | Role |
|------|------|
| `server.py` | `FastMCP` server — `add` / `note_lookup` tools, `notes://{id}` resource, `review_note` prompt |
| `client.py` | minimal stdio host — initialize, list tools, call them |
| `__init__.py` | marks `app/` as a package so `python -m app.server` works |

`note_lookup` reuses Module 17's `notes.db` when present, else a seeded fallback —
so it runs whether or not you completed the backend track.
