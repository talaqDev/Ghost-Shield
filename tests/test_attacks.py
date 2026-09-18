import pytest

from ghost_shield.attacks import KNNInversionAttack, MLPInversionAttack


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


@pytest.mark.asyncio
async def test_mlp_inversion_attack() -> None:
    attack = MLPInversionAttack(embedding_dim=16, vocab_size=32, epochs=2)
    await attack.fit(["red apple", "blue sky", "green garden"])

    candidates = await attack.invert([attack.encode_text("red apple")], top_k=2)

    assert len(candidates) == 1
    assert len(candidates[0]) == 2
    assert all(isinstance(token, str) for token in candidates[0])
    assert attack.model is not None
    assert attack.model.training is False
