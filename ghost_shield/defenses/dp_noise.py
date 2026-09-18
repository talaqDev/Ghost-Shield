"""Differential privacy noise for vector embeddings."""

import logging
from typing import Literal

import numpy as np

from ghost_shield.connectors.schemas import Document

logger = logging.getLogger(__name__)
Mechanism = Literal["gaussian", "laplacian"]


class DPNoiseGenerator:
    """Obfuscate embeddings with Gaussian or Laplacian differential privacy noise."""

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        mechanism: Mechanism = "gaussian",
    ) -> None:
        if epsilon <= 0:
            raise ValueError("epsilon must be greater than zero")
        if not 0 < delta < 1:
            raise ValueError("delta must be between zero and one")
        if mechanism not in {"gaussian", "laplacian"}:
            raise ValueError("mechanism must be 'gaussian' or 'laplacian'")
        self.epsilon = epsilon
        self.delta = delta
        self.mechanism = mechanism

    def _scale(self) -> float:
        if self.mechanism == "gaussian":
            return float(np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon)
        return float(1.0 / self.epsilon)

    def apply_noise(self, vector: list[float] | np.ndarray) -> list[float]:
        """Add calibrated noise and return a unit-L2 normalized embedding."""
        values = np.asarray(vector, dtype=np.float64)
        if values.ndim != 1 or values.size == 0:
            raise ValueError("vector must be a non-empty one-dimensional sequence")
        if not np.all(np.isfinite(values)):
            raise ValueError("vector must contain only finite values")

        scale = self._scale()
        if self.mechanism == "gaussian":
            noise = np.random.normal(0.0, scale, size=values.shape)
        else:
            noise = np.random.laplace(0.0, scale, size=values.shape)
        obfuscated = values + noise
        norm = float(np.linalg.norm(obfuscated))
        if norm == 0:
            raise ValueError("noise produced a zero-norm vector")
        return (obfuscated / norm).astype(np.float32).tolist()

    def obfuscate_documents(self, documents: list[Document]) -> list[Document]:
        """Return deep-copied documents with their vectors differentially obfuscated."""
        obfuscated_documents = []
        for document in documents:
            if document.vector is None:
                raise ValueError(f"Document {document.id} requires a vector")
            obfuscated_documents.append(
                document.model_copy(
                    deep=True,
                    update={"vector": self.apply_noise(document.vector)},
                )
            )
        logger.info("Obfuscated %d document embeddings", len(obfuscated_documents))
        return obfuscated_documents
