from fastapi.testclient import TestClient
from sentence_transformers import SentenceTransformer

from ghost_shield.server.app import app

client = TestClient(app)
model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


def test_health_reports_active_drivers() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "faiss" in response.json()["active_db_drivers"]


def test_knn_attack_endpoint() -> None:
    reference = ["patient diagnosis record", "quantum computing research"]
    target_vector = model.encode(
        [reference[0]], convert_to_numpy=True, show_progress_bar=False
    )[0].tolist()

    response = client.post(
        "/attack/knn",
        json={
            "target_vectors": [target_vector],
            "reference_corpus": reference,
            "top_k": 1,
        },
    )

    assert response.status_code == 200
    assert response.json()["candidates"] == [[reference[0]]]


def test_mlp_attack_endpoint() -> None:
    response = client.post(
        "/attack/mlp",
        json={
            "target_vectors": [[1.0, 0.0, 0.0, 0.0]],
            "reference_corpus": ["red apple", "blue sky"],
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert len(candidates) == 1
    assert all(isinstance(token, str) for token in candidates[0])


def test_dp_defense_endpoint() -> None:
    response = client.post(
        "/defense/dp",
        json={
            "documents": [
                {"id": "doc-1", "text": "secret", "vector": [1.0, 0.0, 0.0]}
            ],
            "epsilon": 1.0,
            "mechanism": "gaussian",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mechanism"] == "gaussian"
    assert payload["documents"][0]["id"] == "doc-1"
    assert len(payload["documents"][0]["vector"]) == 3


def test_audit_endpoint() -> None:
    text = "patient diagnosis record"
    vector = model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0].tolist()
    response = client.post(
        "/audit/run",
        json={
            "db_type": "faiss",
            "documents": [{"id": "audit-1", "text": text, "vector": vector}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["db_type"] == "faiss"
    assert payload["total_documents"] == 1
    assert payload["soft_delete_leakage_found"] is True
    assert payload["leakage_metrics"]["risk_level"] == "CRITICAL"
    assert len(payload["reports"]) == 2


def test_attack_validation_returns_bad_request() -> None:
    response = client.post(
        "/attack/mlp",
        json={"target_vectors": [[]], "reference_corpus": ["text"]},
    )

    assert response.status_code == 400
