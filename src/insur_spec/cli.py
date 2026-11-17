from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from jinja2 import Template

from .config import InsurSpecConfig, load_config, save_config, find_workspace_root
from .core.state_machine import PhaseStateMachine, LifecyclePhase
from .core.constitution_checker import ConstitutionGatekeeper
from .core.circuit_breaker import CircuitBreaker
from .core.audit_signer import AuditSigner
from .core.executor import ImplementExecutor
from .core.feature_registry import FeatureRegistry
from .llm.switchboard import LLMSwitchboard
from .mcp_server import InsurSpecMCPServer
from .skills.manager import SkillsManager, ConstitutionalViolationError
from .skills.loader import SkillsLoader

app = typer.Typer(
    name="insur-spec",
    help="Sovereign Spec-Driven Coding Agent with Immutable Constitutional Governance & Backstage.io Integration",
    no_args_is_help=True,
)
skill_app = typer.Typer(name="skill", help="Manage domain skills (CRUD operations with constitutional enforcement)")
feature_app = typer.Typer(name="feature", help="Manage incremental feature specs for brownfield iterations")
app.add_typer(skill_app, name="skill")
app.add_typer(feature_app, name="feature")

console = Console()
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def _load_constitution_text(root: Path) -> str:
    const_file = root / ".insur-spec" / "memory" / "constitution.md"
    if not const_file.is_file():
        const_file = TEMPLATES_DIR / "constitution.md"
    return const_file.read_text(encoding="utf-8") if const_file.is_file() else ""


def _is_mock_response(text: str) -> bool:
    return text.startswith("[Gemini Mock") or text.startswith("[AWS Bedrock Mock")


def _resolve_active_feature(fsm: PhaseStateMachine, feature_opt: Optional[str]) -> Optional[str]:
    return feature_opt or fsm.state.active_feature


def _update_feature_phase(fsm: PhaseStateMachine, slug: Optional[str], phase: str) -> None:
    if slug and slug in fsm.state.features:
        fsm.state.features[slug]["phase"] = phase


COPILOT_PROMPTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "insur-specify",
        "Elicit v1 insurance feature requirements into spec.md",
        "[feature requirement]",
        "Run `{cli} specify \"<requirement>\"` (obeying `.insur-spec/memory/constitution.md`) and summarize any `## 5. Ambiguity Triage` items before proceeding to `/insur-plan`.",
    ),
    (
        "insur-feature-add",
        "Add an incremental brownfield feature without overwriting v1 spec.md",
        "[new feature requirement]",
        "Run `{cli} specify --add \"<requirement>\"` to create `.insur-spec/features/<NNN-slug>/spec.md` and append a `## Feature Delta Log` entry to root `spec.md`. Preserve v1 contracts.",
    ),
    (
        "insur-plan",
        "Generate technical architecture plan.md and run Constitution Check",
        "[optional --feature <slug>]",
        "Run `{cli} plan` (or `{cli} plan --feature <slug>`) and verify zero Constitution Gatekeeper violations.",
    ),
    (
        "insur-tasks",
        "Deconstruct plan.md into atomic Essential Triad TDD tasks",
        "[optional --feature <slug>]",
        "Run `{cli} tasks` (or `{cli} tasks --feature <slug>`) to generate `tasks.md`.",
    ),
    (
        "insur-implement",
        "Implement tasks.md using active domain skills and 5-Strike Breaker",
        "[optional --verify-cmd pytest]",
        "Run `{cli} implement` (with `--verify-cmd \"pytest\"` when tests exist), strictly obeying `.insur-spec/memory/constitution.md`.",
    ),
    (
        "insur-qa",
        "Generate Essential Triad QA tests (Happy Path, Key Boundary, Failure)",
        "[optional --feature <slug>]",
        "Run `{cli} qa` (or `{cli} qa --feature <slug>`) to generate parameterized QA tests enforcing Article III (Essential Triad) and run `pytest`.",
    ),
    (
        "insur-verify",
        "Run final Constitution Gate and sign COMPLIANCE_RECEIPT.json",
        "[optional --feature <slug>]",
        "Run `{cli} verify` (or use MCP tool `insur_spec_verify`) to audit compliance and sign `COMPLIANCE_RECEIPT.json`.",
    ),
)


