"""Differential privacy defense API routes."""

import logging

from fastapi import APIRouter, HTTPException

from ghost_shield.defenses import DPNoiseGenerator

from ..schemas import DefenseRequest, DefenseResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/defense", tags=["defenses"])


@router.post("/dp", response_model=DefenseResponse)
async def apply_dp_defense(request: DefenseRequest) -> DefenseResponse:
    """Obfuscate incoming document vectors with DP noise."""
    try:
        generator = DPNoiseGenerator(
            epsilon=request.epsilon,
            mechanism=request.mechanism,
        )
        documents = generator.obfuscate_documents(request.documents)
        return DefenseResponse(
            documents=documents,
            mechanism=request.mechanism,
            epsilon=request.epsilon,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected DP defense failure")
        raise HTTPException(status_code=500, detail="DP defense failed") from error
