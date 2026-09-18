import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
documents: list[dict] = []
vectors: list[dict] = []


class ExperimentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    vector_store: str = Field(default="chroma", pattern="^(chroma|faiss)$")
    defense_enabled: bool = False
    epoch: int = Field(default=1, ge=1, le=1000)


class AttackRequest(BaseModel):
    vector_ids: list[str] = Field(default_factory=list)
    defense_enabled: bool = True
    epoch: int = Field(default=1, ge=1, le=1000)


def embed_text(text: str) -> list[float]:
    """Generate a deterministic local embedding until a real model is configured."""
    digest = hashlib.sha256(text.encode()).digest()
    return [round((value / 255) * 2 - 1, 4) for value in digest[:8]]


def chunk_text(text: str, size: int = 420) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for word in words:
        if current and current_size + len(word) + 1 > size:
            chunks.append(" ".join(current))
            current = []
            current_size = 0
        current.append(word)
        current_size += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks or [text]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ghost-shield-api", "documents": len(documents), "vectors": len(vectors)}


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="Upload a UTF-8 text document for this MVP.") from error
    if not text.strip():
        raise HTTPException(status_code=400, detail="The document is empty.")

    document_id = str(uuid4())
    chunks = chunk_text(text)
    created_vectors = []
    for index, chunk in enumerate(chunks):
        record = {
            "id": str(uuid4()),
            "document_id": document_id,
            "document_name": file.filename,
            "chunk_index": index,
            "text": chunk,
            "embedding": embed_text(chunk),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        vectors.append(record)
        created_vectors.append(record)
    document = {
        "id": document_id,
        "name": file.filename,
        "size": len(content),
        "chunk_count": len(created_vectors),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    documents.insert(0, document)
    return {"document": document, "vectors": created_vectors}


@app.get("/documents")
def list_documents() -> list[dict]:
    return documents


@app.get("/vectors")
def list_vectors() -> list[dict]:
    return vectors


@app.delete("/vectors/{vector_id}")
def delete_vector(vector_id: str) -> dict:
    global vectors
    before = len(vectors)
    vectors = [vector for vector in vectors if vector["id"] != vector_id]
    if len(vectors) == before:
        raise HTTPException(status_code=404, detail="Vector not found.")
    return {"deleted": vector_id, "remaining": len(vectors)}


@app.delete("/documents/{document_id}")
def delete_document(document_id: str) -> dict:
    global documents, vectors
    if not any(document["id"] == document_id for document in documents):
        raise HTTPException(status_code=404, detail="Document not found.")
    documents = [document for document in documents if document["id"] != document_id]
    vectors = [vector for vector in vectors if vector["document_id"] != document_id]
    return {"deleted": document_id, "remaining_vectors": len(vectors)}


@app.post("/attacks/run")
def run_attack(request: AttackRequest) -> dict:
    selected = [vector for vector in vectors if not request.vector_ids or vector["id"] in request.vector_ids]
    if not selected:
        raise HTTPException(status_code=400, detail="Upload and select at least one embedding first.")
    source_text = " ".join(vector["text"] for vector in selected)
    result = run_inversion_attack(source_text, request.defense_enabled, request.epoch)
    attack = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "vector_ids": [vector["id"] for vector in selected],
        "vector_count": len(selected),
        "document_names": sorted({vector["document_name"] for vector in selected}),
        **result.__dict__,
    }
    experiments.insert(0, attack)
    return attack


@app.get("/reports/{experiment_id}/download")
def download_report(experiment_id: str) -> Response:
    experiment = next((item for item in experiments if item["id"] == experiment_id), None)
    if not experiment:
        raise HTTPException(status_code=404, detail="Attack report not found.")
    payload = json.dumps({"report": "Ghost Shield leakage assessment", "experiment": experiment}, indent=2)
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="ghost-shield-{experiment_id}.json"'},
    )


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
