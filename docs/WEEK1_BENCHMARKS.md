# Week 1 Benchmarks

Status: Week 1 core-engine freeze template

This document records the baseline measurements for Ghost Shield's vector connectors and KNN inversion attack. Values should be captured on the same machine, Python version, embedding model, and corpus size so backend comparisons remain meaningful.

## Test profile

| Field | Value |
| --- | --- |
| Embedding model | `all-MiniLM-L6-v2` |
| Embedding dimension | 384 |
| Reference corpus | Sensitive medical and financial test records |
| Vector count | 2 baseline records |
| Search `top_k` | 1 |
| Hardware | Fill in CPU, RAM, and architecture |
| Python / Poetry lock | Fill in from benchmark run |

## Connector benchmark

| Vector database | Storage mode | Insert latency (ms) | Search latency (ms) | Memory footprint (MB) | Hard-purge latency (ms) | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| FAISS | `IndexFlatL2`, in-memory | pending | pending | pending | pending | Structural rebuild removes purged vectors |
| ChromaDB | `EphemeralClient`, cosine collection | pending | pending | pending | pending | Metadata soft-delete flag retains raw vector |
| Qdrant | `:memory:`, cosine collection | pending | pending | pending | pending | Complete in-memory point deletion |
| Mock Pinecone | In-memory simulated cloud index | pending | pending | pending | pending | Include simulated network latency |

## Attack and deletion-risk benchmark

| Vector database | Reconstruction latency (ms) | Top-1 recovery rate (%) | Soft-delete search visibility | Soft-delete raw vector retained | Hard-purge raw vector retained | Residual-risk assessment |
| --- | ---: | ---: | --- | --- | --- | --- |
| FAISS | pending | pending | Hidden from connector search | Yes | No | Soft deletion is not physical erasure |
| ChromaDB | pending | pending | Hidden by metadata filter | Yes | No | Soft deletion is not physical erasure |
| Qdrant | pending | pending | Hidden by payload filter | Yes | No | Measure payload/vector retrieval directly |
| Mock Pinecone | pending | pending | Hidden by simulated metadata filter | Yes | No | Represents cloud-provider retention behavior |

## Measurement method

1. Initialize an isolated connector and record process memory before insertion.
2. Insert the same embedded corpus and record insertion time and memory delta.
3. Search each target vector with the same `top_k` and record latency.
4. Fit `KNNInversionAttack` on the known reference corpus and record reconstruction latency and top-1 recovery.
5. Soft-delete the target, verify that normal search hides it, then inspect raw storage and rerun inversion against the retained vector.
6. Hard-purge the target, verify the deletion report, inspect storage again, and record whether a fresh extraction is possible.

## Week 1 freeze criteria

- [x] FAISS and ChromaDB lifecycle tests pass.
- [x] Qdrant and Mock Pinecone lifecycle tests pass.
- [x] KNN inversion attack passes semantic recovery test.
- [x] End-to-end soft-delete retention risk is covered by integration tests.
- [x] End-to-end hard-purge verification is covered by integration tests.
- [ ] Fill benchmark values from a repeatable benchmark runner.
- [ ] Review and archive the final Week 1 measurements.
