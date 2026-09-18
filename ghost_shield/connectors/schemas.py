"""Pydantic models shared by vector database connectors."""

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A text payload and its optional embedding and metadata."""

    id: str
    text: str
    metadata: dict = Field(default_factory=dict)
    vector: list[float] | None = None


class QueryResult(BaseModel):
    """A document returned from a similarity search."""

    document: Document
    score: float
    is_soft_deleted: bool = False


class DeletionReport(BaseModel):
    """Report describing the outcome of a deletion or verification operation."""

    id: str
    soft_deleted: bool
    hard_purged: bool
    residual_artifacts_found: bool
    details: str
