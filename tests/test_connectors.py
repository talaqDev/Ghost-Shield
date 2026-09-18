from uuid import uuid4

import pytest

from ghost_shield.connectors.chroma_driver import ChromaDriver
from ghost_shield.connectors.faiss_driver import FAISSDriver
from ghost_shield.connectors.schemas import Document


@pytest.mark.asyncio
async def test_faiss_driver_lifecycle() -> None:
    driver = FAISSDriver(dimension=3)
    await driver.initialize()
    documents = [
        Document(id="doc_1", text="Alpha", vector=[1.0, 0.0, 0.0]),
        Document(id="doc_2", text="Beta", vector=[0.0, 1.0, 0.0]),
    ]

    assert await driver.insert(documents) == ["doc_1", "doc_2"]
    results = await driver.search([1.0, 0.0, 0.0], top_k=2)
    assert [result.document.id for result in results] == ["doc_1", "doc_2"]

    soft_reports = await driver.soft_delete(["doc_1"])
    assert soft_reports[0].soft_deleted is True
    assert soft_reports[0].residual_artifacts_found is True
    verification = await driver.verify_deleted_status("doc_1")
    assert verification.soft_deleted is True
    assert verification.residual_artifacts_found is True
    assert len(await driver.search([1.0, 0.0, 0.0], top_k=2)) == 1

    purge_reports = await driver.hard_purge(["doc_1"])
    assert purge_reports[0].hard_purged is True
    verification = await driver.verify_deleted_status("doc_1")
    assert verification.hard_purged is True
    assert verification.residual_artifacts_found is False


@pytest.mark.asyncio
async def test_chroma_driver_lifecycle() -> None:
    driver = ChromaDriver(collection_name=f"test_{uuid4().hex}")
    await driver.initialize()
    documents = [
        Document(id="chroma_1", text="Hello", vector=[0.1, 0.2, 0.3]),
        Document(id="chroma_2", text="World", vector=[0.4, 0.5, 0.6]),
    ]

    assert await driver.insert(documents) == ["chroma_1", "chroma_2"]
    results = await driver.search([0.1, 0.2, 0.3], top_k=2)
    assert len(results) == 2
    assert results[0].document.id == "chroma_1"

    soft_reports = await driver.soft_delete(["chroma_1"])
    assert soft_reports[0].soft_deleted is True
    verification = await driver.verify_deleted_status("chroma_1")
    assert verification.soft_deleted is True
    assert verification.residual_artifacts_found is True
    results_after_soft_delete = await driver.search([0.1, 0.2, 0.3], top_k=2)
    assert [result.document.id for result in results_after_soft_delete] == ["chroma_2"]

    purge_reports = await driver.hard_purge(["chroma_1"])
    assert purge_reports[0].hard_purged is True
    verification = await driver.verify_deleted_status("chroma_1")
    assert verification.hard_purged is True
    assert verification.residual_artifacts_found is False
