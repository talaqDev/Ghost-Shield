"""PyTorch MLP embedding inversion attack."""

import hashlib
import logging
import re
from collections import Counter
from typing import ClassVar

import torch
from torch import Tensor, nn

from .base import BaseInversionAttack

logger = logging.getLogger(__name__)


class MLPDecoderNetwork(nn.Module):
    """Decode an embedding into log-probabilities over a token vocabulary."""

    def __init__(self, embedding_dim: int, vocab_size: int) -> None:
        super().__init__()
        if embedding_dim <= 0 or vocab_size <= 0:
            raise ValueError("embedding_dim and vocab_size must be greater than zero")
        self.network = nn.Sequential(
            nn.Linear(embedding_dim, 512),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, vocab_size),
            nn.LogSoftmax(dim=1),
        )

    def forward(self, embeddings: Tensor) -> Tensor:
        """Return log-probabilities for a batch of embedding vectors."""
        return self.network(embeddings)


class MLPInversionAttack(BaseInversionAttack):
    """Learn a continuous embedding-to-token decoder on a reference corpus."""

    _token_pattern: ClassVar[re.Pattern[str]] = re.compile(r"[A-Za-z0-9']+")

    def __init__(
        self,
        embedding_dim: int = 384,
        vocab_size: int = 1000,
        learning_rate: float = 1e-3,
        epochs: int = 5,
        device: str = "cpu",
    ) -> None:
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be greater than zero")
        if vocab_size <= 0:
            raise ValueError("vocab_size must be greater than zero")
        if learning_rate <= 0:
            raise ValueError("learning_rate must be greater than zero")
        if epochs <= 0:
            raise ValueError("epochs must be greater than zero")

        self.embedding_dim = embedding_dim
        self.vocab_size = vocab_size
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.device = torch.device(device)
        if self.device.type == "cpu":
            torch.set_num_threads(1)
        self.model: MLPDecoderNetwork | None = None
        self.token_to_index: dict[str, int] = {}
        self.index_to_token: list[str] = []
        self.loss_history: list[float] = []
        self.is_fitted = False

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        return cls._token_pattern.findall(text.lower()) or ["<empty>"]

    def encode_text(self, text: str) -> list[float]:
        """Create a deterministic normalized bag-of-words feature vector."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must be a non-empty string")
        vector = torch.zeros(self.embedding_dim, dtype=torch.float32)
        for token in self._tokenize(text):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            bucket = int.from_bytes(digest, byteorder="big") % self.embedding_dim
            vector[bucket] += 1.0
        norm = torch.linalg.vector_norm(vector)
        if norm > 0:
            vector /= norm
        return vector.tolist()

    def _build_vocabulary(self, reference_corpus: list[str]) -> None:
        token_counts = Counter(
            token
            for text in reference_corpus
            for token in self._tokenize(text)
        )
        vocabulary = [token for token, _ in token_counts.most_common(self.vocab_size)]
        self.index_to_token = vocabulary
        self.token_to_index = {
            token: index for index, token in enumerate(self.index_to_token)
        }

    async def fit(self, reference_corpus: list[str]) -> None:
        """Train the MLP decoder using one token target per corpus token."""
        if any(not isinstance(text, str) or not text.strip() for text in reference_corpus):
            raise ValueError("Reference corpus entries must be non-empty strings")

        self.model = None
        self.loss_history = []
        self.is_fitted = False
        if not reference_corpus:
            self.token_to_index = {}
            self.index_to_token = []
            logger.info("MLP inversion attack fitted with an empty corpus")
            return

        self._build_vocabulary(reference_corpus)
        samples: list[list[float]] = []
        labels: list[int] = []
        for text in reference_corpus:
            embedding = self.encode_text(text)
            for token in self._tokenize(text):
                token_index = self.token_to_index.get(token)
                if token_index is not None:
                    samples.append(embedding)
                    labels.append(token_index)

        if not samples:
            raise ValueError("Reference corpus produced no trainable tokens")
        self.model = MLPDecoderNetwork(
            embedding_dim=self.embedding_dim,
            vocab_size=self.vocab_size,
        ).to(self.device)
        features = torch.tensor(samples, dtype=torch.float32, device=self.device)
        targets = torch.tensor(labels, dtype=torch.long, device=self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        criterion = nn.NLLLoss()

        self.model.train()
        for epoch in range(self.epochs):
            optimizer.zero_grad()
            log_probs = self.model(features)
            loss = criterion(log_probs, targets)
            loss.backward()
            optimizer.step()
            loss_value = float(loss.detach().cpu().item())
            self.loss_history.append(loss_value)
            logger.info("MLP decoder epoch %d/%d loss=%.4f", epoch + 1, self.epochs, loss_value)
        self.model.eval()
        self.is_fitted = True

    async def invert(
        self, target_vectors: list[list[float]], top_k: int = 1
    ) -> list[list[str]]:
        """Decode each target vector into its most likely vocabulary tokens."""
        if not target_vectors:
            return []
        if top_k <= 0:
            return [[] for _ in target_vectors]
        if not self.is_fitted or self.model is None or not self.index_to_token:
            return [[] for _ in target_vectors]

        targets = torch.tensor(target_vectors, dtype=torch.float32, device=self.device)
        if targets.ndim != 2 or targets.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Target vectors must have dimension {self.embedding_dim}; "
                f"received shape {tuple(targets.shape)}"
            )

        self.model.eval()
        with torch.no_grad():
            log_probs = self.model(targets)
            top_indices = torch.topk(
                log_probs,
                k=min(top_k, len(self.index_to_token)),
                dim=1,
            ).indices.cpu().tolist()
        return [
            [self.index_to_token[index] for index in row if index < len(self.index_to_token)]
            for row in top_indices
        ]
