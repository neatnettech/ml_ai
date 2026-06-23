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
# # Module 27 — Model Context Protocol: Give an LLM Hands
#
# **Purpose:** You've shipped a model behind an authenticated REST API (Module 20).
# A REST API serves *people and programs*. This module serves a different caller — a
# **large language model**. The **Model Context Protocol (MCP)** is the open standard
# that lets a model like Claude discover and call *your* tools, read *your* data, and
# reuse *your* prompts — over one protocol instead of bespoke glue per integration.
#
# **Prerequisites:** Module 17 (FastAPI/Pydantic — MCP reuses the same "typed inputs,
# validated at the boundary" idea); solid Python (Module 1). A little `async`/`await`
# helps but the cells explain it as they go.
#
# Welcome to the **Agents & Tooling** track. The backend track taught you to expose code
# to *the web*. MCP exposes capabilities to *a model* — the foundation of every useful
# AI agent. By the end you'll have built a server with all three MCP primitives and a
# client that drives it, and you'll know how to register it with Claude.
#
# > A complete, runnable version lives in the `app/` folder next to this notebook — this
# > notebook explains every piece and has `# TODO` exercises. To run the *server + client*
# > as separate processes (the real setup), see `app/README.md`.

# %% [markdown]
# ## Step 0: Is the SDK installed?
#
# Everything here uses the official **`mcp`** Python SDK. If it's missing, install the
# backend/agents deps: `pip install -r ../requirements.txt` (or `pip install "mcp>=1.2"`).
# The notebook is guarded so it *runs top to bottom either way* — concept cells always
# work; live cells skip with a note when the SDK is absent (same pattern as the GPU-guarded
# cells elsewhere in the catalog).

# %%
try:
    from mcp.server.fastmcp import FastMCP

    HAVE_MCP = True
    print("mcp SDK ready — live cells will run.")

    # Small helpers so output reads cleanly. The server's async API returns rich
    # objects (a model needs the structure); we just pull the text for display.
    def tool_text(result):
        """Unwrap a call_tool result to its text payload."""
        content = result[0] if isinstance(result, tuple) else result
        return content[0].text

    def resource_text(result):
        """Unwrap a read_resource result to its text payload."""
        return list(result)[0].content
except ImportError:
    HAVE_MCP = False
    print("mcp SDK not installed — concept cells run; live cells will skip.")
    print('Install with:  pip install "mcp>=1.2"')

# %% [markdown]
# ## Step 1: What MCP actually is
#
# MCP has three roles:
#
# | Role | Who | Example |
# |------|-----|---------|
# | **Host** | the app the user talks to | Claude Desktop, Claude Code |
# | **Client** | one connection inside the host | the host opens one per server |
# | **Server** | *your* program exposing capabilities | the one you build below |
#
# The host speaks to each server through a client. **You write servers.** The win is
# standardization: write one MCP server and *any* MCP host can use it — no custom
# integration per model or per app. It's "USB-C for LLM tools."
#
# A server exposes **three primitives**:
#
# | Primitive | The model... | Closest REST analogy |
# |-----------|--------------|----------------------|
# | **Tool** | *calls* it to do something | `POST` an action |
# | **Resource** | *reads* it for context | `GET` a document |
# | **Prompt** | *inserts* a reusable template | a saved request body |
#
# Rule of thumb: **tools do, resources are, prompts template.**

# %% [markdown]
# ## Step 2: A server in a dozen lines
#
# `FastMCP` is the high-level server. You register a tool with a decorator — and your
# **type hints become the tool's schema**, exactly like Pydantic request models in
# Module 17. The model sees that `a` and `b` must be numbers and validates before calling.