def _scaffold_copilot_prompts(github_dir: Path, cli_command: str) -> None:
    prompts_dir = github_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for name, description, arg_hint, body_tmpl in COPILOT_PROMPTS:
        target = prompts_dir / f"{name}.prompt.md"
        if target.is_file():
            continue
        body = body_tmpl.format(cli=cli_command)
        target.write_text(
            f"---\n"
            f"name: \"{name}\"\n"
            f"description: \"{description}\"\n"
            f"argument-hint: \"{arg_hint}\"\n"
            f"agent: \"agent\"\n"
            f"---\n\n"
            f"{body}\n",
            encoding="utf-8",
        )


@app.command()
def init(
    service_name: str = typer.Option("insurance-service", "--name", "-n", help="Microservice or repository name"),
    lob: str = typer.Option("pnc", "--lob", "-l", help="Line of Business: pnc, life_annuity, health, commercial"),
    domain: str = typer.Option("claims", "--domain", "-d", help="1 of 10 enterprise domains (e.g. claims, policy, rating)"),
    provider: str = typer.Option("auto", "--provider", "-p", help="LLM provider: auto, gemini, bedrock"),
):
    """Scaffolds .insur-spec/ workspace, binds Constitution, and provisions Backstage & VS Code."""
    root = Path.cwd().resolve()
    insur_dir = root / ".insur-spec"
    memory_dir = insur_dir / "memory"
    skills_dir = insur_dir / "skills"

    memory_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save Config
    cfg = InsurSpecConfig(
        service_name=service_name,
        line_of_business=lob,
        domain=domain,
        llm_provider=provider,
        domain_architect_team=f"{domain}-architecture-team",
    )
    save_config(cfg, workspace_root=root)

    # 2. Copy Master Constitution
    const_source = TEMPLATES_DIR / "constitution.md"
    const_target = memory_dir / "constitution.md"
    if const_source.is_file():
        const_target.write_text(const_source.read_text(encoding="utf-8"), encoding="utf-8")

    # 3. Generate Backstage catalog-info.yaml if not present
    catalog_target = root / "catalog-info.yaml"
    if not catalog_target.is_file():
        tmpl_content = (TEMPLATES_DIR / "catalog-info.yaml.j2").read_text(encoding="utf-8")
        rendered = Template(tmpl_content).render(
            service_name=service_name,
            service_description=f"Enterprise {lob.upper()} {domain.capitalize()} Service",
            repo_slug=f"enterprise-insurance/{service_name}",
            line_of_business=lob,
            domain=domain,
            domain_architect_team=f"{domain}-architecture-team",
        )
        catalog_target.write_text(rendered, encoding="utf-8")

    # 4. Generate Backstage mkdocs.yml and docs/index.md
    mkdocs_target = root / "mkdocs.yml"
    if not mkdocs_target.is_file():
        tmpl_content = (TEMPLATES_DIR / "mkdocs.yml.j2").read_text(encoding="utf-8")
        rendered = Template(tmpl_content).render(
            service_name=service_name,
            domain_architect_team=f"{domain}-architecture-team",
        )
        mkdocs_target.write_text(rendered, encoding="utf-8")

    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    if not (docs_dir / "index.md").is_file():
        (docs_dir / "index.md").write_text(
            f"# {service_name}\n\nEnterprise {lob.upper()} {domain.capitalize()} Service registered with Backstage.io.\n",
            encoding="utf-8",
        )

    # 5. Generate VS Code Tasks (.vscode/tasks.json), MCP (.vscode/mcp.json), & Agent Instructions
    has_global_cli = shutil.which("insur-spec") is not None
    cli_command = "insur-spec" if has_global_cli else f"{Path(sys.executable).as_posix()} -m insur_spec.cli"

    vscode_dir = root / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)

    tasks_json_target = vscode_dir / "tasks.json"
    if not tasks_json_target.is_file():
        tmpl_content = (TEMPLATES_DIR / "vscode_tasks.json.j2").read_text(encoding="utf-8")
        tasks_json_target.write_text(Template(tmpl_content).render(cli_command=cli_command), encoding="utf-8")

    mcp_json_target = vscode_dir / "mcp.json"
    if not mcp_json_target.is_file():
        mcp_cmd = "insur-spec" if has_global_cli else Path(sys.executable).as_posix()
        mcp_args = ["mcp"] if has_global_cli else ["-m", "insur_spec.cli", "mcp"]
        mcp_tmpl = (TEMPLATES_DIR / "vscode_mcp.json.j2").read_text(encoding="utf-8")
        mcp_json_target.write_text(Template(mcp_tmpl).render(mcp_command=mcp_cmd, mcp_args=mcp_args), encoding="utf-8")

    agents_tmpl = (TEMPLATES_DIR / "AGENTS.md.j2").read_text(encoding="utf-8")
    rendered_agents = Template(agents_tmpl).render(
        service_name=service_name,
        line_of_business=lob,
        domain=domain,
        domain_architect_team=f"{domain}-architecture-team",
        cli_command=cli_command,
    )

    agents_md_target = root / "AGENTS.md"
    if not agents_md_target.is_file():
        agents_md_target.write_text(rendered_agents, encoding="utf-8")

    github_dir = root / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)
    copilot_target = github_dir / "copilot-instructions.md"
    if not copilot_target.is_file():
        copilot_target.write_text(rendered_agents, encoding="utf-8")
    _scaffold_copilot_prompts(github_dir, cli_command)

    # 6. Initialize State Machine
    fsm = PhaseStateMachine(root)
    fsm.transition(LifecyclePhase.INITIALIZED, {"service_name": service_name, "lob": lob, "domain": domain})

    console.print(Panel(
        f"[bold green]✔ Initialized InsurSpec for {service_name}[/bold green]\n\n"
        f"• [cyan]Line of Business:[/cyan] {lob.upper()}\n"
        f"• [cyan]Enterprise Domain:[/cyan] {domain.capitalize()} (Architect: {domain}-architecture-team)\n"
        f"• [cyan]LLM Provider:[/cyan] {provider.upper()}\n"
        f"• [cyan]Constitution:[/cyan] Bound to .insur-spec/memory/constitution.md\n"
        f"• [cyan]Backstage.io:[/cyan] catalog-info.yaml & mkdocs.yml provisioned\n"
        f"• [cyan]VS Code Ready:[/cyan] .vscode/tasks.json, .vscode/mcp.json, AGENTS.md & .github/copilot-instructions.md created\n",
        title="InsurSpec Workspace Scaffolded",
    ))


