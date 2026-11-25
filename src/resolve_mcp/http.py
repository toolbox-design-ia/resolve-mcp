"""Serving over streamable HTTP, for an agent platform on another machine (Agents Factory).

Only with a token: every request carries `Authorization: Bearer <token>` or gets 401. The token
comes from RESOLVE_MCP_TOKEN or from a file only its owner reads (by default
~/.config/resolve-mcp/token); without one, or with a short one, the server does not start.
Listen on a private address (the tailnet one), never on all interfaces of a public network.
"""

from __future__ import annotations

import hmac
import os
import stat
from pathlib import Path

DEFAULT_TOKEN_FILE = Path.home() / ".config" / "resolve-mcp" / "token"
MIN_TOKEN = 32


class TokenError(RuntimeError):
    """No usable token: the HTTP server does not start."""


def read_token(path: Path | None = None) -> str:
    token = os.environ.get("RESOLVE_MCP_TOKEN", "").strip()
    if not token:
        path = path or DEFAULT_TOKEN_FILE
        if not path.exists():
            raise TokenError(f"no token: set RESOLVE_MCP_TOKEN or write one to {path} (chmod 600)")
        if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise TokenError(f"{path} can be read by others: chmod 600 {path}")
        token = path.read_text().strip()
    if len(token) < MIN_TOKEN:
        raise TokenError(f"the token is too short: at least {MIN_TOKEN} characters")
    return token


class BearerAuth:
    """ASGI: lets through only requests with the token. Compared in constant time."""

    def __init__(self, app, token: str) -> None:
        self.app, self.expected = app, f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            sent = dict(scope.get("headers") or []).get(b"authorization", b"")
            if not hmac.compare_digest(sent, self.expected):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json"), (b"www-authenticate", b"Bearer")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await self.app(scope, receive, send)


def build_app(token: str, host: str, port: int):
    from mcp.server.transport_security import TransportSecuritySettings

    from .server import mcp

    hosts = [host, f"{host}:{port}", "localhost", f"localhost:{port}", "127.0.0.1", f"127.0.0.1:{port}"]
    app = mcp.streamable_http_app(
        stateless_http=True,
        json_response=True,
        host=host,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=[]),
    )
    return BearerAuth(app, token)


def serve(host: str, port: int, token_file: Path | None = None) -> None:
    import uvicorn

    app = build_app(read_token(token_file), host, port)
    uvicorn.run(app, host=host, port=port, log_level="warning")
