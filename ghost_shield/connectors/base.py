"""Abstract interface implemented by vector database connectors."""

from abc import ABC, abstractmethod

from .schemas import DeletionReport, Document, QueryResult


class BaseVectorDB(ABC):
    """Standard asynchronous contract for vector database adapters."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize a database connection or local index."""
        raise NotImplementedError

    @abstractmethod
    async def insert(self, documents: list[Document]) -> list[str]:
        """Insert documents and return their identifiers."""
        raise NotImplementedError

    @abstractmethod
    async def search(
        self, query_vector: list[float], top_k: int = 5
    ) -> list[QueryResult]:
        """Return the nearest documents for a query vector."""
        raise NotImplementedError

    @abstractmethod
    async def soft_delete(self, document_ids: list[str]) -> list[DeletionReport]:
        """Mark documents deleted without freeing physical index allocations."""
        raise NotImplementedError

    @abstractmethod
    async def hard_purge(self, document_ids: list[str]) -> list[DeletionReport]:
        """Permanently remove documents and their stored records."""
        raise NotImplementedError

    @abstractmethod
    async def verify_deleted_status(self, document_id: str) -> DeletionReport:
        """Inspect storage for residual vectors or metadata after deletion."""
        raise NotImplementedError
