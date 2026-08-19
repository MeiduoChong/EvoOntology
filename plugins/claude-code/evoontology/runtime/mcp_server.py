"""Dependency-free stdio MCP server for the active EvoOntology workspace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

if __package__:
    from ..workspace import resolve_workspace
    from .runtime import SemanticLayer
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from evoontology.runtime.runtime import SemanticLayer
    from evoontology.workspace import resolve_workspace

_RESOURCE_URI = "evo-semantic://session-manifest"
_TOOLS = [
    {
        "name": "browse_semantics",
        "description": "Discover semantic concepts relevant to an analytical need.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "kind": {
                    "type": "string",
                    "enum": ["term", "mapping", "relation", "constraint", "all"],
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 6},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "resolve_semantics",
        "description": "Resolve selected concepts to grounded mappings and linked objects.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mentions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                },
                "context": {"type": "string"},
            },
            "required": ["mentions"],
            "additionalProperties": False,
        },
    },
]


class SemanticMCPServer:
    """Serve the two semantic tools over newline-delimited JSON-RPC."""

    def __init__(self, store_path: str):
        self.layer = SemanticLayer.load(store_path)

    def dispatch(self, method: str, params: Dict[str, Any]) -> Any:
        if method == "initialize":
            return {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "evo-semantic-mcp", "version": "1.0.0"},
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": _TOOLS}
        if method == "tools/call":
            name = str(params.get("name", ""))
            arguments = params.get("arguments", {})
            if name not in {"browse_semantics", "resolve_semantics"}:
                result = {"status": "error", "message": f"Unknown tool: {name}"}
                is_error = True
            else:
                try:
                    result = self.layer.execute(name, arguments)
                    is_error = False
                except Exception as exc:
                    result = {"status": "error", "message": str(exc)}
                    is_error = True
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, default=str),
                    }
                ],
                "isError": is_error,
            }
        if method == "resources/list":
            return {
                "resources": [
                    {
                        "uri": _RESOURCE_URI,
                        "name": "EvoOntology semantic session manifest",
                        "mimeType": "text/plain",
                    }
                ]
            }
        if method == "resources/read":
            uri = str(params.get("uri", ""))
            if uri != _RESOURCE_URI:
                raise ValueError(f"Unknown resource: {uri}")
            return {
                "contents": [
                    {
                        "uri": _RESOURCE_URI,
                        "mimeType": "text/plain",
                        "text": self.layer.manifest(),
                    }
                ]
            }
        if method == "shutdown":
            return None
        raise KeyError(method)

    def run(self) -> None:
        request: Dict[str, Any] = {}
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                request = json.loads(line)
                request_id = request.get("id")
                if request_id is None:
                    continue
                result = self.dispatch(str(request.get("method", "")), request.get("params") or {})
                response = {"jsonrpc": "2.0", "id": request_id, "result": result}
            except KeyError as exc:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": f"Method not found: {exc.args[0]}"},
                }
            except Exception as exc:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32603, "message": str(exc)},
                }
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="EvoOntology semantic MCP server")
    parser.add_argument(
        "--store",
        default=None,
        help="Workspace root containing active.json (default: <cwd>/.evoontology)",
    )
    args = parser.parse_args()
    SemanticMCPServer(str(resolve_workspace(args.store))).run()


if __name__ == "__main__":
    main()
