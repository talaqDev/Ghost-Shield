from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import attack, audit, defense

app = FastAPI(
    title="Ghost Shield API",
    description="Vector Database Privacy Audit & Security Engine",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit.router)
app.include_router(attack.router)
app.include_router(defense.router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ghost-shield",
        "version": "0.1.0",
        "active_db_drivers": ["faiss", "chroma", "qdrant", "pinecone"],
    }
