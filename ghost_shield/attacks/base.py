"""Abstract contracts for embedding inversion attacks."""

from abc import ABC, abstractmethod


class BaseInversionAttack(ABC):
    """Standard asynchronous interface for inversion attack implementations."""

    @abstractmethod
    async def fit(self, reference_corpus: list[str]) -> None:
        """Index reference text for later reconstruction attempts."""
        raise NotImplementedError

    @abstractmethod
    async def invert(
        self, target_vectors: list[list[float]], top_k: int = 1
    ) -> list[list[str]]:
        """Return ranked candidate texts for each target vector."""
        raise NotImplementedError
