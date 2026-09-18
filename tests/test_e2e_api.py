import httpx
import pytest
from sentence_transformers import SentenceTransformer

from ghost_shield.auditors.schemas import SoftDeleteAuditReport
from ghost_shield.server.app import app


@pytest.mark.asyncio
@pytest.mark.parametrize("db_type", ["faiss", "chroma"])
async def test_complete_api_workflow(db_type: str) -> None:
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    texts = ["patient diagnosis record", "financial account transaction"]
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False).tolist()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport, base_url="http://ghost-shield.test"
    ) as client:
        audit = await client.post(
            "/audit/run",
            json={
                "db_type": db_type,
                "documents": [
                    {"id": f"e2e-{index}", "text": text, "vector": vector}
                    for index, (text, vector) in enumerate(zip(texts, vectors))
                ],
            },
        )
        assert audit.status_code == 200
        assert audit.headers["x-process-time"]
        audit_payload = audit.json()
        assert audit_payload["db_type"] == db_type
        assert audit_payload["soft_delete_leakage_found"] is True
        report_payload = SoftDeleteAuditReport(
            total_audited=audit_payload["total_documents"],
            soft_deleted_count=sum(
                detail["soft_deleted"] for detail in audit_payload["reports"]
            ),
            residual_artifacts_detected=sum(
                detail["residual_artifacts_found"]
                for detail in audit_payload["reports"]
            ),
            successful_inversions=1 if audit_payload["leakage_metrics"] else 0,
            max_leakage_score=audit_payload["inversion_vulnerability_score"],
            risk_level=audit_payload["risk_level"],
            details=audit_payload["reports"],
        ).model_dump()

        attack = await client.post(
            "/attack/knn",
            json={
                "target_vectors": [vectors[0]],
                "reference_corpus": texts,
                "top_k": 1,
            },
        )
        assert attack.status_code == 200
        assert attack.json()["candidates"][0][0] == texts[0]

        defense = await client.post(
            "/defense/dp",
            json={
                "documents": [
                    {"id": "e2e-defense", "text": texts[0], "vector": vectors[0]}
                ],
                "epsilon": 1.0,
            },
        )
        assert defense.status_code == 200
        obfuscated = defense.json()["documents"][0]["vector"]
        assert len(obfuscated) == len(vectors[0])
        assert obfuscated != vectors[0]

        for report_format in ("json", "pdf"):
            report = await client.post(
                "/reports/export",
                json={"audit_report": report_payload, "format": report_format},
            )
            assert report.status_code == 200
            assert "attachment" in report.headers["content-disposition"]
            assert report.content
