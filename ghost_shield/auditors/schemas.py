"""Schemas for soft-delete residual leakage audits."""

from pydantic import BaseModel, Field

from ghost_shield.connectors.schemas import DeletionReport


class SoftDeleteAuditReport(BaseModel):
    """Aggregate findings from inspecting soft-deleted vector records."""

    total_audited: int = Field(ge=0)
    soft_deleted_count: int = Field(ge=0)
    residual_artifacts_detected: int = Field(ge=0)
    successful_inversions: int = Field(ge=0)
    max_leakage_score: float = Field(ge=0.0, le=1.0)
    risk_level: str
    details: list[DeletionReport]
