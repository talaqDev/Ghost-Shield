# Ghost Shield

Ghost Shield is a research-to-product MVP for measuring embedding inversion leakage and demonstrating an epoch key rotation defense.

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

The dashboard runs at `http://localhost:5173`. The backend currently uses an in-memory experiment store and a deterministic local attack simulation so the product shell is runnable before loading research-specific vec2text weights. The replacement point is `backend/app/core/attack_engine.py`.

## Product shape

- `POST /experiments/run` executes an attack/defense comparison.
- `GET /experiments` lists recent runs.
- Chroma and FAISS are represented as selectable local vector-store targets in the MVP contract.
- Epoch rotation seals the reconstruction and drives leakage risk down for comparison.

See `docs/threat_model.md` for the intended security boundary.
