# Threat Model

Ghost Shield models an attacker who obtains vector representations and attempts to reconstruct source text through an inversion model.

## Assets

- Source text and PII embedded into a vector store.
- Experiment metadata and comparative leakage scores.

## Attacker capabilities

- Read access to stored vectors.
- Knowledge of the embedding model family.
- Ability to run repeated reconstruction attempts across epochs.

## Defense claim

Epoch-scoped rotation makes a captured representation stale across epochs. The MVP visualizes the resulting drop in ROUGE-L similarity; production validation must use the existing vec2text pipeline and research datasets.
