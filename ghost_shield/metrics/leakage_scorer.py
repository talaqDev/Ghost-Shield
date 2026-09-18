"""Privacy leakage scoring using semantic and lexical similarity metrics."""

import logging
from typing import Any

import nltk
import numpy as np
from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer

from .schemas import LeakageScoreResult

logger = logging.getLogger(__name__)


class LeakageScorer:
    """Calculate a normalized privacy leakage score for reconstructed text."""

    def __init__(
        self,
        embedding_model: Any | None = None,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.embedding_model = embedding_model
        self.model_name = model_name
        self._rouge_scorer = rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"], use_stemmer=True
        )
        self._ensure_nltk_data()

    @staticmethod
    def _ensure_nltk_data() -> None:
        """Ensure tokenizers exist, falling back to whitespace tokenization if offline."""
        for resource, package in (
            ("tokenizers/punkt", "punkt"),
            ("tokenizers/punkt_tab", "punkt_tab"),
        ):
            try:
                nltk.data.find(resource)
            except LookupError:
                try:
                    nltk.download(package, quiet=True)
                except Exception:
                    logger.warning("Unable to download NLTK resource %s", package)

    @staticmethod
    def _tokens(text: str) -> list[str]:
        if not text.strip():
            return []
        try:
            return nltk.word_tokenize(text.lower())
        except LookupError:
            return text.lower().split()

    def _get_embedding_model(self) -> Any:
        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer(
                    self.model_name, device="cpu"
                )
            except Exception as error:
                logger.exception("Unable to initialize leakage embedding model")
                raise RuntimeError(
                    f"Unable to initialize embedding model {self.model_name!r}"
                ) from error
        return self.embedding_model

    def _cosine_similarity(self, original_text: str, reconstructed_text: str) -> float:
        if not original_text.strip() or not reconstructed_text.strip():
            return 0.0
        model = self._get_embedding_model()
        try:
            embeddings = model.encode(
                [original_text, reconstructed_text],
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as error:
            logger.exception("Failed to encode texts for cosine similarity")
            raise RuntimeError("Unable to compute semantic text embeddings") from error
        vectors = np.asarray(embeddings, dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] != 2:
            raise ValueError("Embedding model returned an invalid shape")
        norms = np.linalg.norm(vectors, axis=1)
        if np.any(norms == 0):
            return 0.0
        score = float(np.dot(vectors[0], vectors[1]) / (norms[0] * norms[1]))
        return float(np.clip(score, 0.0, 1.0))

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 0.75:
            return "CRITICAL"
        if score >= 0.50:
            return "HIGH"
        if score >= 0.25:
            return "MEDIUM"
        return "LOW"

    def compute_score(
        self,
        original_text: str,
        reconstructed_text: str,
        embedding_model: Any | None = None,
    ) -> LeakageScoreResult:
        """Compute semantic, BLEU, ROUGE, and weighted leakage metrics."""
        if not isinstance(original_text, str) or not isinstance(reconstructed_text, str):
            raise TypeError("original_text and reconstructed_text must be strings")

        if embedding_model is not None:
            previous_model = self.embedding_model
            self.embedding_model = embedding_model
        else:
            previous_model = None

        try:
            reference_tokens = self._tokens(original_text)
            candidate_tokens = self._tokens(reconstructed_text)
            if not reference_tokens or not candidate_tokens:
                cosine = bleu = rouge_1 = rouge_2 = rouge_l = 0.0
            else:
                cosine = self._cosine_similarity(original_text, reconstructed_text)
                bleu = float(
                    sentence_bleu(
                        [reference_tokens],
                        candidate_tokens,
                        weights=(0.25, 0.25, 0.25, 0.25),
                        smoothing_function=SmoothingFunction().method1,
                    )
                )
                rouge_scores = self._rouge_scorer.score(
                    original_text, reconstructed_text
                )
                rouge_1 = float(rouge_scores["rouge1"].fmeasure)
                rouge_2 = float(rouge_scores["rouge2"].fmeasure)
                rouge_l = float(rouge_scores["rougeL"].fmeasure)

            overall = float(np.clip(0.3 * cosine + 0.3 * bleu + 0.4 * rouge_l, 0.0, 1.0))
            return LeakageScoreResult(
                original_text=original_text,
                reconstructed_text=reconstructed_text,
                cosine_similarity=cosine,
                bleu_score=bleu,
                rouge_1=rouge_1,
                rouge_2=rouge_2,
                rouge_l=rouge_l,
                overall_leakage_score=overall,
                risk_level=self._risk_level(overall),
            )
        finally:
            if embedding_model is not None:
                self.embedding_model = previous_model
