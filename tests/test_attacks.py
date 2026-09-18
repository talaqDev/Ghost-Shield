import pytest

from ghost_shield.attacks import KNNInversionAttack


@pytest.mark.asyncio
async def test_knn_inversion_attack() -> None:
    attack = KNNInversionAttack()
    reference_corpus = [
        "apple pie recipe",
        "quantum computing research",
        "credit card transaction details",
    ]

    await attack.fit(reference_corpus)
    target_embedding = attack.model.encode(
        ["quantum computing"],
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0].tolist()

    candidates = await attack.invert([target_embedding], top_k=1)

    assert candidates == [["quantum computing research"]]


@pytest.mark.asyncio
async def test_knn_attack_handles_empty_corpus_and_dimension_errors() -> None:
    attack = KNNInversionAttack()

    await attack.fit([])
    assert await attack.invert([[1.0, 2.0]]) == [[]]
    assert await attack.invert([]) == []

    await attack.fit(["reference text"])
    with pytest.raises(ValueError, match="Target vectors must have dimension"):
        await attack.invert([[1.0]])
