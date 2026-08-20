"""Shared semantic tool registry used by the MCP server and the visualizer."""

from __future__ import annotations


TOOLS = [
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
