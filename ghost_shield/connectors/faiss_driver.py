"""FAISS vector database connector."""

import logging

import faiss
import numpy as np

from .base import BaseVectorDB
from .schemas import DeletionReport, Document, QueryResult

logger = logging.getLogger(__name__)


class FAISSDriver(BaseVectorDB):
    """FAISS CPU connector with soft deletion and structural rebuilding."""

    def __init__(self, dimension: int = 384) -> None:
        if dimension <= 0:
            raise ValueError("FAISS dimension must be greater than zero")
        self.dimension = dimension
        self.index: faiss.IndexFlatL2 | None = None
        self.documents: dict[str, Document] = {}
        self.id_to_idx: dict[str, int] = {}
        self.idx_to_id: dict[int, str] = {}
        self.soft_deleted_ids: set[str] = set()

    async def initialize(self) -> None:
        """Create an empty L2 index and clear connector state."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents.clear()
        self.id_to_idx.clear()
        self.idx_to_id.clear()
        self.soft_deleted_ids.clear()
        logger.debug("Initialized FAISS index with dimension %d", self.dimension)

    def _validate_vector(self, vector: list[float], label: str) -> None:
        if len(vector) != self.dimension:
            raise ValueError(
                f"{label} must have vector dimension {self.dimension}; "
                f"received {len(vector)}"
            )

    async def insert(self, documents: list[Document]) -> list[str]:
        """Add documents with vectors to the FAISS index."""
        if self.index is None:
            await self.initialize()
        if not documents:
            return []

        for document in documents:
            if document.id in self.documents:
                raise ValueError(f"Document ID already exists: {document.id}")
            if document.vector is None:
                raise ValueError(f"Document {document.id} requires a vector")
            self._validate_vector(document.vector, f"Document {document.id}")

        assert self.index is not None
        start_idx = self.index.ntotal
        vectors = np.asarray([document.vector for document in documents], dtype=np.float32)
        self.index.add(vectors)

        inserted_ids = []
        for offset, document in enumerate(documents):
            index = start_idx + offset
            self.documents[document.id] = document
            self.id_to_idx[document.id] = index
            self.idx_to_id[index] = document.id
            inserted_ids.append(document.id)
        logger.info("Inserted %d documents into FAISS", len(inserted_ids))
        return inserted_ids

    async def search(
        self, query_vector: list[float], top_k: int = 5
    ) -> list[QueryResult]:
        """Search nearest active documents, excluding soft-deleted IDs."""
        if top_k <= 0:
            return []
        self._validate_vector(query_vector, "Query vector")
        if self.index is None or self.index.ntotal == 0:
            return []

        fetch_k = min(self.index.ntotal, top_k + len(self.soft_deleted_ids))
        distances, indices = self.index.search(
            np.asarray([query_vector], dtype=np.float32), fetch_k
        )
        results: list[QueryResult] = []
        for distance, index in zip(distances[0], indices[0]):
            document_id = self.idx_to_id.get(int(index))
            if document_id is None or document_id in self.soft_deleted_ids:
                continue
            results.append(
                QueryResult(
                    document=self.documents[document_id],
                    score=float(1.0 / (1.0 + distance)),
                )
            )
            if len(results) == top_k:
                break
        return results

    async def soft_delete(self, document_ids: list[str]) -> list[DeletionReport]:
        """Flag documents while retaining their raw vectors in the index."""
        reports = []
        for document_id in document_ids:
            if document_id not in self.documents:
                reports.append(
                    DeletionReport(
                        id=document_id,
                        soft_deleted=False,
                        hard_purged=False,
                        residual_artifacts_found=False,
                        details="Document ID not found.",
                    )
                )
                continue
            self.soft_deleted_ids.add(document_id)
            reports.append(
                DeletionReport(
                    id=document_id,
                    soft_deleted=True,
                    hard_purged=False,
                    residual_artifacts_found=True,
                    details="Flagged as soft-deleted; raw vector remains in FAISS.",
                )
            )
        return reports

    async def hard_purge(self, document_ids: list[str]) -> list[DeletionReport]:
        """Rebuild the FAISS index without the requested documents."""
        purge_set = set(document_ids)
        existing_ids = set(self.documents)
        remaining_documents = [
            document
            for document_id, document in self.documents.items()
            if document_id not in purge_set
        ]
        remaining_soft_deleted = self.soft_deleted_ids - purge_set

        reports = [
            DeletionReport(
                id=document_id,
                soft_deleted=False,
                hard_purged=document_id in existing_ids,
                residual_artifacts_found=False,
                details=(
                    "Purged from FAISS by structural rebuild."
                    if document_id in existing_ids
                    else "Document ID not found."
                ),
            )
            for document_id in document_ids
        ]

        await self.initialize()
        if remaining_documents:
            await self.insert(remaining_documents)
            self.soft_deleted_ids = remaining_soft_deleted
        logger.info("Hard purged %d requested documents from FAISS", len(document_ids))
        return reports

    async def verify_deleted_status(self, document_id: str) -> DeletionReport:
        """Inspect document and index mappings for residual vector artifacts."""
        exists = document_id in self.documents
        has_index_mapping = document_id in self.id_to_idx
        is_soft_deleted = document_id in self.soft_deleted_ids
        return DeletionReport(
            id=document_id,
            soft_deleted=is_soft_deleted,
            hard_purged=not exists,
            residual_artifacts_found=has_index_mapping,
            details=(
                "Raw vector entry remains in the FAISS index."
                if is_soft_deleted
                else "Active record found."
                if exists
                else "Record completely removed from FAISS."
            ),
        )
