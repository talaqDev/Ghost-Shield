"""Nearest-neighbor embedding inversion attack."""

import logging
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .base import BaseInversionAttack

logger = logging.getLogger(__name__)


class KNNInversionAttack(BaseInversionAttack):
    """Reconstruct candidate text by nearest-neighbor embedding lookup."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        model: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.model = model
        self.index: faiss.IndexFlatL2 | None = None
        self.reference_corpus: list[str] = []
        self.dimension: int | None = None

    def _get_model(self) -> Any:
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as error:
                logger.exception("Unable to initialize embedding model %s", self.model_name)
                raise RuntimeError(
                    f"Unable to initialize Sentence-Transformers model "
                    f"{self.model_name!r}. Check model availability and network access."
                ) from error
        return self.model

    def _encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        try:
            embeddings = self._get_model().encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as error:
            logger.exception("Failed to encode %d text values", len(texts))
            raise RuntimeError("Sentence embedding failed") from error
        encoded = np.asarray(embeddings, dtype=np.float32)
        if encoded.ndim != 2 or encoded.shape[0] != len(texts):
            raise ValueError("Embedding model returned an invalid embedding shape")
        return encoded

    async def fit(self, reference_corpus: list[str]) -> None:
        """Encode and index the supplied reference text corpus."""
        if any(not isinstance(text, str) or not text.strip() for text in reference_corpus):
            raise ValueError("Reference corpus entries must be non-empty strings")

        self.reference_corpus = list(reference_corpus)
        self.index = None
        self.dimension = None
        if not self.reference_corpus:
            logger.info("KNN attack fitted with an empty reference corpus")
            return

        embeddings = self._encode(self.reference_corpus)
        self.dimension = int(embeddings.shape[1])
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)
        logger.info(
            "Indexed %d reference texts with embedding dimension %d",
            len(self.reference_corpus),
            self.dimension,
        )

    async def invert(
        self, target_vectors: list[list[float]], top_k: int = 1
    ) -> list[list[str]]:
        """Return nearest reference texts for each target embedding."""
        if not target_vectors:
            return []
        if top_k <= 0:
            return [[] for _ in target_vectors]
        if self.index is None or not self.reference_corpus:
            return [[] for _ in target_vectors]
        if self.dimension is None:
            raise RuntimeError("KNN attack index has no embedding dimension")

        targets = np.asarray(target_vectors, dtype=np.float32)
        if targets.ndim != 2 or targets.shape[1] != self.dimension:
            raise ValueError(
                f"Target vectors must have dimension {self.dimension}; "
                f"received shape {targets.shape}"
            )
        distances, indices = self.index.search(
            targets, min(top_k, len(self.reference_corpus))
        )
        candidates: list[list[str]] = []
        for row_indices in indices:
            candidates.append(
                [self.reference_corpus[int(index)] for index in row_indices if index >= 0]
            )
        return candidates
