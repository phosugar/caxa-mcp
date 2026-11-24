"""Portable entry point and configuration snippets for local MCP clients."""

import argparse
import json
from pathlib import Path
import sys

from . import __version__


def _launcher():
    entry = Path(sys.argv[0]).resolve()
    # Windows packaging launchers can strip ".exe" from argv[0].
    if entry.name.lower() == "caxa-mcp":
        entry = entry.with_suffix(".exe")
    if entry.name.lower() == "caxa-mcp.exe" and entry.is_file():
        return [entry.as_posix()]
    return [Path(sys.executable).as_posix(), "-m", "caxa_mcp.server"]


def _quote(value):
    return json.dumps(value, ensure_ascii=False)


def _configuration(client, command, caxa_path):
    program, *args = command
    env = {"CAXA_PATH": caxa_path} if caxa_path else {}
    entry = {"command": program, "args": args}
    if env:
        entry["env"] = env

    if client == "codex":
        lines = ["[mcp_servers.caxa]", f"command = {_quote(program)}"]
        if args:
            lines.append(f"args = {_quote(args)}")
        if caxa_path:
            lines.extend(("", "[mcp_servers.caxa.env]", f"CAXA_PATH = {_quote(caxa_path)}"))
        return "\n".join(lines)

    if client == "vscode":
        config = {"servers": {"caxa": {"type": "stdio", **entry}}}
    elif client == "opencode":
        local = {"type": "local", "command": command}
        if env:
            local["environment"] = env
        config = {"mcp": {"servers": {"caxa": local}}}
    else:
        config = {"mcpServers": {"caxa": entry}}
    return json.dumps(config, ensure_ascii=False, indent=2)


def run(controller, start_server):
    parser = argparse.ArgumentParser(prog="caxa-mcp", description="Local CAXA MCP server for Windows.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    mode.add_argument("--check", action="store_true", help="Report CAXA installation and window status.")
    mode.add_argument(
        "--config",
        choices=("generic", "codex", "vscode", "opencode"),
        help="Print a local MCP configuration snippet for the selected client.",
    )
    options = parser.parse_args()
    if not options.check and options.config is None:
        start_server()
        return 0

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if options.check:
        status = controller.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0 if status["installed"] else 1

    path = Path(controller.caxa_path)
    print(_configuration(options.config, _launcher(), path.as_posix() if path.is_file() else None))
    return 0
