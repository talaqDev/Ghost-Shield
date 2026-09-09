from .base import VectorStoreAdapter


class FaissAdapter(VectorStoreAdapter):
    """Dependency-free local contract for a future faiss index."""

    def __init__(self) -> None:
        self.records: dict[str, dict] = {}

    def insert(self, item_id: str, vector: list[float], metadata: dict) -> None:
        self.records[item_id] = {"id": item_id, "vector": vector, "metadata": metadata}

    def delete(self, item_id: str) -> None:
        self.records.pop(item_id, None)

    def query(self, vector: list[float], limit: int = 5) -> list[dict]:
        return list(self.records.values())[:limit]
