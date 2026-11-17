from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

from .config import find_workspace_root, load_config
from .core.audit_signer import AuditSigner
from .core.constitution_checker import ConstitutionGatekeeper
from .core.feature_registry import FeatureRegistry
from .core.state_machine import PhaseStateMachine
from .skills.manager import SkillsManager


TOOLS_CATALOG = [
    {
        "name": "insur_spec_audit_plan",
        "description": "Audit a plan or source file against the 10-Article Insurance Constitution and Backstage catalog requirements.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_path": {"type": "string", "description": "Relative or absolute path to plan.md (defaults to active feature or root plan.md)."},
                "feature_slug": {"type": "string", "description": "Optional incremental feature slug."},
            },
        },
    },
    {
        "name": "insur_spec_skill_list",
        "description": "List all available enterprise insurance skills from the Skills Factory and local overrides.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "insur_spec_skill_get",
        "description": "Retrieve the full SKILL.md runbook and instructions for a named insurance skill.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Skill slug name"}},
            "required": ["name"],
        },
    },
    {
        "name": "insur_spec_verify",
        "description": "Run final Constitution verification and generate a signed COMPLIANCE_RECEIPT.json.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "feature_slug": {"type": "string", "description": "Optional incremental feature slug to verify."},
            },
        },
    },
    {
        "name": "insur_spec_feature_list",
        "description": "List all incremental features tracked in .insur-spec/state.json and the active feature slug.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "insur_spec_constitution",
        "description": "Return the active 10-Article Insurance Constitution text.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


class InsurSpecMCPServer:
    """Zero-dependency stdio JSON-RPC 2.0 MCP Server for VS Code & Agentic IDEs."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or find_workspace_root()

    def handle_request(self, request: dict[str, Any]) -> Optional[dict[str, Any]]:
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params") or {}

        # Notifications without id do not expect a response
        if req_id is None and method.startswith("notifications/"):
            return None

        if method == "initialize":
            return self._ok(
                req_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "insur-spec", "version": "0.1.0"},
                },
            )

        if method == "tools/list":
            return self._ok(req_id, {"tools": TOOLS_CATALOG})

        if method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments") or {}
            try:
                text = self._dispatch_tool(tool_name, args)
                return self._ok(req_id, {"content": [{"type": "text", "text": text}], "isError": False})
            except Exception as e:
                return self._ok(req_id, {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True})

        return self._err(req_id, -32601, f"Method not found: {method}")

    def _dispatch_tool(self, name: str, args: dict[str, Any]) -> str:
        if name == "insur_spec_audit_plan":
            feature_slug = args.get("feature_slug")
            if "plan_path" in args:
                plan_path = Path(args["plan_path"])
                if not plan_path.is_absolute():
                    plan_path = self.workspace_root / plan_path
            else:
                slug = feature_slug or PhaseStateMachine(self.workspace_root).state.active_feature
                _, plan_path, _ = FeatureRegistry(self.workspace_root).resolve_paths(slug)
            report = ConstitutionGatekeeper(self.workspace_root).audit_plan(plan_path)
            return report.model_dump_json(indent=2)

        if name == "insur_spec_feature_list":
            state = PhaseStateMachine(self.workspace_root).state
            return json.dumps({"active_feature": state.active_feature, "features": state.features}, indent=2)

        if name == "insur_spec_skill_list":
            skills = SkillsManager(self.workspace_root).list_skills()
            return json.dumps([s.model_dump() for s in skills], indent=2)

        if name == "insur_spec_skill_get":
            skill_name = args.get("name", "")
            res = SkillsManager(self.workspace_root).get_skill(skill_name)
            if not res:
                raise ValueError(f"Skill '{skill_name}' not found.")
            meta, doc = res
            return f"# {meta.name}\n\n{doc}"

        if name == "insur_spec_verify":
            cfg = load_config(self.workspace_root)
            slug = args.get("feature_slug") or PhaseStateMachine(self.workspace_root).state.active_feature
            spec_path, plan_path, _ = FeatureRegistry(self.workspace_root).resolve_paths(slug)
            target = plan_path if plan_path.is_file() else spec_path
            report = ConstitutionGatekeeper(self.workspace_root).audit_plan(target)
            if not report.is_compliant:
                return json.dumps({"verified": False, "violations": report.violations}, indent=2)

            signer = AuditSigner()
            receipt = signer.generate_receipt(
                service_name=cfg.service_name,
                line_of_business=cfg.line_of_business,
                domain=cfg.domain,
                constitution_path=self.workspace_root / ".insur-spec" / "memory" / "constitution.md",
                spec_path=spec_path,
                plan_path=plan_path,
                backstage_registered=(self.workspace_root / "catalog-info.yaml").is_file(),
                feature_id=slug,
            )
            signer.write_receipt(receipt, self.workspace_root / "COMPLIANCE_RECEIPT.json")
            return receipt.model_dump_json(indent=2)

        if name == "insur_spec_constitution":
            const_file = self.workspace_root / ".insur-spec" / "memory" / "constitution.md"
            if not const_file.is_file():
                const_file = Path(__file__).resolve().parent.parent.parent / "templates" / "constitution.md"
            return const_file.read_text(encoding="utf-8")

        raise ValueError(f"Unknown tool: {name}")

    @staticmethod
    def _ok(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _err(req_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def serve_stdio(self) -> None:
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError as e:
                err_resp = self._err(None, -32700, f"Parse error: {e}")
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