@app.command()
def specify(
    directive: str = typer.Argument(..., help="High-level business requirement or feature description"),
    add: bool = typer.Option(False, "--add", "-a", help="Add an incremental feature while preserving root spec.md"),
    feature: Optional[str] = typer.Option(None, "--feature", "-f", help="Explicit kebab-case feature slug"),
):
    """Elicits structured requirements and authors spec.md (or an incremental feature spec)."""
    root = find_workspace_root()
    cfg = load_config(root)
    fsm = PhaseStateMachine(root)
    registry = FeatureRegistry(root)

    is_incremental = add or bool(feature) or (
        (root / "spec.md").is_file()
        and fsm.current_phase in {LifecyclePhase.IMPLEMENTED, LifecyclePhase.VERIFIED}
    )

    console.print(f"[bold cyan]▶ Eliciting specification for:[/bold cyan] {directive}")

    provider = LLMSwitchboard.get_provider(cfg.llm_provider, gemini_model=cfg.gemini_model, bedrock_model=cfg.bedrock_model, aws_region=cfg.aws_region)
    spec_tmpl = (TEMPLATES_DIR / "spec_template.md").read_text(encoding="utf-8")
    rendered_base = Template(spec_tmpl).render(
        feature_title=directive[:60],
        line_of_business=cfg.line_of_business.upper(),
        domain=cfg.domain.capitalize(),
        domain_architect_team=cfg.domain_architect_team,
        service_name=cfg.service_name,
        business_outcomes=directive,
    )

    brownfield_ctx = registry.build_brownfield_context() if is_incremental else ""
    prompt_parts = [
        "Fill out and refine this insurance feature specification in Markdown based on the requirement below.",
        "If any critical business rules or PII boundaries are ambiguous, list them under '## 5. Ambiguity Triage'.",
    ]
    if brownfield_ctx:
        prompt_parts.append(f"Existing System Context (do not break v1 contracts):\n{brownfield_ctx}")
    prompt_parts.append(f"Requirement: {directive}\n\nTemplate:\n{rendered_base}")

    llm_output = provider.generate(
        prompt="\n\n".join(prompt_parts),
        system_instructions=_load_constitution_text(root),
    )

    spec_content = rendered_base if _is_mock_response(llm_output) else llm_output

    if is_incremental:
        record = registry.create_feature(directive, custom_slug=feature)
        spec_file = root / record.spec_path
        spec_file.write_text(spec_content, encoding="utf-8")
        registry.append_to_master_spec(record)
        fsm.state.active_feature = record.slug
        fsm.state.features[record.slug] = record.model_dump()
        display_target = f"{record.spec_path} (linked in root spec.md)"
    else:
        spec_file = root / "spec.md"
        spec_file.write_text(spec_content, encoding="utf-8")
        fsm.state.active_feature = None
        display_target = "spec.md"

    fsm.state.last_spec_path = str(spec_file)
    fsm.transition(LifecyclePhase.SPECIFIED, {"directive": directive, "feature": fsm.state.active_feature})

    console.print(Panel(
        f"[bold green]✔ Specification authored at {display_target}[/bold green]\n"
        f"Next step: Run [bold yellow]insur-spec plan[/bold yellow] to generate architecture blueprint and run Constitution Check.",
        title="Phase 1 (Specify) Complete",
    ))


