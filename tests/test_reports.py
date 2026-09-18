import json

from fastapi.testclient import TestClient

from ghost_shield.auditors.schemas import SoftDeleteAuditReport
from ghost_shield.connectors.schemas import DeletionReport
from ghost_shield.reports import ReportExporter
from ghost_shield.server.app import app

client = TestClient(app)


def audit_report() -> SoftDeleteAuditReport:
    return SoftDeleteAuditReport(
        total_audited=2,
        soft_deleted_count=2,
        residual_artifacts_detected=2,
        successful_inversions=1,
        max_leakage_score=0.82,
        risk_level="CRITICAL",
        details=[
            DeletionReport(
                id="patient-1",
                soft_deleted=True,
                hard_purged=False,
                residual_artifacts_found=True,
                details="Raw vector remains in storage.",
            )
        ],
    )


def test_json_export_generation(tmp_path) -> None:
    path = ReportExporter().export_json(audit_report(), str(tmp_path / "audit.json"))

    payload = json.loads(open(path, encoding="utf-8").read())
    assert payload["risk_level"] == "CRITICAL"
    assert payload["details"][0]["id"] == "patient-1"


def test_html_report_contains_summary_and_recommendation() -> None:
    html = ReportExporter().export_html_report(audit_report())

    assert "Ghost Shield Security Audit" in html
    assert "CRITICAL" in html
    assert "patient-1" in html
    assert "Recommendation" in html
    assert "hard-purge" in html


def test_pdf_export_or_html_fallback(tmp_path) -> None:
    path = ReportExporter().export_pdf(audit_report(), str(tmp_path / "audit.pdf"))
    exported = open(path, "rb").read()

    assert exported
    if path.endswith(".html"):
        assert b"Ghost Shield Security Audit" in exported
    else:
        assert exported.startswith(b"%PDF")


def test_report_export_json_endpoint() -> None:
    response = client.post(
        "/reports/export",
        json={"audit_report": audit_report().model_dump(), "format": "json"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment" in response.headers["content-disposition"]
    assert response.json()["risk_level"] == "CRITICAL"


def test_report_export_pdf_endpoint_returns_pdf_or_fallback() -> None:
    response = client.post(
        "/reports/export",
        json={"audit_report": audit_report().model_dump(), "format": "pdf"},
    )

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["content-type"].startswith(("application/pdf", "text/html"))
    assert response.content
