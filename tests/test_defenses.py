import numpy as np
import pytest

from ghost_shield.attacks import KNNInversionAttack
from ghost_shield.connectors.schemas import Document
from ghost_shield.defenses import DPNoiseGenerator
from ghost_shield.metrics import LeakageScorer


def test_gaussian_noise_changes_and_normalizes_vectors() -> None:
    raw_vector = np.array([1.0, 0.0, 0.0])
    np.random.seed(7)
    obfuscated = DPNoiseGenerator(epsilon=1.0).apply_noise(raw_vector)

    assert np.linalg.norm(np.asarray(obfuscated) - raw_vector) > 0
    assert np.isclose(np.linalg.norm(obfuscated), 1.0)


def test_laplacian_noise_supports_python_lists() -> None:
    np.random.seed(7)
    obfuscated = DPNoiseGenerator(
        epsilon=1.0, mechanism="laplacian"
    ).apply_noise([1.0, 2.0, 3.0])

    assert isinstance(obfuscated, list)
    assert np.isclose(np.linalg.norm(obfuscated), 1.0)


def test_lower_epsilon_produces_larger_perturbation() -> None:
    raw_vector = np.ones(32, dtype=np.float64)
    np.random.seed(11)
    high_epsilon = np.asarray(
        DPNoiseGenerator(epsilon=10.0).apply_noise(raw_vector)
    )
    np.random.seed(11)
    low_epsilon = np.asarray(
        DPNoiseGenerator(epsilon=0.1).apply_noise(raw_vector)
    )

    high_perturbation = np.linalg.norm(high_epsilon - raw_vector / np.linalg.norm(raw_vector))
    low_perturbation = np.linalg.norm(low_epsilon - raw_vector / np.linalg.norm(raw_vector))
    assert low_perturbation > high_perturbation


def test_obfuscate_documents_does_not_mutate_input() -> None:
    document = Document(id="doc-1", text="secret", vector=[1.0, 0.0, 0.0])
    np.random.seed(3)
    obfuscated = DPNoiseGenerator(epsilon=1.0).obfuscate_documents([document])

    assert obfuscated[0] is not document
    assert document.vector == [1.0, 0.0, 0.0]
    assert obfuscated[0].vector != document.vector


@pytest.mark.asyncio
async def test_dp_noise_reduces_knn_leakage_metrics() -> None:
    reference = [
        "patient diagnosis hypertension medication",
        "quantum computing research laboratory",
        "credit card transaction account",
    ]
    attack = KNNInversionAttack()
    await attack.fit(reference)
    assert attack.model is not None
    raw_vector = attack.model.encode(
        [reference[0]], convert_to_numpy=True, show_progress_bar=False
    )[0].tolist()

    raw_candidate = (await attack.invert([raw_vector], top_k=1))[0][0]
    np.random.seed(19)
    noisy_vector = DPNoiseGenerator(epsilon=0.05).apply_noise(raw_vector)
    noisy_candidate = (await attack.invert([noisy_vector], top_k=1))[0][0]

    scorer = LeakageScorer(embedding_model=attack.model)
    raw_score = scorer.compute_score(reference[0], raw_candidate)
    noisy_score = scorer.compute_score(reference[0], noisy_candidate)

    assert raw_score.cosine_similarity >= noisy_score.cosine_similarity
    assert raw_score.bleu_score >= noisy_score.bleu_score
    assert raw_score.overall_leakage_score > noisy_score.overall_leakage_score
