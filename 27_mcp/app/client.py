"""A minimal MCP host — the smallest thing that drives `app/server.py`.

This is what Claude Desktop / Claude Code do under the hood: launch the server
as a stdio subprocess, run the MCP handshake, then list and call tools.

Run it (from the module folder so `app` is importable):
    cd 27_mcp && python -m app.client

Expected output: the server's tool names, then a couple of tool-call results.
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    # Tell the client *how* to launch the server. Same Python, run as a module.
    params = StdioServerParameters(command="python", args=["-m", "app.server"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            # The MCP handshake: exchange capabilities before anything else.
            await session.initialize()

            # 1. Discover what the server offers.
            tools = await session.list_tools()
            print("tools:", [t.name for t in tools.tools])

            # 2. Call a tool by name with arguments (the model does exactly this).
            result = await session.call_tool("add", {"a": 2, "b": 3})
            print("add(2, 3) ->", result.content[0].text)

            note = await session.call_tool("note_lookup", {"note_id": 1})
            print("note_lookup(1) ->", note.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
