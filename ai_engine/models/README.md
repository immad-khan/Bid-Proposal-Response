# Models Directory

This folder stores pre-trained ML model artifacts used by the AI engine.

## Expected Files

| File | Used By | Description |
| --- | --- | --- |
| `go_nogo_classifier.pkl` | `services/go_nogo_engine.py` | Pre-trained scikit-learn RandomForest for Go/No-Go bid decisions |

## Embedding & Cross-Encoder Models

Embedding and cross-encoder models are loaded directly by `sentence-transformers`
and cached automatically at `~/.cache/torch/sentence_transformers/`:

- **Embedding**: `BAAI/bge-small-en-v1.5` (384-dim, ~33M params)
- **Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~22M params)

These are downloaded on first use. For offline deployment, pre-download them
into this directory and set the `EMBEDDING_MODEL` environment variable to the
local path.

## Training a Go/No-Go Model

Use the `GoNoGoEngine.train_model()` API to train on historical bid data:

```python
from services.go_nogo_engine import GoNoGoEngine

engine = GoNoGoEngine(model_path="models/go_nogo_classifier.pkl")
metrics = engine.train_model([
    {"capability_score": 0.9, "budget_alignment": 0.8, ..., "label": 1},
    {"capability_score": 0.3, "budget_alignment": 0.4, ..., "label": 0},
])
print(metrics)
```
