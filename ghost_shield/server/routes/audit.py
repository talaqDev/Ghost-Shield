"""End-to-end vector database audit route."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from ghost_shield.attacks import KNNInversionAttack
from ghost_shield.connectors import (
    ChromaDriver,
    FAISSDriver,
    MockPineconeDriver,
    QdrantDriver,
)
from ghost_shield.defenses import DPNoiseGenerator
from ghost_shield.metrics import LeakageScorer

from ..schemas import AuditRequest, AuditResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["audits"])


def _driver(db_type: str, dimension: int) -> Any:
    if db_type == "faiss":
        return FAISSDriver(dimension=dimension)
    if db_type == "chroma":
        return ChromaDriver(collection_name=f"audit_{uuid.uuid4().hex}")
    if db_type == "qdrant":
        return QdrantDriver(collection_name=f"audit_{uuid.uuid4().hex}", dimension=dimension)
    if db_type == "pinecone":
        return MockPineconeDriver(latency=0.0)
    raise ValueError(f"Unsupported database type: {db_type}")


@router.post("/run", response_model=AuditResponse)
async def run_audit(request: AuditRequest) -> AuditResponse:
    """Run insertion, inversion, soft-delete, and residual-risk checks."""
    try:
        vectors = [document.vector for document in request.documents]
        if any(vector is None for vector in vectors):
            raise ValueError("Every audit document requires an embedding vector")
        dimension = len(vectors[0])
        if dimension == 0 or any(len(vector or []) != dimension for vector in vectors):
            raise ValueError("All audit vectors must have the same non-zero dimension")

        documents = request.documents
        if request.epsilon is not None:
            documents = DPNoiseGenerator(epsilon=request.epsilon).obfuscate_documents(documents)
        driver = _driver(request.db_type, dimension)
        await driver.initialize()
        await driver.insert(documents)

        target = documents[0]
        attack = KNNInversionAttack()
        await attack.fit([document.text for document in documents])
        active_results = await driver.search(target.vector or [], top_k=1)
        leakage_metrics = None
        if active_results and active_results[0].document.vector is not None:
            candidates = await attack.invert([active_results[0].document.vector], top_k=1)
            if candidates and candidates[0]:
                leakage_metrics = LeakageScorer(
                    embedding_model=attack.model
                ).compute_score(target.text, candidates[0][0])

        soft_report = (await driver.soft_delete([target.id]))[0]
        status = await driver.verify_deleted_status(target.id)
        risk_score = leakage_metrics.overall_leakage_score if leakage_metrics else 0.0
        return AuditResponse(
            db_type=request.db_type,
            total_documents=len(documents),
            soft_delete_leakage_found=(
                soft_report.residual_artifacts_found
                or status.residual_artifacts_found
            ),
            inversion_vulnerability_score=risk_score,
            risk_level=leakage_metrics.risk_level if leakage_metrics else "LOW",
            reports=[soft_report, status],
            leakage_metrics=leakage_metrics,
        )
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected audit failure")
        raise HTTPException(status_code=500, detail="Audit failed") from error
