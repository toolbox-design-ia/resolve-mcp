"""Command line: `resolve-mcp` (serve over stdio), `resolve-mcp serve --http` (over HTTP, with a token),
`resolve-mcp status`, `resolve-mcp tools`."""

from __future__ import annotations

import argparse
import json
import sys


def _status() -> int:
    from .connection import ResolveConnectionError, get_resolve, run_sync

    def probe():
        r = get_resolve()
        pm = r.GetProjectManager()
        p = pm.GetCurrentProject()
        return {"product": r.GetProductName(), "version": r.GetVersionString(), "studio": r.IsStudio(), "project": p.GetName() if p else None}

    try:
        print(json.dumps(run_sync(probe), indent=2))
        return 0
    except ResolveConnectionError as exc:
        print(f"Not connected: {exc}", file=sys.stderr)
        return 1


def _tools() -> int:
    import anyio

    from .server import mcp

    async def main() -> None:
        from mcp.client import Client

        async with Client(mcp) as client:
            tools = (await client.list_tools()).tools
        for t in tools:
            print(f"{t.name:32} {(t.description or '').splitlines()[0][:90]}")
        print(f"\n{len(tools)} tools")

    anyio.run(main)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="resolve-mcp", description="MCP server for DaVinci Resolve Studio")
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "status", "tools"])
    parser.add_argument("--http", action="store_true", help="serve over streamable HTTP at /mcp, with a token, instead of stdio")
    parser.add_argument("--host", default="127.0.0.1", help="address to listen on with --http (a private one, e.g. the tailnet's)")
    parser.add_argument("--port", type=int, default=8765, help="port with --http (8765)")
    parser.add_argument("--token-file", help="file with the token (default ~/.config/resolve-mcp/token; RESOLVE_MCP_TOKEN wins)")
    args = parser.parse_args(argv)
    if args.command == "status":
        sys.exit(_status())
    if args.command == "tools":
        sys.exit(_tools())
    if args.http:
        from pathlib import Path

        from .http import TokenError, serve

        try:
            serve(args.host, args.port, Path(args.token_file).expanduser() if args.token_file else None)
        except TokenError as exc:
            print(f"resolve-mcp: {exc}", file=sys.stderr)
            sys.exit(2)
        return
    from .server import mcp

    mcp.run("stdio")
