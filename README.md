# Ghost Shield

Ghost Shield is a research-to-product MVP for measuring embedding inversion leakage and demonstrating an epoch key rotation defense.

## Interactive workflow

The dashboard now supports the complete local workflow:

1. Upload a UTF-8 text document (`.txt`, `.md`, `.csv`, or `.json`).
2. Generate deterministic local embeddings for its chunks.
3. Store and inspect those embeddings in the local vector store session.
4. Select and delete individual embeddings.
5. Run an inversion attack against the selected embeddings, with optional epoch rotation.
6. View the ROUGE-L leakage risk score and reconstructed output.
7. Download the full assessment as a JSON report.

The embedding function is intentionally dependency-free for the MVP. Replace `embed_text` in `backend/app/main.py` with sentence-transformers or your existing embedding pipeline when the research model is ready.

## Run locally

From any terminal directory, open two terminals and run these commands exactly:

Terminal 1, API:

```bash
cd "/Users/talak/Documents/Ghost Sheild Project/backend"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONPATH=. python -m uvicorn app.main:app --reload
```

Terminal 2, dashboard:

```bash
cd "/Users/talak/Documents/Ghost Sheild Project/frontend"
npm install
npm run dev
```

If you are already at the project root, the shorter equivalents are `cd backend` and `cd frontend`. Do not run those commands from your home directory (`~`).

The dashboard runs at `http://localhost:5173`. The backend uses an in-memory vector store and deterministic local attack simulation so the complete product workflow is runnable before loading research-specific vec2text weights. The replacement point for the attack is `backend/app/core/attack_engine.py`.

## Product shape

- `POST /experiments/run` executes an attack/defense comparison.
- `GET /experiments` lists recent runs.
- Chroma and FAISS are represented as selectable local vector-store targets in the MVP contract.
- Epoch rotation seals the reconstruction and drives leakage risk down for comparison.

See `docs/threat_model.md` for the intended security boundary.
