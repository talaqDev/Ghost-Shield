"""JSON, HTML, and optional PDF security audit report generation."""

import html
import json
import logging
from pathlib import Path

from ghost_shield.auditors.schemas import SoftDeleteAuditReport

logger = logging.getLogger(__name__)


class ReportExporter:
    """Serialize soft-delete audit results into machine and human-readable reports."""

    def export_json(self, audit_report: SoftDeleteAuditReport, output_path: str) -> str:
        """Write a formatted JSON report and return its resolved file path."""
        path = self._prepare_path(output_path, ".json")
        path.write_text(
            json.dumps(audit_report.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        return str(path)

    def export_html_report(self, audit_report: SoftDeleteAuditReport) -> str:
        """Return a styled HTML security report as a string."""
        risk = html.escape(audit_report.risk_level)
        rows = "".join(
            "<tr>"
            f"<td>{html.escape(detail.id)}</td>"
            f"<td>{'Yes' if detail.soft_deleted else 'No'}</td>"
            f"<td>{'Yes' if detail.residual_artifacts_found else 'No'}</td>"
            f"<td>{html.escape(detail.details)}</td>"
            "</tr>"
            for detail in audit_report.details
        )
        recommendation = (
            "Immediately hard-purge affected records and rotate any exposed embeddings."
            if audit_report.risk_level in {"CRITICAL", "HIGH"}
            else "Continue monitoring deletion verification and enforce physical purge policies."
        )
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><title>Ghost Shield Security Audit</title>
<style>
body {{ font-family: Arial, sans-serif; color: #17221d; margin: 42px; }}
h1 {{ color: #183b2b; margin-bottom: 4px; }}
.subtitle {{ color: #64736a; }}
.summary {{ display: flex; gap: 16px; margin: 28px 0; }}
.metric {{ border: 1px solid #c9d8ce; padding: 16px; min-width: 150px; }}
.metric strong {{ display: block; font-size: 25px; margin-top: 7px; }}
.risk {{ color: #a44225; }} table {{ border-collapse: collapse; width: 100%; margin-top: 18px; }}
th, td {{ border: 1px solid #c9d8ce; padding: 10px; text-align: left; }}
th {{ background: #e9f1eb; }} .recommendation {{ background: #f5f8f5; padding: 16px; margin-top: 26px; }}
</style></head>
<body>
<h1>Ghost Shield Security Audit</h1>
<p class="subtitle">Soft-delete residual leakage assessment</p>
<div class="summary">
<div class="metric">Records audited<strong>{audit_report.total_audited}</strong></div>
<div class="metric">Residual artifacts<strong>{audit_report.residual_artifacts_detected}</strong></div>
<div class="metric">Successful inversions<strong>{audit_report.successful_inversions}</strong></div>
<div class="metric">Risk level<strong class="risk">{risk}</strong></div>
<div class="metric">Max leakage<strong>{audit_report.max_leakage_score:.2%}</strong></div>
</div>
<h2>Deletion verification details</h2>
<table><thead><tr><th>Record ID</th><th>Soft deleted</th><th>Residual artifact</th><th>Details</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="recommendation"><strong>Recommendation:</strong> {html.escape(recommendation)}</div>
</body></html>"""

    def export_pdf(self, audit_report: SoftDeleteAuditReport, output_path: str) -> str:
        """Write a PDF when ReportLab is available, otherwise write an HTML fallback."""
        path = self._prepare_path(output_path, ".pdf")
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            fallback = path.with_suffix(".html")
            fallback.write_text(self.export_html_report(audit_report), encoding="utf-8")
            logger.info("ReportLab unavailable; exported HTML fallback to %s", fallback)
            return str(fallback)

        pdf = canvas.Canvas(str(path), pagesize=letter)
        width, height = letter
        y = height - 54
        pdf.setTitle("Ghost Shield Security Audit")
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(48, y, "Ghost Shield Security Audit")
        y -= 28
        pdf.setFont("Helvetica", 11)
        lines = [
            f"Risk level: {audit_report.risk_level}",
            f"Maximum leakage score: {audit_report.max_leakage_score:.2%}",
            f"Records audited: {audit_report.total_audited}",
            f"Residual artifacts: {audit_report.residual_artifacts_detected}",
            f"Successful inversions: {audit_report.successful_inversions}",
            "",
            "Deletion verification details:",
        ]
        for line in lines:
            pdf.drawString(48, y, line)
            y -= 18
        for detail in audit_report.details:
            text = f"{detail.id}: {detail.details}"
            pdf.drawString(60, y, text[:105])
            y -= 16
            if y < 54:
                pdf.showPage()
                y = height - 54
                pdf.setFont("Helvetica", 11)
        pdf.save()
        return str(path)

    @staticmethod
    def _prepare_path(output_path: str, suffix: str) -> Path:
        """Create a safe parent directory and normalize the report suffix."""
        if not output_path or not output_path.strip():
            raise ValueError("output_path must not be empty")
        path = Path(output_path).expanduser()
        if path.exists() and path.is_dir():
            raise ValueError("output_path must name a file")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.with_suffix(suffix)
