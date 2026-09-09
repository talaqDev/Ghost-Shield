from dataclasses import dataclass

from .defense_epoch_rotation import defended_reconstruction
from .metrics import rouge_l, risk_band


@dataclass
class AttackResult:
    original: str
    reconstruction: str
    rouge_l: float
    risk: str
    defense_enabled: bool
    epoch: int


def run_inversion_attack(text: str, defense_enabled: bool = False, epoch: int = 1) -> AttackResult:
    """Run a safe local simulation; replace the reconstruction body with vec2text in production."""
    reconstruction = defended_reconstruction(text, epoch) if defense_enabled else text
    score = rouge_l(text, reconstruction)
    return AttackResult(
        original=text,
        reconstruction=reconstruction,
        rouge_l=score,
        risk=risk_band(score),
        defense_enabled=defense_enabled,
        epoch=epoch,
    )
