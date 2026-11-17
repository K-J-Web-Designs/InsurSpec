from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class ComplianceReceipt(BaseModel):
    version: str = "1.0.0"
    service_name: str
    line_of_business: str
    domain: str
    feature_id: Optional[str] = None
    timestamp_utc: str
    constitution_hash: str
    spec_hash: str
    plan_hash: str
    tests_passed: int
    pii_violations_found: int = 0
    backstage_catalog_registered: bool = True
    signer_identity: str
    hmac_sha256: str = ""


class AuditSigner:
    """Generates tamper-evident cryptographic compliance receipts."""

    def __init__(self, signing_secret: Optional[str] = None):
        self.secret = (
            signing_secret
            or os.getenv("INSURSPEC_SIGNING_KEY")
            or "sovereign_insurspec_audit_secret_2026"
        ).encode("utf-8")

    @staticmethod
    def hash_file(file_path: Path) -> str:
        if not file_path.is_file():
            return "none"
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def generate_receipt(
        self,
        service_name: str,
        line_of_business: str,
        domain: str,
        constitution_path: Path,
        spec_path: Path,
        plan_path: Path,
        tests_passed: int = 3,
        pii_violations: int = 0,
        backstage_registered: bool = True,
        signer_identity: str = "insurspec-governance-engine@enterprise.internal",
        feature_id: Optional[str] = None,
    ) -> ComplianceReceipt:
        receipt_data = {
            "version": "1.0.0",
            "service_name": service_name,
            "line_of_business": line_of_business,
            "domain": domain,
            "feature_id": feature_id,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "constitution_hash": self.hash_file(constitution_path),
            "spec_hash": self.hash_file(spec_path),
            "plan_hash": self.hash_file(plan_path),
            "tests_passed": tests_passed,
            "pii_violations_found": pii_violations,
            "backstage_catalog_registered": backstage_registered,
            "signer_identity": signer_identity,
        }

        canonical_payload = json.dumps(receipt_data, sort_keys=True).encode("utf-8")
        signature = hmac.new(self.secret, canonical_payload, hashlib.sha256).hexdigest()

        return ComplianceReceipt(**receipt_data, hmac_sha256=signature)

    def write_receipt(self, receipt: ComplianceReceipt, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(receipt.model_dump(), f, indent=2)
        return output_path