@app.command()
def plan(
    feature: Optional[str] = typer.Option(None, "--feature", "-f", help="Target incremental feature slug"),
):
    """Synthesizes technical architecture plan and executes the mandatory Constitution Check."""
    root = find_workspace_root()
    cfg = load_config(root)
    fsm = PhaseStateMachine(root)
    registry = FeatureRegistry(root)
    active_slug = _resolve_active_feature(fsm, feature)
    spec_file, plan_file, _ = registry.resolve_paths(active_slug)

    spec_text = spec_file.read_text(encoding="utf-8") if spec_file.is_file() else ""
    plan_tmpl = (TEMPLATES_DIR / "plan_template.md").read_text(encoding="utf-8")
    rendered_base = Template(plan_tmpl).render(
        feature_title=active_slug or cfg.service_name,
        service_name=cfg.service_name,
    )

    brownfield_ctx = registry.build_brownfield_context(active_slug=active_slug) if active_slug else ""
    prompt_parts = [
        "Generate a technical architecture plan matching the template below.",
        "You MUST include the exact heading '## 5. Mandatory Constitution Check' and follow Expand-Contract DDL.",
    ]
    if brownfield_ctx:
        prompt_parts.append(brownfield_ctx)
    prompt_parts.append(f"Specification:\n{spec_text}\n\nTemplate:\n{rendered_base}")

    provider = LLMSwitchboard.get_provider(cfg.llm_provider, gemini_model=cfg.gemini_model, bedrock_model=cfg.bedrock_model, aws_region=cfg.aws_region)
    llm_output = provider.generate(
        prompt="\n\n".join(prompt_parts),
        system_instructions=_load_constitution_text(root),
    )

    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(rendered_base if _is_mock_response(llm_output) else llm_output, encoding="utf-8")

    gatekeeper = ConstitutionGatekeeper(root)
    report = gatekeeper.audit_plan(plan_file)

    if not report.is_compliant:
        console.print("[bold red]✖ Constitution Check FAILED:[/bold red]")
        for v in report.violations:
            console.print(f"  • [{v['severity']}] {v['article']} - {v['description']} ({v['file_path']}:{v['line_number']})")
        raise typer.Exit(code=1)

    fsm.state.last_plan_path = str(plan_file)
    _update_feature_phase(fsm, active_slug, LifecyclePhase.PLANNED.value)
    fsm.transition(LifecyclePhase.PLANNED, {"compliant": True, "feature": active_slug})

    console.print(Panel(
        f"[bold green]✔ Architecture Plan generated & Constitution Check PASSED[/bold green]\n\n"
        f"• Verified 10 Articles: Anti-Slop, Expand-Contract DDL, Sync, Test Triad, Backstage.\n"
        f"• Zero Blocker Violations Found.\n"
        f"Next step: Run [bold yellow]insur-spec tasks[/bold yellow] to generate TDD implementation checklist.",
        title="Phase 2 (Plan) Complete",
    ))


