"""Qdrant in-memory vector database connector."""

import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient, models

from .base import BaseVectorDB
from .schemas import DeletionReport, Document, QueryResult

logger = logging.getLogger(__name__)


class QdrantDriver(BaseVectorDB):
    """Qdrant local-memory connector with payload-based soft deletion."""

    def __init__(self, collection_name: str = "ghost_shield", dimension: int = 384) -> None:
        if dimension <= 0:
            raise ValueError("Qdrant dimension must be greater than zero")
        self.collection_name = collection_name
        self.dimension = dimension
        self.client = QdrantClient(":memory:")
        self._initialized = False

    def _hash_id(self, document_id: str) -> str:
        """Map an application ID deterministically to a Qdrant UUID."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, document_id))

    def _validate_vector(self, vector: list[float], label: str) -> None:
        if len(vector) != self.dimension:
            raise ValueError(
                f"{label} must have vector dimension {self.dimension}; "
                f"received {len(vector)}"
            )

    async def initialize(self) -> None:
        """Recreate the configured in-memory collection."""
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.dimension, distance=models.Distance.COSINE
            ),
        )
        self._initialized = True
        logger.debug("Initialized Qdrant collection %s", self.collection_name)

    async def insert(self, documents: list[Document]) -> list[str]:
        """Insert documents as Qdrant points with searchable payload metadata."""
        if not self._initialized:
            await self.initialize()
        if not documents:
            return []

        points = []
        for document in documents:
            if document.vector is None:
                raise ValueError(f"Document {document.id} requires a vector")
            self._validate_vector(document.vector, f"Document {document.id}")
            payload = {
                **document.metadata,
                "is_soft_deleted": False,
                "original_id": document.id,
                "text": document.text,
            }
            points.append(
                models.PointStruct(
                    id=self._hash_id(document.id),
                    vector=document.vector,
                    payload=payload,
                )
            )
        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info("Inserted %d documents into Qdrant", len(points))
        return [document.id for document in documents]

    async def search(
        self, query_vector: list[float], top_k: int = 5
    ) -> list[QueryResult]:
        """Search Qdrant while filtering out soft-deleted payloads."""
        if top_k <= 0 or not self._initialized:
            return []
        self._validate_vector(query_vector, "Query vector")
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="is_soft_deleted",
                        match=models.MatchValue(value=False),
                    )
                ]
            ),
        )
        parsed_results: list[QueryResult] = []
        for result in results:
            payload: dict[str, Any] = result.payload or {}
            document = Document(
                id=str(payload.get("original_id", result.id)),
                text=str(payload.get("text", "")),
                metadata={
                    key: value
                    for key, value in payload.items()
                    if key not in {"is_soft_deleted", "original_id", "text"}
                },
            )
            parsed_results.append(QueryResult(document=document, score=float(result.score)))
        return parsed_results

    async def soft_delete(self, document_ids: list[str]) -> list[DeletionReport]:
        """Flag existing Qdrant points while leaving vectors physically present."""
        if not self._initialized:
            await self.initialize()
        reports = []
        for document_id in document_ids:
            point_id = self._hash_id(document_id)
            records = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False,
            )
            if not records:
                reports.append(self._not_found_report(document_id))
                continue
            self.client.set_payload(
                collection_name=self.collection_name,
                payload={"is_soft_deleted": True},
                points=[point_id],
            )
            reports.append(
                DeletionReport(
                    id=document_id,
                    soft_deleted=True,
                    hard_purged=False,
                    residual_artifacts_found=True,
                    details="Payload flagged soft-deleted; vector remains in Qdrant.",
                )
            )
        return reports

    async def hard_purge(self, document_ids: list[str]) -> list[DeletionReport]:
        """Permanently delete requested Qdrant points."""
        if not self._initialized:
            await self.initialize()
        reports = []
        for document_id in document_ids:
            point_id = self._hash_id(document_id)
            records = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=False,
                with_vectors=False,
            )
            existed = bool(records)
            if existed:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=[point_id]),
                )
            reports.append(
                DeletionReport(
                    id=document_id,
                    soft_deleted=False,
                    hard_purged=existed,
                    residual_artifacts_found=False,
                    details=(
                        "Point permanently deleted from Qdrant."
                        if existed
                        else "Document ID not found."
                    ),
                )
            )
        return reports

    async def verify_deleted_status(self, document_id: str) -> DeletionReport:
        """Retrieve a point directly to detect residual vectors or payloads."""
        if not self._initialized:
            await self.initialize()
        records = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[self._hash_id(document_id)],
            with_payload=True,
            with_vectors=True,
        )
        if not records:
            return DeletionReport(
                id=document_id,
                soft_deleted=False,
                hard_purged=True,
                residual_artifacts_found=False,
                details="Point entirely missing from Qdrant.",
            )
        is_soft_deleted = records[0].payload.get("is_soft_deleted", False)
        return DeletionReport(
            id=document_id,
            soft_deleted=bool(is_soft_deleted),
            hard_purged=False,
            residual_artifacts_found=True,
            details=(
                "Soft-deleted payload and vector still exist."
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
