# Ghost Shield API

Base URL: `http://localhost:8000`

The API is designed for the Week 3 React dashboard. All route handlers return JSON except report downloads. Every response includes `X-Process-Time`, measured in seconds.

## Health

### `GET /health`

Returns service readiness and registered vector drivers.

```json
{
  "status": "healthy",
  "service": "ghost-shield",
  "version": "0.1.0",
  "active_db_drivers": ["faiss", "chroma", "qdrant", "pinecone"]
}
```

## Audit

### `POST /audit/run`

Runs insertion, KNN inversion, leakage scoring, soft deletion, and residual storage verification.

Request:

```json
{
  "db_type": "faiss",
  "documents": [
    {
      "id": "patient-1",
      "text": "Patient diagnosis record",
      "metadata": {"source": "demo"},
      "vector": [0.1, 0.2, 0.3]
    }
  ],
  "epsilon": null
}
```

`db_type` accepts `faiss`, `chroma`, `qdrant`, or `pinecone` (the local Mock Pinecone driver). `epsilon`, when provided, applies Gaussian DP obfuscation before insertion.

Response fields include `total_documents`, `soft_delete_leakage_found`, `inversion_vulnerability_score`, `risk_level`, deletion `reports`, and nested `leakage_metrics`.

## Attacks

### `POST /attack/knn`

Runs the Sentence-Transformers plus FAISS nearest-neighbor inversion attack.

```json
{
  "target_vectors": [[0.1, 0.2, 0.3]],
  "reference_corpus": ["patient diagnosis record", "financial account"],
  "top_k": 1
}
```

Response:

```json
{"candidates": [["patient diagnosis record"]]}
```

### `POST /attack/mlp`

Trains the CPU MLP decoder on `reference_corpus` and returns token candidates for each target vector. Target vectors in one request must have the same non-zero dimension.

## Defense

### `POST /defense/dp`

Applies DP noise and unit-L2 normalization to document vectors without mutating the request payload.

```json
{
  "documents": [{"id": "doc-1", "text": "secret", "vector": [1.0, 0.0, 0.0]}],
  "epsilon": 1.0,
  "mechanism": "gaussian"
}
```

`mechanism` accepts `gaussian` or `laplacian`.

## Reports

### `POST /reports/export`

Returns a downloadable machine-readable JSON report or a human-readable PDF. When ReportLab is unavailable, the `pdf` request returns a styled HTML attachment instead.

```json
{
  "audit_report": {
    "total_audited": 1,
    "soft_deleted_count": 1,
    "residual_artifacts_detected": 1,
    "successful_inversions": 1,
    "max_leakage_score": 0.82,
    "risk_level": "CRITICAL",
    "details": []
  },
  "format": "json"
}
```

The response uses `Content-Disposition: attachment` and a generated filename.

## Error responses

- `400 Bad Request`: invalid vectors, unsupported values, missing embeddings, or attack/defense validation failures.
- `422 Unprocessable Entity`: malformed request schema rejected by Pydantic.
- `500 Internal Server Error`: unexpected route or engine failure.

## Local execution

```bash
poetry run uvicorn ghost_shield.server.app:app --reload
```
