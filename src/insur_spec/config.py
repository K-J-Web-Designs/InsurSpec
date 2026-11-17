from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional
from .yaml_utils import yaml
from pydantic import BaseModel, Field


class InsurSpecConfig(BaseModel):
    service_name: str = Field(default="insurance-service")
    line_of_business: str = Field(default="pnc", description="pnc, life_annuity, health, commercial")
    domain: str = Field(default="claims", description="One of 10 enterprise domains")
    domain_architect_team: str = Field(default="claims-architecture-team")
    parent_system: str = Field(default="insurance-core")
    
    # LLM Switchboard configuration
    llm_provider: str = Field(default="auto", description="auto, gemini, bedrock")
    gemini_model: str = Field(default="gemini-3.8-flash")
    bedrock_model: str = Field(default="anthropic.claude-3-5-sonnet-20241022-v2:0")
    aws_region: str = Field(default="us-east-1")
    
    # Backstage integration
    backstage_enabled: bool = Field(default=True)
    repo_slug: str = Field(default="enterprise-insurance/service")
    
    # Active Skills
    active_skills: list[str] = Field(
        default_factory=lambda: [
            "backstage-techdocs-cataloger",
            "phi-pii-token-masker",
            "expand-contract-db-migrator",
            "test-triad-generator",
            "temporal-data-versioning",
        ]
    )


def find_workspace_root(start_dir: Optional[Path] = None) -> Path:
    current = (start_dir or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".insur-spec").is_dir():
            return parent
    return current


def load_config(workspace_root: Optional[Path] = None) -> InsurSpecConfig:
    root = workspace_root or find_workspace_root()
    config_file = root / ".insur-spec" / "config.yaml"
    
    data: dict[str, Any] = {}
    if config_file.is_file():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            pass

    # Environment overrides
    if "INSURSPEC_LLM_PROVIDER" in os.environ:
        data["llm_provider"] = os.environ["INSURSPEC_LLM_PROVIDER"]
    if "AWS_REGION" in os.environ:
        data["aws_region"] = os.environ["AWS_REGION"]
    if "GEMINI_MODEL" in os.environ:
        data["gemini_model"] = os.environ["GEMINI_MODEL"]
    if "BEDROCK_MODEL" in os.environ:
        data["bedrock_model"] = os.environ["BEDROCK_MODEL"]

    return InsurSpecConfig(**data)


def save_config(config: InsurSpecConfig, workspace_root: Optional[Path] = None) -> Path:
    root = workspace_root or find_workspace_root()
    insur_dir = root / ".insur-spec"
    insur_dir.mkdir(parents=True, exist_ok=True)
    config_file = insur_dir / "config.yaml"
    
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)
        
    return config_file
