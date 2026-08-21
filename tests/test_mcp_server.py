"""Protocol checks for the dependency-free semantic MCP server."""

import json
import subprocess
import sys

from evoontology import SemanticStore


def test_stdio_mcp_initialize_and_list_tools(tmp_path):
    workspace = tmp_path / ".evoontology"
    SemanticStore.save_version(
        workspace,
        "semantic_v0",
        {family: [] for family in ("terms", "mappings", "relations", "constraints", "evidence")},
    )
    SemanticStore.set_active(workspace, "semantic_v0")

    requests = "\n".join(
        [
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"},
                }
            ),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
            "",
        ]
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "evoontology.runtime.mcp_server",
            "--store",
            str(workspace),
        ],
        input=requests,
        text=True,
        capture_output=True,
        check=True,
    )

    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert responses[0]["result"]["protocolVersion"] == "2025-06-18"
    tool_names = [tool["name"] for tool in responses[1]["result"]["tools"]]
    assert tool_names[:2] == ["browse_semantics", "resolve_semantics"]
    assert "validate_semantics" in tool_names
    assert "accept_evolution" in tool_names