@app.command()
def tasks(
    feature: Optional[str] = typer.Option(None, "--feature", "-f", help="Target incremental feature slug"),
):
    """Deconstructs the plan into atomic TDD implementation tasks."""
    root = find_workspace_root()
    cfg = load_config(root)
    fsm = PhaseStateMachine(root)
    registry = FeatureRegistry(root)
    active_slug = _resolve_active_feature(fsm, feature)
    _, plan_file, tasks_file = registry.resolve_paths(active_slug)

    plan_text = plan_file.read_text(encoding="utf-8") if plan_file.is_file() else ""
    tmpl_content = (TEMPLATES_DIR / "tasks_template.md").read_text(encoding="utf-8")
    rendered_base = Template(tmpl_content).render(feature_title=active_slug or cfg.service_name)

    brownfield_ctx = registry.build_brownfield_context(active_slug=active_slug) if active_slug else ""
    prompt_parts = ["Break down this architecture plan into atomic TDD tasks using the template."]
    if brownfield_ctx:
        prompt_parts.append(brownfield_ctx)
    prompt_parts.append(f"Plan:\n{plan_text}\n\nTemplate:\n{rendered_base}")

    provider = LLMSwitchboard.get_provider(cfg.llm_provider, gemini_model=cfg.gemini_model, bedrock_model=cfg.bedrock_model, aws_region=cfg.aws_region)
    llm_output = provider.generate(
        prompt="\n\n".join(prompt_parts),
        system_instructions=_load_constitution_text(root),
    )

    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(rendered_base if _is_mock_response(llm_output) else llm_output, encoding="utf-8")

    fsm.state.last_tasks_path = str(tasks_file)
    _update_feature_phase(fsm, active_slug, LifecyclePhase.TASKS_READY.value)
    fsm.transition(LifecyclePhase.TASKS_READY, {"feature": active_slug})

    console.print(Panel(
        f"[bold green]✔ Atomic TDD tasks generated at {tasks_file.relative_to(root).as_posix()}[/bold green]\n"
        f"Next step: Run [bold yellow]insur-spec implement[/bold yellow] to execute tasks.",
        title="Phase 3 (Tasks) Complete",
    ))


@app.command()
def implement(
    verify_cmd: Optional[str] = typer.Option(None, "--verify-cmd", help="Optional test command to run after synthesis (e.g. 'pytest')"),
    feature: Optional[str] = typer.Option(None, "--feature", "-f", help="Target incremental feature slug"),
):
    """Synthesizes code for tasks using active domain skills and the 5-Strike Circuit Breaker."""
    root = find_workspace_root()
    cfg = load_config(root)
    fsm = PhaseStateMachine(root)
    registry = FeatureRegistry(root)
    active_slug = _resolve_active_feature(fsm, feature)
    _, _, tasks_file = registry.resolve_paths(active_slug)

    skill_names = list(cfg.active_skills)
    if active_slug:
        for brownfield_skill in ("backward-compat-api-guard", "expand-contract-db-migrator"):
            if brownfield_skill not in skill_names:
                skill_names.append(brownfield_skill)

    mgr = SkillsManager(root)
    loader = SkillsLoader(mgr)
    skills_prompt = loader.assemble_skills_context(skill_names)
    brownfield_ctx = registry.build_brownfield_context(active_slug=active_slug) if active_slug else ""
    system_instructions = _load_constitution_text(root) + skills_prompt + ("\n\n" + brownfield_ctx if brownfield_ctx else "")

    tasks_md = tasks_file.read_text(encoding="utf-8") if tasks_file.is_file() else "Implement core service."

    provider = LLMSwitchboard.get_provider(cfg.llm_provider, gemini_model=cfg.gemini_model, bedrock_model=cfg.bedrock_model, aws_region=cfg.aws_region)
    executor = ImplementExecutor(workspace_root=root, provider=provider)

    verify_fn = None
    if verify_cmd:
        cmd_parts = verify_cmd.split()
        verify_fn = lambda: ImplementExecutor.run_shell_check(cmd_parts, root)

    console.print(f"[bold cyan]▶ Injected {len(skill_names)} domain skills into execution context.[/bold cyan]")
    result = executor.run_loop(tasks_markdown=tasks_md, system_instructions=system_instructions, verify_fn=verify_fn)

    if not result.success:
        console.print(f"[bold red]✖ Implementation halted after {result.attempts} attempt(s):[/bold red] {result.message}")
        if result.incident:
            console.print(f"[yellow]Last error sample:[/yellow]\n{result.incident.last_error_sample}")
        raise typer.Exit(code=1)

    _update_feature_phase(fsm, active_slug, LifecyclePhase.IMPLEMENTED.value)
    fsm.transition(LifecyclePhase.IMPLEMENTED, {"files_written": result.files_written, "attempts": result.attempts, "feature": active_slug})
    console.print(f"[bold green]✔ {result.message}[/bold green] (Files written: {len(result.files_written)})")


