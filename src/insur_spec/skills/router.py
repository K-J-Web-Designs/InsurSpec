from __future__ import annotations

import re
from typing import Iterable

from .manager import SkillMetadata


class SkillRouter:
    """Dynamically selects the most relevant domain skills for a specification or prompt."""

    BASELINE_SKILLS = ("phi-pii-token-masker", "test-triad-generator")

    DOMAIN_KEYWORD_MAP: dict[str, tuple[str, ...]] = {
        "fnol-claims-intake": ("fnol", "claim", "loss", "adjuster", "triage", "subrogation"),
        "policy-lifecycle-engine": ("policy", "quote", "bind", "endorse", "cancel", "reinstate"),
        "rating-algorithm-transpiler": ("rate", "rating", "premium", "decimal", "rounding", "tariff"),
        "actuarial-model-wrapper": ("actuarial", "glm", "mortality", "catastrophe", "loss model"),
        "reinsurance-treaty-allocator": ("reinsurance", "treaty", "quota", "bordereau", "cession"),
        "insurance-fraud-signal-mesh": ("fraud", "siu", "anomaly", "duplicate claim"),
        "acord-standard-parser": ("acord", "xml", "rquid", "xsd"),
        "edifact-x12-translator": ("x12", "edi", "834", "835", "837", "hipaa"),
        "mainframe-copybook-parser": ("cobol", "copybook", "ebcdic", "comp-3", "mainframe"),
        "pas-adapter-generator": ("guidewire", "duck creek", "majesco", "pas", "policycenter"),
        "expand-contract-db-migrator": ("migration", "schema", "sql", "table", "column", "postgres"),
        "temporal-data-versioning": ("temporal", "bi-temporal", "effective_from", "historical", "as-of"),
        "backward-compat-api-guard": ("openapi", "protobuf", "backward", "api", "endpoint", "v2"),
        "idempotent-event-consumer": ("kafka", "eventbridge", "rabbitmq", "idempotent", "outbox"),
        "dead-letter-circuit-breaker": ("dlq", "dead letter", "poison", "retry"),
        "saga-orchestration-builder": ("saga", "compensating", "orchestrator", "distributed"),
        "sox-glba-control-enforcer": ("sox", "glba", "ledger", "disbursement", "reserve"),
        "audit-trail-lineage": ("audit", "lineage", "before_state", "after_state"),
        "state-filing-doc-synthesizer": ("serff", "doi", "state filing", "statutory"),
        "backstage-techdocs-cataloger": ("backstage", "catalog-info", "mkdocs", "techdocs"),
    }

    @classmethod
    def select_skills(
        cls,
        spec_text: str,
        available_skills: Iterable[SkillMetadata],
        baseline: Iterable[str] = BASELINE_SKILLS,
        max_skills: int = 4,
    ) -> list[str]:
        lowered = spec_text.lower()
        tokens = set(re.findall(r"[a-z0-9_-]+", lowered))
        available_names = {s.name for s in available_skills}

        scored: list[tuple[int, str]] = []
        for meta in available_skills:
            score = 0
            for kw in cls.DOMAIN_KEYWORD_MAP.get(meta.name, ()):
                if kw in lowered:
                    score += 3
            desc_tokens = set(re.findall(r"[a-z0-9_-]+", f"{meta.name} {meta.description}".lower()))
            score += len(tokens & desc_tokens)
            if score > 0:
                scored.append((score, meta.name))

        scored.sort(key=lambda item: (-item[0], item[1]))
        selected: list[str] = [name for name in baseline if name in available_names]
        for _, name in scored:
            if name not in selected:
                selected.append(name)
            if len(selected) >= max_skills + len(baseline):
                break
        return selected
