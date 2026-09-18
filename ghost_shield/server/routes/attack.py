"""Inversion attack API routes."""

import logging

from fastapi import APIRouter, HTTPException

from ghost_shield.attacks import KNNInversionAttack, MLPInversionAttack

from ..schemas import AttackRequest, AttackResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/attack", tags=["attacks"])


@router.post("/knn", response_model=AttackResponse)
async def run_knn_attack(request: AttackRequest) -> AttackResponse:
    """Run a KNN inversion attack against supplied target vectors."""
    try:
        attack = KNNInversionAttack()
        await attack.fit(request.reference_corpus)
        candidates = await attack.invert(request.target_vectors, request.top_k)
        return AttackResponse(candidates=candidates)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected KNN attack failure")
        raise HTTPException(status_code=500, detail="KNN attack failed") from error


@router.post("/mlp", response_model=AttackResponse)
async def run_mlp_attack(request: AttackRequest) -> AttackResponse:
    """Train and run the CPU MLP inversion attack."""
    try:
        embedding_dim = len(request.target_vectors[0])
        if embedding_dim == 0 or any(len(vector) != embedding_dim for vector in request.target_vectors):
            raise ValueError("Target vectors must have matching non-zero dimensions")
        attack = MLPInversionAttack(embedding_dim=embedding_dim)
        await attack.fit(request.reference_corpus)
        candidates = await attack.invert(request.target_vectors, request.top_k)
        return AttackResponse(candidates=candidates)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected MLP attack failure")
        raise HTTPException(status_code=500, detail="MLP attack failed") from error
