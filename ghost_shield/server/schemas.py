"""Pydantic request and response models for the Ghost Shield API."""

from typing import Literal

from pydantic import BaseModel, Field

from ghost_shield.connectors.schemas import DeletionReport, Document
from ghost_shield.metrics.schemas import LeakageScoreResult

DBType = Literal["faiss", "chroma", "qdrant", "pinecone"]


class AuditRequest(BaseModel):
    """Input for a complete connector vulnerability audit."""

    db_type: DBType
    documents: list[Document] = Field(min_length=1)
    epsilon: float | None = Field(default=None, gt=0)


class AttackRequest(BaseModel):
    """Input for a standalone inversion attack."""

    target_vectors: list[list[float]] = Field(min_length=1)
    reference_corpus: list[str] = Field(min_length=1)
    top_k: int = Field(default=1, ge=1, le=100)


class DefenseRequest(BaseModel):
    """Input for differential privacy document obfuscation."""

    documents: list[Document] = Field(min_length=1)
    epsilon: float = Field(default=1.0, gt=0)
    mechanism: Literal["gaussian", "laplacian"] = "gaussian"


class AuditResponse(BaseModel):
    """Structured result from a complete security audit."""

    db_type: str
    total_documents: int
    soft_delete_leakage_found: bool
    inversion_vulnerability_score: float = Field(ge=0.0, le=1.0)
    risk_level: str
    reports: list[DeletionReport]
    leakage_metrics: LeakageScoreResult | None


class AttackResponse(BaseModel):
    """Ranked text candidates returned by an inversion attack."""

    candidates: list[list[str]]


class DefenseResponse(BaseModel):
    """Obfuscated documents returned by the DP defense endpoint."""

    documents: list[Document]
    mechanism: str
    epsilon: float
