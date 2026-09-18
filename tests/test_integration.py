import time
from typing import Any
from uuid import uuid4

import pytest

from ghost_shield.attacks import KNNInversionAttack
from ghost_shield.connectors.chroma_driver import ChromaDriver
from ghost_shield.connectors.faiss_driver import FAISSDriver
from ghost_shield.connectors.schemas import Document


@pytest.mark.asyncio
async def test_end_to_end_database_audit() -> None:
    sensitive_documents = [
        "Patient record: Ada Lovelace, diagnosis: hypertension, policy ID H-1842.",
        "Financial record: account 7719 transferred 2400 dollars to beneficiary 12.",
    ]
    attack = KNNInversionAttack()
    await attack.fit(sensitive_documents)
    assert attack.model is not None

    embeddings = attack.model.encode(
        sensitive_documents,
        convert_to_numpy=True,
        show_progress_bar=False,
    ).tolist()
    documents = [
        Document(id=f"sensitive-{index}", text=text, vector=vector)
        for index, (text, vector) in enumerate(zip(sensitive_documents, embeddings))
    ]
    target = documents[0]

    faiss_driver = FAISSDriver(dimension=len(embeddings[0]))
    chroma_driver = ChromaDriver(collection_name=f"integration_{uuid4().hex}")
    await faiss_driver.initialize()
    await chroma_driver.initialize()
    await faiss_driver.insert(documents)
    await chroma_driver.insert(documents)

    benchmark_rows: list[dict[str, Any]] = []
    for name, driver in (("FAISS", faiss_driver), ("ChromaDB", chroma_driver)):
        started = time.perf_counter()
        active_results = await driver.search(target.vector or [], top_k=1)
        attack_latency_ms = (time.perf_counter() - started) * 1000
        assert active_results
        assert active_results[0].document.id == target.id
        assert active_results[0].document.vector is not None

        recovered = await attack.invert([active_results[0].document.vector], top_k=1)
        assert recovered[0][0] == target.text

        soft_report = (await driver.soft_delete([target.id]))[0]
        assert soft_report.soft_deleted is True
        soft_status = await driver.verify_deleted_status(target.id)
        assert soft_status.residual_artifacts_found is True
        visible_after_soft_delete = await driver.search(target.vector or [], top_k=2)
        assert target.id not in {
            result.document.id for result in visible_after_soft_delete
        }

        if name == "FAISS":
            retained_vector = faiss_driver.documents[target.id].vector
        else:
            retained = chroma_driver.collection.get(
                ids=[target.id], include=["embeddings"]
            )
            retained_vector = retained["embeddings"][0]
        assert retained_vector is not None
        retained_recovery = await attack.invert([list(retained_vector)], top_k=1)
        assert retained_recovery[0][0] == target.text

        purge_report = (await driver.hard_purge([target.id]))[0]
        assert purge_report.hard_purged is True
        purged_status = await driver.verify_deleted_status(target.id)
        assert purged_status.hard_purged is True
        assert purged_status.residual_artifacts_found is False
        visible_after_purge = await driver.search(target.vector or [], top_k=2)
        assert target.id not in {result.document.id for result in visible_after_purge}

        if name == "FAISS":
            assert target.id not in faiss_driver.documents
        else:
            purged = chroma_driver.collection.get(ids=[target.id], include=[])
            assert purged["ids"] == []

        benchmark_rows.append(
            {
                "database": name,
                "attack_latency_ms": attack_latency_ms,
                "soft_delete_retained_vector": "yes",
                "hard_purge_retained_vector": "no",
            }
        )

    assert {row["database"] for row in benchmark_rows} == {"FAISS", "ChromaDB"}
