# resolve-mcp

MCP server for **DaVinci Resolve Studio 21** with full coverage of the scripting API — 130+
tools: dedicated tools for projects, media storage, media pool, clips, timelines, tracks, items,
markers, color nodes / LUTs / CDL / versions / groups / gallery, Fusion comps, Fairlight, AI
features and rendering; `call_api` / `call_api_batch` for any other API method, API discovery
tools that read the scripting stubs and README installed with Resolve, and `execute_python` as a
last resort.

```
Agent ── MCP (stdio) ──> resolve-mcp (Python ≥ 3.11) ── fusionscript ──> DaVinci Resolve Studio
```

## Requirements

- DaVinci Resolve **Studio** 21.x running on the same machine, with
  *Preferences > System > General > External scripting using* set to **Local**.
- [uv](https://docs.astral.sh/uv/).

## Install

1. In Resolve: *Preferences > System > General > External scripting using* = **Local**.
2. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Check the connection (Resolve open):

   ```bash
   uvx --from git+https://github.com/toolbox-design-ia/resolve-mcp resolve-mcp status
   ```

4. Register the server with your agent. Desktop apps don't always inherit your shell `PATH`, so
   use uvx's full path (`which uvx`).

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "resolve": {
      "command": "/Users/YOU/.local/bin/uvx",
      "args": ["--from", "git+https://github.com/toolbox-design-ia/resolve-mcp", "resolve-mcp"]
    }
  }
}
```

**Claude Code**

```bash
claude mcp add resolve -- uvx --from git+https://github.com/toolbox-design-ia/resolve-mcp resolve-mcp
```

**OpenAI Codex CLI** (`~/.codex/config.toml`):

```toml
[mcp_servers.resolve]
command = "uvx"
args = ["--from", "git+https://github.com/toolbox-design-ia/resolve-mcp", "resolve-mcp"]
```

Restart the app after editing its configuration. `resolve-mcp tools` lists every tool.

Environment variables: `RESOLVE_SCRIPT_LIB` (path to fusionscript) and `RESOLVE_SCRIPT_API`
(Resolve's Developer/Scripting folder), both auto-detected on macOS, Windows and Linux;
`RESOLVE_HOST` (connect to a Resolve on another machine with network
scripting enabled).

## Addressing objects

| Reference | Object |
|---|---|
| `project`, `media_pool`, `media_storage`, `gallery`, `resolve`, `project_manager`, `fusion` | singletons |
| `timeline`, `timeline:<uid or name>` | current / given timeline |
| `item:<uid>` | timeline item |
| `clip:<uid>`, `clip:Master/Bin/name.mov`, `clip:<name>` | media pool item |
| `folder:Master/Bin` | media pool bin |
| `graph:item:<uid>[:layer]`, `graph:timeline`, `graph:group:<name>:pre\|post` | node graph |
| `color_group:<name>`, `album:still:<n>`, `album:powergrade:<n>`, `comp:<item uid>:<n>` | other |
| `handle:<n>` | any other object returned earlier |

Inside `call_api` arguments, objects are `{"$ref": "..."}` and constants `{"$const": "EXPORT_EDL"}`.

## Development

```bash
uv run pytest                          # offline tests
uv run python scripts/live_check.py    # read-only checks against a running Resolve
uv run python scripts/edit_check.py    # builds and deletes a throw-away project
```

## License

Freeware, © 2026 Toolbox Design — see [LICENSE](LICENSE). DaVinci Resolve is a trademark of
Blackmagic Design; this project is not affiliated with Blackmagic Design.
