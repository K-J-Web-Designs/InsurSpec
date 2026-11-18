# InsurSpec Technical Architecture

## 1. System Architecture
InsurSpec is structured around a deterministic **Spec-Driven Development (SDD)** pipeline enforced by static/AST compliance gates and a dual-LLM switchboard:

```text
src/insur_spec/
├── cli.py                      # Typer CLI & slash-command scaffolding (.github/prompts, .claude/)
├── config.py                   # Pydantic workspace config (.insur-spec/config.yaml + env overrides)
├── mcp_server.py               # Stdio JSON-RPC 2.0 MCP server (tools, resources, prompts)
├── yaml_utils.py               # PyYAML / pure-Python ruamel.yaml compatibility wrapper
├── core/
│   ├── state_machine.py        # LifecyclePhase FSM & per-feature tracking (.insur-spec/state.json)
│   ├── feature_registry.py     # Brownfield feature registry, master spec delta log, AST symbol map
│   ├── constitution_checker.py # 10-Article ConstitutionGatekeeper (SQL, slop, sync, Backstage)
│   ├── executor.py             # ImplementExecutor (<<<FILE>>>, <<<EDIT>>>, --dry-run diffs)
│   ├── circuit_breaker.py      # 5-Strike Circuit Breaker & 100-line log truncation
│   ├── reviewer.py             # DiffReviewer for git diffs (Constitution + secret scanning)
│   └── audit_signer.py         # HMAC-SHA256 COMPLIANCE_RECEIPT.json signer
├── llm/
│   ├── base.py                 # EnterpriseProviderInterface ABC
│   ├── gemini_provider.py      # Google Gemini / Vertex AI adapter + offline mock fallback
│   ├── bedrock_provider.py     # AWS Bedrock Claude 3.5 Sonnet adapter + offline mock fallback
│   └── switchboard.py          # Dynamic provider selection (auto, gemini, bedrock)
└── skills/
    ├── manager.py              # SkillsManager CRUD + Constitutional Inviolability Gate
    ├── loader.py               # Prompt assembly for active skills
    └── router.py               # SkillRouter keyword/domain scoring from spec.md
```

---

## 2. Brownfield & Incremental Feature Design
When `insur-spec specify --add "<requirement>"` is invoked (or automatically after v1 reaches `IMPLEMENTED`/`VERIFIED`):
1. `FeatureRegistry` allocates `.insur-spec/features/<NNN-slug>/` containing isolated `spec.md`, `plan.md`, and `tasks.md`.
2. Root `spec.md` is preserved as the **Living Master Specification**, and a timestamped entry is appended under `## Feature Delta Log` linking to the new feature spec.
3. `build_brownfield_context()` injects the existing master `spec.md`, repository file tree, and a Python AST symbol map (`class`/`def` signatures) into `plan`, `tasks`, `implement`, `qa`, `document`, and `readme`.
4. `implement` automatically adds `backward-compat-api-guard` and `expand-contract-db-migrator` for incremental features.

---

## 3. Execution Safety & Guardrails
- **Targeted Edits (`<<<EDIT>>>`)**: `ImplementExecutor` supports both `<<<FILE: path>>>` and `<<<EDIT: path>>>` (`<<<SEARCH>>>` / `<<<REPLACE>>>`) blocks. Every write is audited by `ConstitutionGatekeeper` *before* touching disk, and `--dry-run` previews unified diffs without modifying files.
- **5-Strike Circuit Breaker**: Repeated identical failures trip on attempt 5 and return an `IncidentReport` with truncated diagnostics ($\le 100$ lines).
- **Pre-Commit & Diff Review**: `insur-spec review` (`DiffReviewer`) audits added diff hunks for Constitutional violations and leaked secrets (`AKIA...`, private keys, hardcoded passwords).

---

## 4. MCP Server Protocol (`insur-spec mcp`)
- **Tools**: `insur_spec_audit_plan`, `insur_spec_feature_list`, `insur_spec_skill_list`, `insur_spec_skill_get`, `insur_spec_verify`, `insur_spec_constitution`
- **Resources**: `insurspec://constitution`, `insurspec://spec`, `insurspec://plan`, `insurspec://config`
- **Prompts**: All 12 `/insur-*` workflows exposed via `prompts/list` and `prompts/get`
