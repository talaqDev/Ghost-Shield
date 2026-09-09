from abc import ABC, abstractmethod


class VectorStoreAdapter(ABC):
    @abstractmethod
    def insert(self, item_id: str, vector: list[float], metadata: dict) -> None: ...

    @abstractmethod
    def delete(self, item_id: str) -> None: ...

    @abstractmethod
    def query(self, vector: list[float], limit: int = 5) -> list[dict]: ...