# %%
if HAVE_MCP:
    demo = FastMCP("notebook-demo")

    @demo.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers and return the sum."""
        return a + b

    @demo.tool()
    def greet(name: str) -> str:
        """Return a friendly greeting."""
        return f"Hello, {name}!"

    print("Server 'notebook-demo' built with 2 tools: add, greet")
else:
    print("(skipped — no mcp SDK)")

# %% [markdown]
# ## Step 3: Discover and call tools (what the model does)
#
# A host first **lists** the tools a server offers (so the model knows what exists), then
# **calls** one by name with arguments. We do both here *in-process* — no subprocess
# needed — using the server object's async API. (`await` works at the top level in
# Jupyter; in a plain script you'd wrap these in `asyncio.run(...)`.)

# %%
if HAVE_MCP:
    tools = await demo.list_tools()
    print("tools the host would see:", [t.name for t in tools])

    result = await demo.call_tool("add", {"a": 2, "b": 3})
    print("add(2, 3) ->", tool_text(result))
else:
    print("(skipped — no mcp SDK)")

# %% [markdown]
# Notice you never imported `add` to call it — you asked the **server** to run the tool
# named `"add"`. That indirection is the whole point: the model picks a name and arguments
# at runtime; the protocol carries the call.

# %% [markdown]
# ## Step 4: Resources and prompts
#
# A **resource** is addressable context the host can read, identified by a URI template.
# A **prompt** is a reusable instruction the host can drop in. Tools act; these two supply
# *content*.

# %%
if HAVE_MCP:
    _DOCS = {"intro": "MCP standardizes how a model reaches tools, data, and prompts."}

    @demo.resource("doc://{name}")
    def doc(name: str) -> str:
        """Expose a named document as readable context."""
        return _DOCS.get(name, f"(no doc '{name}')")

    @demo.prompt()
    def summarize(name: str) -> str:
        """A reusable prompt that asks the model to summarize a doc."""
        return f"Read the doc://{name} resource and summarize it in one sentence."

    print("resource doc://{name} and prompt summarize registered")
    print("doc://intro ->", resource_text(await demo.read_resource("doc://intro")))
else:
    print("(skipped — no mcp SDK)")

# %% [markdown]
# ## Step 5: Transports — how host and server talk
#
# | Transport | How | Use when |
# |-----------|-----|----------|
# | **stdio** | host launches the server as a subprocess, talks over stdin/stdout | local tools (our labs) — zero network, runs anywhere |
# | **HTTP / SSE** | server runs as a web service the host connects to | remote/shared servers, multiple clients |
#
# `app/server.py` uses **stdio**: `mcp.run()` defaults to it. Switching to remote is one
# argument — `mcp.run("sse")` — but stdio keeps these labs setup-free. The `app/` folder
# splits the server and a real **client** into separate processes (the production shape);
# this notebook ran them in one process to teach the moving parts.

# %% [markdown]
# ## Step 6: Connect it to Claude
#
# Registering the runnable server with Claude Code is one command (run from `27_mcp/` so
# the relative module path resolves):
#
# ```bash
# claude mcp add module27-demo -- python -m app.server
# ```
#
# Or add it to a host config like `claude_desktop_config.json`:
#
# ```json
# {
#   "mcpServers": {
#     "module27-demo": {
#       "command": "python",
#       "args": ["-m", "app.server"],
#       "cwd": "/absolute/path/to/27_mcp"
#     }
#   }
# }
# ```
#
# Then ask Claude to "add 2 and 3 with the module27-demo tool" — it discovers and calls
# `add`. **This is the exact mechanism** that loads this very session's MCP servers
# (dev-assistant, stripe, supabase). You've now been on both ends of the protocol.

# %% [markdown]
# ## Step 7: Tool inputs are untrusted (security)
#
# A tool is a callable you've handed to a model — treat every argument as hostile input,
# the same lesson as the crypto/auth/web modules (18, 19, 23):
#
# - **Validate with types/Pydantic.** Let the schema reject impossible inputs (`422`-style)
#   *before* your code runs — that's what the hints in Step 2 buy you.
# - **Never `eval`/`exec` an argument**, and never string-format it into SQL or a shell.
#   `app/server.py`'s `note_lookup` uses a *parameterized* query — compare the SQLi lesson
#   in Module 23.
# - **Scope access.** Open files/DBs read-only; don't expose a "run any SQL" or "read any
#   path" tool. Least privilege, like Module 19's auth in front of compute.
#
# A tool is an *API endpoint with a model on the other side*. Harden it like one.

# %% [markdown]
# ## Exercises
#
# Work in this notebook, then port your favorite into `app/server.py` and call it from
# `app/client.py`.

# %%
# TODO 1: Add a `multiply(a: float, b: float) -> float` tool to the `demo` server,
#         then list the tools and confirm it appears. (Mirror the `add` cell.)


# %%
# TODO 2: Add a resource `time://now` that returns a fixed string like
#         "2026-06-23T12:00:00Z" (a constant — Date.now() is intentionally avoided
#         in this catalog). Read it back with `await demo.read_resource(...)`.


# %%
# TODO 3: Call a tool *by a name stored in a variable* — set
#         `tool_name = "greet"` and `await demo.call_tool(tool_name, {"name": "MCP"})`.
#         This is exactly how a model invokes tools: name + args chosen at runtime.


# %% [markdown]
# ### Solutions (reveal after trying)

# %%
if HAVE_MCP:
    # TODO 1
    @demo.tool()
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    print("after adding multiply:", [t.name for t in await demo.list_tools()])

    # TODO 2
    @demo.resource("time://now")
    def now() -> str:
        """A fixed timestamp (constant by catalog convention)."""
        return "2026-06-23T12:00:00Z"

    print("time://now ->", resource_text(await demo.read_resource("time://now")))

    # TODO 3
    tool_name = "greet"
    print("dynamic call ->", tool_text(await demo.call_tool(tool_name, {"name": "MCP"})))
else:
    print("(skipped — no mcp SDK)")

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | **Host / client / server** | You write servers; any MCP host can then use them |
# | **Three primitives** | tools *do*, resources *are*, prompts *template* |
# | **Type hints = schema** | the model validates arguments before calling — Module 17's idea, for an LLM |
# | **stdio vs HTTP/SSE** | local subprocess vs remote service; stdio keeps tools zero-setup |
# | **Register with Claude** | `claude mcp add` is how this session's own servers load |
# | **Tools are untrusted boundaries** | validate, parameterize, scope — Modules 18/19/23 apply |
#
# ## Further reading
#
# - **MCP specification** (the protocol itself): https://modelcontextprotocol.io/
# - **MCP Python SDK** (`FastMCP`, client, transports):
#   https://github.com/modelcontextprotocol/python-sdk
# - **Example servers** (filesystem, git, sqlite, fetch — patterns to copy):
#   https://github.com/modelcontextprotocol/servers
# - **Claude Code — MCP** (registering and using servers):
#   https://docs.anthropic.com/en/docs/claude-code/mcp
#
# ---
# 🎉 **You finished the Agents & Tooling track.** You can now expose any capability to a
# model through one standard protocol — and you've seen both ends of it, since this very
# session runs on MCP servers. From "train a model" (Modules 1–10) to "ship it behind an
# API" (17–20) to "hand it to an agent" (27): that's the full arc.
