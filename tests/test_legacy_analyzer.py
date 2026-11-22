from pathlib import Path
from insur_spec.core.legacy_analyzer import LegacyRepoAnalyzer


def test_legacy_analyzer_discovers_stack_pii_and_findings(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n\n"
        "def process_claim(ssn: str):\n"
        "    try:\n"
        "        return ssn\n"
        "    except Exception:\n"
        "        pass\n",
        encoding="utf-8",
    )
    (src_dir / "migrate.sql").write_text("DROP TABLE old_claims;\n", encoding="utf-8")

    analyzer = LegacyRepoAnalyzer(tmp_path)
    report = analyzer.analyze()

    assert report.total_files == 2
    assert "Python" in report.languages
    assert "src/app.py" in report.entry_points
    assert "FastAPI / REST" in report.detected_integrations
    assert "src/app.py" in report.pii_surface_files
    assert any("DROP TABLE" in f["description"] for f in report.constitution_findings)
    assert any("except: pass" in f["description"] for f in report.constitution_findings)

    summary = analyzer.format_markdown_summary(report)
    assert "Repository Analysis Baseline" in summary
    assert "src/app.py" in summary
