from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_defense_lowers_leakage_score() -> None:
    response = client.post("/experiments/run", json={"text": "patient email is ada@example.com"})
    defended = client.post(
        "/experiments/run",
        json={"text": "patient email is ada@example.com", "defense_enabled": True},
    )
    assert response.status_code == 200
    assert defended.json()["rouge_l"] < response.json()["rouge_l"]


def test_document_to_attack_and_report_flow() -> None:
    upload = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"A private customer record with an email address.", "text/plain")},
    )
    assert upload.status_code == 200
    uploaded = upload.json()
    assert uploaded["document"]["chunk_count"] == 1
    vector_id = uploaded["vectors"][0]["id"]

    attack = client.post("/attacks/run", json={"vector_ids": [vector_id], "defense_enabled": True})
    assert attack.status_code == 200
    experiment_id = attack.json()["id"]
    assert attack.json()["vector_count"] == 1

    report = client.get(f"/reports/{experiment_id}/download")
    assert report.status_code == 200
    assert "attachment" in report.headers["content-disposition"]
    assert "Ghost Shield leakage assessment" in report.json()["report"]

    deletion = client.delete(f"/vectors/{vector_id}")
    assert deletion.status_code == 200