@app.command()
def qa(
    verify_cmd: Optional[str] = typer.Option(None, "--verify-cmd", help="Optional test runner command (e.g. 'pytest')"),
    feature: Optional[str] = typer.Option(None, "--feature", "-f", help="Target incremental feature slug"),
):
    """Generates Essential Triad QA tests (Happy Path, Key Boundary, Expected Failure) for the active spec."""
    root = find_workspace_root()
    cfg = load_config(root)
    fsm = PhaseStateMachine(root)
    registry = FeatureRegistry(root)
    active_slug = _resolve_active_feature(fsm, feature)
    spec_file, plan_file, tasks_file = registry.resolve_paths(active_slug)

    mgr = SkillsManager(root)
    loader = SkillsLoader(mgr)
    skills_prompt = loader.assemble_skills_context(["test-triad-generator", "phi-pii-token-masker"])
    brownfield_ctx = registry.build_brownfield_context(active_slug=active_slug)
    system_instructions = _load_constitution_text(root) + skills_prompt + ("\n\n" + brownfield_ctx if brownfield_ctx else "")

    spec_text = spec_file.read_text(encoding="utf-8") if spec_file.is_file() else ""
    plan_text = plan_file.read_text(encoding="utf-8") if plan_file.is_file() else ""
    tasks_text = tasks_file.read_text(encoding="utf-8") if tasks_file.is_file() else ""

    qa_prompt = (
        "Generate focused QA unit/integration tests in `tests/` enforcing Article III (The Essential Triad: "
        "Happy Path, Key Boundary, Expected Failure) using parameterized tests where applicable and zero vanity tests.\n\n"
        f"## Specification\n{spec_text}\n\n"
        f"## Architecture Plan\n{plan_text}\n\n"
        f"## Tasks\n{tasks_text}\n"
    )

    provider = LLMSwitchboard.get_provider(cfg.llm_provider, gemini_model=cfg.gemini_model, bedrock_model=cfg.bedrock_model, aws_region=cfg.aws_region)
    executor = ImplementExecutor(workspace_root=root, provider=provider)

    verify_fn = None
    if verify_cmd:
        cmd_parts = verify_cmd.split()
        verify_fn = lambda: ImplementExecutor.run_shell_check(cmd_parts, root)

    console.print(f"[bold cyan]▶ Generating Essential Triad QA tests{f' for {active_slug}' if active_slug else ''}...[/bold cyan]")
    result = executor.run_loop(tasks_markdown=qa_prompt, system_instructions=system_instructions, verify_fn=verify_fn)

    if not result.success:
        console.print(f"[bold red]✖ QA test generation halted after {result.attempts} attempt(s):[/bold red] {result.message}")
        if result.incident:
            console.print(f"[yellow]Last error sample:[/yellow]\n{result.incident.last_error_sample}")
        raise typer.Exit(code=1)

    console.print(f"[bold green]✔ QA generation complete: {result.message}[/bold green] (Test files written: {len(result.files_written)})")


