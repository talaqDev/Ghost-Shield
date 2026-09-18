from uuid import uuid4

import pytest
from sentence_transformers import SentenceTransformer

from ghost_shield.attacks import KNNInversionAttack
from ghost_shield.auditors import SoftDeleteAuditor
from ghost_shield.connectors import ChromaDriver, FAISSDriver
from ghost_shield.connectors.schemas import Document


@pytest.mark.asyncio
@pytest.mark.parametrize("database_name", ["faiss", "chroma"])
async def test_soft_delete_auditor(database_name: str) -> None:
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    texts = [
        "Patient Ada diagnosis hypertension policy H-1842",
        "Account 7719 transferred 2400 dollars beneficiary 12",
    ]
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    documents = [
        Document(id=f"audit-{index}", text=text, vector=vector.tolist())
        for index, (text, vector) in enumerate(zip(texts, vectors))
    ]
    if database_name == "faiss":
        database = FAISSDriver(dimension=vectors.shape[1])
    else:
        database = ChromaDriver(collection_name=f"auditor_{uuid4().hex}")

    report = await SoftDeleteAuditor(
        database=database,
        inversion_attack=KNNInversionAttack(model=model),
    ).run_audit(documents, [documents[0].id])

    assert report.total_audited == 1
    assert report.soft_deleted_count == 1
    assert report.residual_artifacts_detected == 1
    assert report.successful_inversions == 1
    assert report.max_leakage_score > 0.75
    assert report.risk_level == "CRITICAL"
    assert report.details[0].residual_artifacts_found is True
