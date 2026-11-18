from pathlib import Path
from insur_spec.core.reviewer import DiffReviewer


def test_diff_reviewer_blocks_destructive_sql_and_secrets(tmp_path: Path):
    reviewer = DiffReviewer(tmp_path)
    bad_diff = (
        "diff --git a/db/migrate.sql b/db/migrate.sql\n"
        "+++ b/db/migrate.sql\n"
        "@@ -1,0 +1,2 @@\n"
        "+DROP TABLE legacy_claims;\n"
        "diff --git a/src/auth.py b/src/auth.py\n"
        "+++ b/src/auth.py\n"
        "@@ -1,0 +1,2 @@\n"
        "+AWS_KEY = 'AKIA1234567890ABCDEF'\n"
    )
    report = reviewer.review_diff_text(bad_diff)
    assert report.passed is False
    assert report.files_reviewed == 2
    assert any("DROP TABLE" in f.description for f in report.findings)
    assert any("AWS Access Key" in f.description for f in report.findings)


def test_diff_reviewer_passes_clean_diff(tmp_path: Path):
    reviewer = DiffReviewer(tmp_path)
    clean_diff = (
        "diff --git a/src/claims.py b/src/claims.py\n"
        "+++ b/src/claims.py\n"
        "@@ -1,0 +1,2 @@\n"
        "+def get_claim_status(claim_id: str) -> str:\n"
        "+    return 'OPEN'\n"
    )
    report = reviewer.review_diff_text(clean_diff)
    assert report.passed is True
    assert len(report.findings) == 0