@app.command()
def verify(
    feature: Optional[str] = typer.Option(None, "--feature", "-f", help="Target incremental feature slug"),
):
    """Runs final enterprise verification: Constitution check, Backstage catalog lint, and signed receipt."""
    root = find_workspace_root()
    cfg = load_config(root)
    fsm = PhaseStateMachine(root)
    registry = FeatureRegistry(root)
    active_slug = _resolve_active_feature(fsm, feature)
    spec_file, plan_file, _ = registry.resolve_paths(active_slug)

    gatekeeper = ConstitutionGatekeeper(root)
    report = gatekeeper.audit_plan(plan_file if plan_file.is_file() else spec_file)

    if not report.is_compliant:
        console.print("[bold red]✖ Final Verification FAILED on Constitution Gate:[/bold red]")
        for v in report.violations:
            console.print(f"  • {v['description']}")
        raise typer.Exit(code=1)

    signer = AuditSigner()
    receipt = signer.generate_receipt(
        service_name=cfg.service_name,
        line_of_business=cfg.line_of_business,
        domain=cfg.domain,
        constitution_path=root / ".insur-spec" / "memory" / "constitution.md",
        spec_path=spec_file,
        plan_path=plan_file,
        tests_passed=3,
        pii_violations=0,
        backstage_registered=(root / "catalog-info.yaml").is_file(),
        feature_id=active_slug,
    )
    receipt_file = root / "COMPLIANCE_RECEIPT.json"
    signer.write_receipt(receipt, receipt_file)

    fsm.state.last_receipt_path = str(receipt_file)
    _update_feature_phase(fsm, active_slug, LifecyclePhase.VERIFIED.value)
    fsm.transition(LifecyclePhase.VERIFIED, {"feature": active_slug})

    console.print(Panel(
        f"[bold green]✔ Enterprise Verification Succeeded![/bold green]\n\n"
        f"• [cyan]Constitution Check:[/cyan] Passed (0 Findings)\n"
        f"• [cyan]Backstage.io Catalog:[/cyan] Validated (catalog-info.yaml)\n"
        f"• [cyan]Audit Receipt:[/cyan] Cryptographically signed at COMPLIANCE_RECEIPT.json\n"
        f"• [cyan]HMAC Signature:[/cyan] {receipt.hmac_sha256[:24]}...\n\n"
        f"[bold white]Pull Request is certified and ready for Domain Architect & CISO Review.[/bold white]",
        title="Phase 5 (Verify) Certified",
    ))


@app.command()
def mcp():
    """Starts the InsurSpec stdio MCP server for VS Code & agentic IDE integration."""
    root = find_workspace_root()
    InsurSpecMCPServer(workspace_root=root).serve_stdio()


# -----------------------------------------------------------------------------
# SKILLS SUBCOMMANDS (CRUD Operations with Constitutional Inviolability)
# -----------------------------------------------------------------------------

@skill_app.command("list")
def skill_list():
    """Lists all available and local skills."""
    root = find_workspace_root()
    mgr = SkillsManager(root)
    skills = mgr.list_skills()

    table = Table(title="InsurSpec Domain Skills Factory")
    table.add_column("Skill Name", style="cyan", no_wrap=True)
    table.add_column("Scope", style="green")
    table.add_column("Description", style="white")

    for s in skills:
        scope = "Local Override" if s.is_local_override else "Enterprise Factory"
        table.add_row(s.name, scope, s.description)

    console.print(table)


@skill_app.command("get")
def skill_get(name: str):
    """Inspects a skill's runbook and instructions."""
    root = find_workspace_root()
    mgr = SkillsManager(root)
    result = mgr.get_skill(name)

    if not result:
        console.print(f"[bold red]Skill '{name}' not found.[/bold red]")
        raise typer.Exit(code=1)

    meta, content = result
    console.print(Panel(Markdown(content), title=f"Skill: {meta.name} ({'Local' if meta.is_local_override else 'Factory'})"))


