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


def test_mcp_resources_and_prompts(tmp_path: Path):
    (tmp_path / "spec.md").write_text("# Master Spec", encoding="utf-8")
    server = InsurSpecMCPServer(workspace_root=tmp_path)

    res_list = server.handle_request({"jsonrpc": "2.0", "id": 10, "method": "resources/list", "params": {}})
    assert res_list is not None
    uris = [r["uri"] for r in res_list["result"]["resources"]]
    assert "insurspec://constitution" in uris
    assert "insurspec://spec" in uris

    res_read = server.handle_request({"jsonrpc": "2.0", "id": 11, "method": "resources/read", "params": {"uri": "insurspec://spec"}})
    assert res_read is not None
    assert "# Master Spec" in res_read["result"]["contents"][0]["text"]

    prompts_list = server.handle_request({"jsonrpc": "2.0", "id": 12, "method": "prompts/list", "params": {}})
    assert prompts_list is not None
    prompt_names = [p["name"] for p in prompts_list["result"]["prompts"]]
    assert "insur-review" in prompt_names
    assert "insur-quick" in prompt_names
