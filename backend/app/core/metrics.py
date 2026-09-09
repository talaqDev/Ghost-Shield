from difflib import SequenceMatcher


def rouge_l(reference: str, candidate: str) -> float:
    """Small dependency-free ROUGE-L proxy for the local MVP."""
    if not reference or not candidate:
        return 0.0
    return round(SequenceMatcher(None, reference.lower(), candidate.lower()).ratio(), 4)


def risk_band(score: float) -> str:
    if score >= 0.75:
        return "critical"
    if score >= 0.45:
        return "elevated"
    return "contained"
