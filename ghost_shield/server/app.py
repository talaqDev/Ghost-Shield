import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ghost_shield.connectors import (
    ChromaDriver,
    FAISSDriver,
    MockPineconeDriver,
    QdrantDriver,
)

from .routes import attack, audit, defense, reports

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize local driver clients and release their registry on shutdown."""
    drivers = {
        "faiss": FAISSDriver(dimension=384),
        "chroma": ChromaDriver(collection_name="ghost_shield_runtime"),
        "qdrant": QdrantDriver(collection_name="ghost_shield_runtime", dimension=384),
        "pinecone": MockPineconeDriver(latency=0.0),
    }
    for name, driver in drivers.items():
        await driver.initialize()
        logger.info("Initialized vector driver: %s", name)
    application.state.vector_drivers = drivers
    try:
        yield
    finally:
        application.state.vector_drivers.clear()
        logger.info("Released vector driver registry")


app = FastAPI(
    title="Ghost Shield API",
    description="Vector Database Privacy Audit & Security Engine",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(reports.router)


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    """Log request completion and expose elapsed processing time to clients."""
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"
    logger.info(
        "%s %s -> %s in %.3f ms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed * 1000,
    )
    return response


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ghost-shield",
        "version": "0.1.0",
        "active_db_drivers": ["faiss", "chroma", "qdrant", "pinecone"],
    }
