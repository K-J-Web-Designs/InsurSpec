from __future__ import annotations

import json
from pathlib import Path
from insur_spec.mcp_server import InsurSpecMCPServer


def test_mcp_initialize_and_tools_list(tmp_path: Path):
    server = InsurSpecMCPServer(workspace_root=tmp_path)

    init_resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init_resp is not None
    assert init_resp["result"]["serverInfo"]["name"] == "insur-spec"

    list_resp = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert list_resp is not None
    tool_names = [t["name"] for t in list_resp["result"]["tools"]]
    assert "insur_spec_audit_plan" in tool_names
    assert "insur_spec_skill_list" in tool_names
    assert "insur_spec_verify" in tool_names


def test_mcp_tool_call_skill_list_and_audit(tmp_path: Path):
    server = InsurSpecMCPServer(workspace_root=tmp_path)

    skills_resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "insur_spec_skill_list", "arguments": {}},
    })
    assert skills_resp is not None
    assert skills_resp["result"]["isError"] is False
    parsed = json.loads(skills_resp["result"]["content"][0]["text"])
    assert len(parsed) >= 25