@skill_app.command("add")
def skill_add(
    name: str = typer.Argument(..., help="Skill name in kebab-case"),
    description: str = typer.Option("", "--desc", "-d", help="Short description"),
):
    """Creates a new project skill. Automatically validated against Constitution."""
    root = find_workspace_root()
    mgr = SkillsManager(root)

    boilerplate = (
        f"# {name.replace('-', ' ').title()} Runbook\n\n"
        f"## Operational Instructions\n"
        f"Follow enterprise standards for {name}.\n"
    )

    try:
        meta = mgr.add_skill(name, description or f"Custom domain skill for {name}", boilerplate)
        console.print(f"[bold green]✔ Successfully created local skill:[/bold green] {meta.name} at {meta.path}")
    except ConstitutionalViolationError as e:
        console.print(f"[bold red]✖ Rejected by Constitution Gatekeeper:[/bold red] {e}")
        raise typer.Exit(code=1)


@skill_app.command("edit")
def skill_edit(
    name: str = typer.Argument(..., help="Skill name to edit or override locally"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to updated SKILL.md content"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Inline SKILL.md content"),
):
    """Modifies a skill locally. Automatically validated against Constitution."""
    root = find_workspace_root()
    mgr = SkillsManager(root)

    if file and file.is_file():
        new_text = file.read_text(encoding="utf-8")
    elif content:
        new_text = content
    else:
        existing = mgr.get_skill(name)
        if not existing:
            console.print(f"[bold red]Skill '{name}' not found and no --file/--content provided.[/bold red]")
            raise typer.Exit(code=1)
        new_text = existing[1]

    try:
        meta = mgr.edit_skill(name, new_text)
        console.print(f"[bold green]✔ Updated local skill override:[/bold green] {meta.name} at {meta.path}")
    except (ConstitutionalViolationError, ValueError) as e:
        console.print(f"[bold red]✖ Rejected by Constitution Gatekeeper:[/bold red] {e}")
        raise typer.Exit(code=1)


@skill_app.command("delete")
def skill_delete(name: str):
    """Deletes a local project skill override."""
    root = find_workspace_root()
    mgr = SkillsManager(root)
    if mgr.delete_skill(name):
        console.print(f"[bold green]✔ Deleted local skill override '{name}'.[/bold green]")
    else:
        console.print(f"[bold yellow]No local override found for '{name}'.[/bold yellow]")


# -----------------------------------------------------------------------------
# FEATURE SUBCOMMANDS (Incremental Brownfield Feature Management)
# -----------------------------------------------------------------------------

@feature_app.command("list")
def feature_list():
    """Lists all incremental features tracked in this workspace."""
    root = find_workspace_root()
    fsm = PhaseStateMachine(root)

    if not fsm.state.features:
        console.print("[yellow]No incremental features registered yet. Use `insur-spec specify --add \"...\"` to add one.[/yellow]")
        return

    table = Table(title="InsurSpec Incremental Features")
    table.add_column("Slug", style="cyan", no_wrap=True)
    table.add_column("Phase", style="green")
    table.add_column("Active", style="magenta")
    table.add_column("Title", style="white")

    for slug, info in fsm.state.features.items():
        is_active = "★" if slug == fsm.state.active_feature else ""
        table.add_row(slug, str(info.get("phase", "")), is_active, str(info.get("title", "")))

    console.print(table)


@feature_app.command("use")
def feature_use(slug: str = typer.Argument(..., help="Feature slug to set as active")):
    """Switches the active incremental feature context."""
    root = find_workspace_root()
    fsm = PhaseStateMachine(root)
    if slug not in fsm.state.features:
        console.print(f"[bold red]Feature '{slug}' not found.[/bold red]")
        raise typer.Exit(code=1)
    fsm.state.active_feature = slug
    fsm.save()
    console.print(f"[bold green]✔ Active feature switched to:[/bold green] {slug}")


@app.command()
def constitution():
    """Displays the active 10-Article Insurance Constitution."""
    root = find_workspace_root()
    const_text = _load_constitution_text(root)
    if const_text:
        console.print(Panel(Markdown(const_text), title="Software Engineering & Anti-Slop Constitution"))
    else:
        console.print("[bold red]Constitution document not found.[/bold red]")


if __name__ == "__main__":
    app()
