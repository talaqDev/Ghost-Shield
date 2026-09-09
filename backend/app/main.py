from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .core.attack_engine import run_inversion_attack

app = FastAPI(title="Ghost Shield API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

experiments: list[dict] = []


class ExperimentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    vector_store: str = Field(default="chroma", pattern="^(chroma|faiss)$")
    defense_enabled: bool = False
    epoch: int = Field(default=1, ge=1, le=1000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ghost-shield-api"}


@app.get("/experiments")
def list_experiments() -> list[dict]:
    return experiments


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict:
    return next((item for item in experiments if item["id"] == experiment_id), {"detail": "Not found"})


@app.post("/experiments/run")
def run_experiment(request: ExperimentRequest) -> dict:
    result = run_inversion_attack(request.text, request.defense_enabled, request.epoch)
    experiment = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "vector_store": request.vector_store,
        "input_preview": request.text[:80],
        **result.__dict__,
    }
    experiments.insert(0, experiment)
    return experiment
