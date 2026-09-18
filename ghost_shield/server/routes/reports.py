"""Downloadable audit report API route."""

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from ghost_shield.auditors.schemas import SoftDeleteAuditReport
from ghost_shield.reports import ReportExporter

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportExportRequest(BaseModel):
    """Audit report and requested downloadable format."""

    audit_report: SoftDeleteAuditReport
    format: Literal["json", "pdf"] = "json"


@router.post("/export")
async def export_report(request: ReportExportRequest) -> Response:
    """Return a JSON report or PDF/HTML fallback as a downloadable attachment."""
    try:
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory(prefix="ghost-shield-report-") as directory:
            requested = Path(directory) / "security-audit"
            if request.format == "json":
                path = Path(exporter.export_json(request.audit_report, str(requested)))
                media_type = "application/json"
            else:
                path = Path(exporter.export_pdf(request.audit_report, str(requested)))
                media_type = "application/pdf" if path.suffix == ".pdf" else "text/html"
            content = path.read_bytes()
            filename = path.name
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Report export failed") from error
