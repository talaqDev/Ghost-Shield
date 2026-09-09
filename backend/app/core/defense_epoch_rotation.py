import hashlib


def rotate_epoch_key(text: str, epoch: int) -> str:
    """Represent an epoch-scoped key without exposing cryptographic material."""
    digest = hashlib.sha256(f"ghost-shield:{epoch}:{text}".encode()).hexdigest()
    return digest[:16]


def defended_reconstruction(text: str, epoch: int) -> str:
    """Deterministic local stand-in for the epoch rotation defense."""
    return f"epoch-{epoch}-sealed-{rotate_epoch_key(text, epoch)}"
