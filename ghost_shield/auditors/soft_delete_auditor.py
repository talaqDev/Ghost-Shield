"""Audit residual vector leakage after soft deletion."""

import logging

from ghost_shield.attacks import BaseInversionAttack
from ghost_shield.connectors import BaseVectorDB
from ghost_shield.connectors.schemas import DeletionReport, Document
from ghost_shield.metrics import LeakageScorer

from .schemas import SoftDeleteAuditReport

logger = logging.getLogger(__name__)


class SoftDeleteAuditor:
    """Inspect soft-deleted storage and attempt inversion of residual vectors."""

    def __init__(
        self,
        database: BaseVectorDB,
        inversion_attack: BaseInversionAttack,
        leakage_scorer: LeakageScorer | None = None,
    ) -> None:
        self.database = database
        self.inversion_attack = inversion_attack
        self.leakage_scorer = leakage_scorer or LeakageScorer(
            embedding_model=getattr(inversion_attack, "model", None)
        )

    async def _extract_residual_vector(
        self, document_id: str
    ) -> tuple[list[float] | None, str | None]:
        """Extract a raw vector and source text from supported connector storage."""
        documents = getattr(self.database, "documents", None)
        if isinstance(documents, dict) and document_id in documents:
            document = documents[document_id]
            if isinstance(document, Document):
                return document.vector, document.text

        collection = getattr(self.database, "collection", None)
        if collection is not None:
            record = collection.get(
                ids=[document_id],
                include=["embeddings", "documents"],
            )
            ids = record.get("ids", [])
            if ids and record.get("embeddings"):
                vector = record["embeddings"][0]
                text_values = record.get("documents") or [None]
                return list(vector), text_values[0]
        return None, None

    @staticmethod
    def _risk_level(score: float, residual_count: int) -> str:
        if residual_count == 0 or score < 0.25:
            return "LOW"
        if score >= 0.75:
            return "CRITICAL"
        if score >= 0.50:
            return "HIGH"
        return "MEDIUM"

    async def run_audit(
        self, documents: list[Document], target_ids: list[str]
    ) -> SoftDeleteAuditReport:
        """Insert, soft-delete, inspect, and attack selected document records."""
        if not documents:
            raise ValueError("At least one document is required")
        if not target_ids:
            raise ValueError("At least one target ID is required")
        by_id = {document.id: document for document in documents}
        missing_ids = [document_id for document_id in target_ids if document_id not in by_id]
        if missing_ids:
            raise ValueError(f"Target IDs are not in documents: {missing_ids}")
        if any(document.vector is None for document in documents):
            raise ValueError("Every document requires a vector")

        await self.database.initialize()
        await self.database.insert(documents)
        await self.inversion_attack.fit([document.text for document in documents])
        deletion_reports = await self.database.soft_delete(target_ids)
        details: list[DeletionReport] = []
        max_score = 0.0
        successful_inversions = 0
        residual_count = 0

        for document_id, deletion_report in zip(target_ids, deletion_reports):
            verification = await self.database.verify_deleted_status(document_id)
            residual_vector, residual_text = await self._extract_residual_vector(document_id)
            if residual_vector is not None:
                residual_count += 1
            if residual_vector is not None and residual_text is not None:
                candidates = await self.inversion_attack.invert([residual_vector], top_k=1)
                if candidates and candidates[0]:
                    successful_inversions += 1
                    metrics = self.leakage_scorer.compute_score(
                        residual_text,
                        candidates[0][0],
                        embedding_model=getattr(self.inversion_attack, "model", None),
                    )
                    max_score = max(max_score, metrics.overall_leakage_score)
            details.append(
                verification.model_copy(
                    update={
                        "soft_deleted": deletion_report.soft_deleted,
                        "residual_artifacts_found": (
                            deletion_report.residual_artifacts_found
                            or verification.residual_artifacts_found
                            or residual_vector is not None
                        ),
                        "details": (
                            f"{deletion_report.details} "
                            f"Verification: {verification.details}"
                        ),
                    }
                )
            )

        logger.info(
            "Soft-delete audit found %d residual vectors and %d inversions",
            residual_count,
            successful_inversions,
        )
        return SoftDeleteAuditReport(
            total_audited=len(target_ids),
            soft_deleted_count=sum(
                report.soft_deleted for report in deletion_reports
            ),
            residual_artifacts_detected=residual_count,
            successful_inversions=successful_inversions,
            max_leakage_score=max_score,
            risk_level=self._risk_level(max_score, residual_count),
            details=details,
        )
