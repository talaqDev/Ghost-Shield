"""ChromaDB vector database connector."""

import logging
from pathlib import Path
from typing import Any

import chromadb

from .base import BaseVectorDB
from .schemas import DeletionReport, Document, QueryResult

logger = logging.getLogger(__name__)


class ChromaDriver(BaseVectorDB):
    """ChromaDB connector using metadata flags for soft deletion."""

    def __init__(
        self,
        collection_name: str = "ghost_shield_audit",
        persist_directory: str | Path | None = None,
    ) -> None:
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory) if persist_directory else None
        self.client: Any = None
        self.collection: Any = None

    async def initialize(self) -> None:
        """Create an ephemeral or persistent Chroma client and collection."""
        if self.persist_directory is None:
            self.client = chromadb.EphemeralClient()
        else:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.debug("Initialized Chroma collection %s", self.collection_name)

    async def insert(self, documents: list[Document]) -> list[str]:
        """Insert documents, embeddings, text, and active metadata flags."""
        if self.collection is None:
            await self.initialize()
        if not documents:
            return []
        if any(document.vector is None for document in documents):
            raise ValueError("Every document requires a vector for Chroma insertion")

        ids = [document.id for document in documents]
        if len(ids) != len(set(ids)):
            raise ValueError("Document IDs must be unique within an insert batch")
        existing = self.collection.get(ids=ids, include=[])["ids"]
        if existing:
            raise ValueError(f"Document IDs already exist: {existing}")

        metadatas = [
            {**document.metadata, "is_soft_deleted": False} for document in documents
        ]
        self.collection.add(
            ids=ids,
            embeddings=[document.vector for document in documents],
            metadatas=metadatas,
            documents=[document.text for document in documents],
        )
        logger.info("Inserted %d documents into Chroma", len(ids))
        return ids

    async def search(
        self, query_vector: list[float], top_k: int = 5
    ) -> list[QueryResult]:
        """Search active Chroma records using the soft-delete metadata filter."""
        if top_k <= 0 or self.collection is None or self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, self.collection.count()),
            where={"is_soft_deleted": False},
            include=["documents", "metadatas", "distances", "embeddings"],
        )
        query_results: list[QueryResult] = []
        ids = results.get("ids", [[]])[0]
        for index, document_id in enumerate(ids):
            metadata = results.get("metadatas", [[]])[0][index] or {}
            embedding = results.get("embeddings", [[]])[0][index]
            document = Document(
                id=document_id,
                text=results["documents"][0][index],
                metadata={
                    key: value
                    for key, value in metadata.items()
                    if key != "is_soft_deleted"
                },
                vector=list(embedding) if embedding is not None else None,
            )
            query_results.append(
                QueryResult(
                    document=document,
                    score=float(1.0 - results["distances"][0][index]),
                )
            )
        return query_results

    async def soft_delete(self, document_ids: list[str]) -> list[DeletionReport]:
        """Set the soft-delete metadata flag without removing the Chroma record."""
        if self.collection is None:
            await self.initialize()
        reports = []
        for document_id in document_ids:
            record = self.collection.get(ids=[document_id], include=["metadatas"])
            if not record["ids"]:
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
            metadata = record["metadatas"][0] or {}
            metadata["is_soft_deleted"] = True
            self.collection.update(ids=[document_id], metadatas=[metadata])
            reports.append(
                DeletionReport(
                    id=document_id,
                    soft_deleted=True,
                    hard_purged=False,
                    residual_artifacts_found=True,
                    details="Soft-deleted metadata flag set; vector remains stored.",
                )
            )
        return reports

    async def hard_purge(self, document_ids: list[str]) -> list[DeletionReport]:
        """Delete requested records from the Chroma collection."""
        if self.collection is None:
            await self.initialize()
        reports = []
        for document_id in document_ids:
            record = self.collection.get(ids=[document_id], include=[])
            existed = bool(record["ids"])
            if existed:
                self.collection.delete(ids=[document_id])
            reports.append(
                DeletionReport(
                    id=document_id,
                    soft_deleted=False,
                    hard_purged=existed,
                    residual_artifacts_found=False,
                    details=(
                        "Hard purged from Chroma collection."
                        if existed
                        else "Document ID not found."
                    ),
                )
            )
        return reports

    async def verify_deleted_status(self, document_id: str) -> DeletionReport:
        """Query Chroma directly to detect soft-deleted or residual records."""
        if self.collection is None:
            await self.initialize()
        record = self.collection.get(ids=[document_id], include=["metadatas"])
        if not record["ids"]:
            return DeletionReport(
                id=document_id,
                soft_deleted=False,
                hard_purged=True,
                residual_artifacts_found=False,
                details="Document physically absent from Chroma collection.",
            )
        metadata = record["metadatas"][0] or {}
        is_soft_deleted = metadata.get("is_soft_deleted") is True
        return DeletionReport(
            id=document_id,
            soft_deleted=is_soft_deleted,
            hard_purged=False,
            residual_artifacts_found=True,
            details=(
                "Soft-deleted record still found in Chroma collection."
                if is_soft_deleted
                else "Active document found in Chroma collection."
            ),
        )
