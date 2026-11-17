# InsurSpec 🛡️

**Sovereign Spec-Driven Coding Agent with Immutable Constitutional Governance, 26-Skill Insurance Factory, MCP Server & Backstage.io Integration**

InsurSpec is an enterprise AI engineering platform designed for Fortune 500 insurance organizations operating across matrixed Line-of-Business (LOB) domains and shared services. It pairs a structured Spec-Driven Development (SDD) workflow with hard AST/regex compliance gates, a pluggable Dual-LLM switchboard (**AWS Bedrock** + **Google Gemini**), and automatic **Backstage.io** service cataloging.

---

## Key Capabilities

1. **Deterministic 6-Command Lifecycle**:
   - `insur-spec init`: Scaffolds `.insur-spec/`, binds the 10-Article Constitution, provisions Backstage (`catalog-info.yaml`, `mkdocs.yml`), and sets up VS Code (`.vscode/tasks.json`, `.vscode/mcp.json`, `AGENTS.md`, `.github/copilot-instructions.md`).
   - `insur-spec specify`: Elicits structured requirements and regulatory/PII classification into `spec.md` (use `--add` for incremental brownfield features).
   - `insur-spec plan`: Synthesizes technical architecture into `plan.md` and enforces the **Constitution Gatekeeper**.
   - `insur-spec tasks`: Breaks down the approved plan into atomic TDD tasks (`tasks.md`).
   - `insur-spec implement`: Executes the autonomous synthesis loop with injected domain skills and the **5-Strike Circuit Breaker**.
   - `insur-spec verify`: Runs final Constitution & Backstage checks and emits an HMAC-SHA256 signed `COMPLIANCE_RECEIPT.json`.

2. **Immutable 10-Article Constitution (`constitution.md`)**:
   - **Zero AI Slop**: Blocks `// TODO`, `NotImplementedError`, truncating ellipses (`// ...rest of`), and empty `catch`/`except: pass` blocks.
   - **Focused Testing (Anti-Bloat)**: Enforces the **Essential Triad** (*Happy Path*, *Key Boundary*, *Expected Failure*) with parameterized tests—zero vanity tests.
   - **Zero-Destruction Data Preservation**: Blocks `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, and unbounded `DELETE FROM`; mandates **Expand-Contract** migrations.
   - **Universal Cross-Device Sync**: Flags un-synced client-only data silos (`localStorage.setItem('user_...')`).
   - **5-Strike Circuit Breaker & Token Economy**: Halts circular failure loops on strike 5 and slices raw logs to <= 100 lines.

3. **Pluggable Dual-LLM Switchboard**:
   - **Development / Local Testing**: **Google Gemini / Vertex AI** (`--provider gemini`, default fallback when AWS creds are absent).
   - **Enterprise Production**: **AWS Bedrock** (`--provider bedrock`, Anthropic Claude 3.5 Sonnet over AWS PrivateLink).

4. **VS Code & MCP Native Integration**:
   - **Zero-Code Workspace Integration**: `.vscode/tasks.json` + `AGENTS.md` + `.github/copilot-instructions.md`.
   - **MCP Server (`insur-spec mcp`)**: Exposes `insur_spec_audit_plan`, `insur_spec_feature_list`, `insur_spec_skill_list`, `insur_spec_skill_get`, `insur_spec_verify`, and `insur_spec_constitution` over `stdio` JSON-RPC 2.0.

5. **26-Skill Enterprise Insurance Factory (`skills_factory/`)**:
   - Full CRUD CLI (`insur-spec skill [list|get|add|edit|delete]`) with a **Constitutional Inviolability Gate**—custom skills cannot bypass the Constitution.

---

## Quickstart

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -e ".[all]"

# 3. Initialize a new insurance microservice repo
mkdir my-claims-service && cd my-claims-service
insur-spec init --name fnol-intake --lob pnc --domain claims --provider gemini

# 4. Run the Spec-Driven workflow
insur-spec specify "Ingest FNOL auto claims with PII masking and temporal lookup"
insur-spec plan
insur-spec tasks
insur-spec implement --verify-cmd "pytest"
insur-spec verify
```

---

## Running Tests

```bash
pytest tests/ -v
```
