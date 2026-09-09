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
