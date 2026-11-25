"""HTTP with a token, without Resolve: refused without the token, tools listed with it."""

import os
import stat

import httpx2 as httpx
import pytest

from resolve_mcp import http

TOKEN = "t" * 40


def test_without_a_token_it_does_not_start(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("RESOLVE_MCP_TOKEN", raising=False)
    with pytest.raises(http.TokenError):
        http.read_token(tmp_path / "missing")
    short = tmp_path / "short"
    short.write_text("abc")
    short.chmod(0o600)
    with pytest.raises(http.TokenError):
        http.read_token(short)
    shared = tmp_path / "shared"
    shared.write_text(TOKEN)
    shared.chmod(0o644)
    with pytest.raises(http.TokenError):
        http.read_token(shared)
    good = tmp_path / "good"
    good.write_text(TOKEN + "\n")
    good.chmod(stat.S_IRUSR | stat.S_IWUSR)
    assert http.read_token(good) == TOKEN
    monkeypatch.setenv("RESOLVE_MCP_TOKEN", "e" * 40)
    assert http.read_token(good) == "e" * 40


async def test_only_with_the_token() -> None:
    app = http.build_app(TOKEN, "127.0.0.1", 8765)
    inner = app.app
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-06-18"}
    async with inner.router.lifespan_context(inner):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8765") as c:
            r = await c.post("/mcp", json=body, headers=headers)
            assert r.status_code == 401
            r = await c.post("/mcp", json=body, headers={**headers, "Authorization": "Bearer otra"})
            assert r.status_code == 401
            r = await c.post("/mcp", json=body, headers={**headers, "Authorization": f"Bearer {TOKEN}"})
            assert r.status_code == 200, r.text
            names = {t["name"] for t in r.json()["result"]["tools"]}
            assert {"get_status", "execute_python"} <= names
