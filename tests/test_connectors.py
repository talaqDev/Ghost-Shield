from uuid import uuid4

import pytest

from ghost_shield.connectors.chroma_driver import ChromaDriver
from ghost_shield.connectors.faiss_driver import FAISSDriver
from ghost_shield.connectors.mock_pinecone_driver import MockPineconeDriver
from ghost_shield.connectors.qdrant_driver import QdrantDriver
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


@pytest.mark.asyncio
async def test_qdrant_driver_lifecycle() -> None:
    driver = QdrantDriver(collection_name=f"test_{uuid4().hex}", dimension=3)
    await driver.initialize()
    documents = [
        Document(id="qdrant_1", text="Hello Qdrant", vector=[0.1, 0.2, 0.3]),
        Document(id="qdrant_2", text="Bye Qdrant", vector=[0.8, 0.9, 1.0]),
    ]

    assert await driver.insert(documents) == ["qdrant_1", "qdrant_2"]
    results = await driver.search([0.1, 0.2, 0.3], top_k=2)
    assert len(results) == 2
    assert results[0].document.id == "qdrant_1"

    soft_reports = await driver.soft_delete(["qdrant_1"])
    assert soft_reports[0].soft_deleted is True
    verification = await driver.verify_deleted_status("qdrant_1")
    assert verification.soft_deleted is True
    assert verification.residual_artifacts_found is True
    results_after_soft_delete = await driver.search([0.1, 0.2, 0.3], top_k=2)
    assert [result.document.id for result in results_after_soft_delete] == ["qdrant_2"]

    purge_reports = await driver.hard_purge(["qdrant_1"])
    assert purge_reports[0].hard_purged is True
    verification = await driver.verify_deleted_status("qdrant_1")
    assert verification.hard_purged is True
    assert verification.residual_artifacts_found is False


@pytest.mark.asyncio
async def test_mock_pinecone_lifecycle() -> None:
    driver = MockPineconeDriver(latency=0.01)
    await driver.initialize()
    document = Document(id="pinecone_1", text="Cloud record", vector=[1.0, 0.0, 0.0])

    assert await driver.insert([document]) == ["pinecone_1"]
    results = await driver.search([1.0, 0.0, 0.0])
    assert len(results) == 1
    assert results[0].document.id == "pinecone_1"

    soft_reports = await driver.soft_delete(["pinecone_1"])
    assert soft_reports[0].soft_deleted is True
    assert await driver.search([1.0, 0.0, 0.0]) == []
    verification = await driver.verify_deleted_status("pinecone_1")
    assert verification.soft_deleted is True
    assert verification.residual_artifacts_found is True

    purge_reports = await driver.hard_purge(["pinecone_1"])
    assert purge_reports[0].hard_purged is True
    verification = await driver.verify_deleted_status("pinecone_1")
    assert verification.hard_purged is True
    assert verification.residual_artifacts_found is False
