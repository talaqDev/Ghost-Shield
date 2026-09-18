"""Schemas returned by privacy leakage metrics."""

from pydantic import BaseModel, Field


class LeakageScoreResult(BaseModel):
    """Similarity metrics and the resulting privacy leakage assessment."""

    original_text: str
    reconstructed_text: str
    cosine_similarity: float = Field(ge=0.0, le=1.0)
    bleu_score: float = Field(ge=0.0, le=1.0)
    rouge_1: float = Field(ge=0.0, le=1.0)
    rouge_2: float = Field(ge=0.0, le=1.0)
    rouge_l: float = Field(ge=0.0, le=1.0)
    overall_leakage_score: float = Field(ge=0.0, le=1.0)
    risk_level: str
