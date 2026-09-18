"""In-memory Pinecone API simulation for local connector testing."""

import asyncio
import logging

import numpy as np

from .base import BaseVectorDB
from .schemas import DeletionReport, Document, QueryResult

logger = logging.getLogger(__name__)


class MockPineconeDriver(BaseVectorDB):
    """Simulate Pinecone records and network latency without cloud credentials."""

    def __init__(self, latency: float = 0.1) -> None:
        if latency < 0:
            raise ValueError("Latency cannot be negative")
        self.latency = latency
        self.index: dict[str, dict[str, object]] = {}

    async def initialize(self) -> None:
        """Reset the simulated remote index."""
        await asyncio.sleep(self.latency)
        self.index.clear()

    async def insert(self, documents: list[Document]) -> list[str]:
        """Upsert documents into the simulated Pinecone index."""
        await asyncio.sleep(self.latency)
        for document in documents:
            if document.vector is None:
                raise ValueError(f"Document {document.id} requires a vector")
            self.index[document.id] = {
                "vector": np.asarray(document.vector, dtype=np.float32),
                "metadata": {
                    **document.metadata,
                    "is_soft_deleted": False,
                    "text": document.text,
                },
            }
        logger.info("Upserted %d documents into mock Pinecone", len(documents))
        return [document.id for document in documents]

    async def search(
        self, query_vector: list[float], top_k: int = 5
    ) -> list[QueryResult]:
        """Return active records ranked by cosine similarity."""
        await asyncio.sleep(self.latency)
        if top_k <= 0 or not self.index:
            return []
        query = np.asarray(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            raise ValueError("Query vector cannot have zero magnitude")

        results: list[QueryResult] = []
        for document_id, record in self.index.items():
            metadata = record["metadata"]
            if not isinstance(metadata, dict) or metadata.get("is_soft_deleted"):
                continue
            vector = record["vector"]
            if not isinstance(vector, np.ndarray) or vector.shape != query.shape:
                raise ValueError("Stored and query vectors must have matching dimensions")
            score = float(np.dot(query, vector) / (query_norm * np.linalg.norm(vector) + 1e-9))
            results.append(
                QueryResult(
                    document=Document(
                        id=document_id,
                        text=str(metadata.get("text", "")),
                        metadata={
                            key: value
                            for key, value in metadata.items()
                            if key not in {"is_soft_deleted", "text"}
                        },
                    ),
                    score=score,
                )
            )
        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]

    async def soft_delete(self, document_ids: list[str]) -> list[DeletionReport]:
        """Set the simulated Pinecone metadata deletion flag."""
        await asyncio.sleep(self.latency)
        reports = []
        for document_id in document_ids:
            record = self.index.get(document_id)
            if record is None:
                reports.append(self._not_found_report(document_id))
                continue
            metadata = record["metadata"]
            if not isinstance(metadata, dict):
                raise TypeError("Mock Pinecone metadata must be a dictionary")
            metadata["is_soft_deleted"] = True
            reports.append(
                DeletionReport(
                    id=document_id,
                    soft_deleted=True,
                    hard_purged=False,
                    residual_artifacts_found=True,
                    details="Metadata flagged soft-deleted in mock Pinecone.",
                )
            )
        return reports

    async def hard_purge(self, document_ids: list[str]) -> list[DeletionReport]:
        """Remove records from the simulated Pinecone index."""
        await asyncio.sleep(self.latency)
        reports = []
        for document_id in document_ids:
            existed = self.index.pop(document_id, None) is not None
            reports.append(
                DeletionReport(
                    id=document_id,
                    soft_deleted=False,
                    hard_purged=existed,
                    residual_artifacts_found=False,
                    details=(
                        "Record purged from mock Pinecone."
                        if existed
                        else "Document ID not found."
                    ),
                )
            )
        return reports

    async def verify_deleted_status(self, document_id: str) -> DeletionReport:
        """Inspect the simulated remote record for deletion artifacts."""
        await asyncio.sleep(self.latency)
        record = self.index.get(document_id)
        if record is None:
            return DeletionReport(
                id=document_id,
                soft_deleted=False,
                hard_purged=True,
                residual_artifacts_found=False,
                details="Record missing from mock Pinecone.",
            )
        metadata = record["metadata"]
        is_soft_deleted = isinstance(metadata, dict) and bool(
            metadata.get("is_soft_deleted")
        )
        return DeletionReport(
            id=document_id,
            soft_deleted=is_soft_deleted,
            hard_purged=False,
            residual_artifacts_found=True,
            details=(
                "Soft-deleted record remains in mock Pinecone."
                if is_soft_deleted
                else "Active record found."
            ),
        )

    @staticmethod
    def _not_found_report(document_id: str) -> DeletionReport:
        return DeletionReport(
            id=document_id,
            soft_deleted=False,
            hard_purged=False,
            residual_artifacts_found=False,
            details="Document ID not found.",
        )
