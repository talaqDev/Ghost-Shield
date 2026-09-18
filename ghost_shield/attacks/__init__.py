"""Embedding inversion attack implementations."""

from .base import BaseInversionAttack
from .knn_attack import KNNInversionAttack

__all__ = ["BaseInversionAttack", "KNNInversionAttack"]
