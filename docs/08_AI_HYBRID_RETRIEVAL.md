# File: `ai_engine/services/retrieval_service.py` — Hybrid Search & RRF Orchestration

This service merges semantic vector search results with keyword matching to provide context for the proposal generation agents.

---

## 🛠️ 1. Architecture Overview

The `RetrievalService` integrates three search modules:
- **`VectorStore` (Qdrant)**: Performs semantic search using dense vector embeddings.
- **`BM25Index`**: Performs keyword search using sparse token frequencies.
- **`Reranker` (Cross-Encoder)**: Reranks the fused results to measure relevancy.

```python
class RetrievalService:
    def __init__(self, vector_store: VectorStore, bm25_index: BM25Index, reranker: Reranker):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.reranker = reranker
```

---

## 🔀 2. Reciprocal Rank Fusion (RRF)

To combine results from vector search and BM25 search, the service implements the **Reciprocal Rank Fusion (RRF)** algorithm. RRF scores documents based on their rank in each individual search result, reducing the impact of outliers.

### Mathematical Formula:
$$RRF\_Score(d \in D) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

- **$M$**: The set of search channels (dense vector search and sparse keyword search).
- **$r_m(d)$**: The 1-based rank position of document $d$ in search channel $m$.
- **$k$**: A constant parameter (default is `60`) that controls the influence of low-ranked documents.

### Code Implementation:
```python
def reciprocal_rank_fusion(self, vector_results: List[Dict[str, Any]], bm25_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}
    
    # Process vector search results
    for rank, doc in enumerate(vector_results):
        doc_id = doc["id"]
        doc_map[doc_id] = doc
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        
    # Process BM25 search results
    for rank, doc in enumerate(bm25_results):
        doc_id = doc["id"]
        if doc_id not in doc_map:
            doc_map[doc_id] = doc
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        
    # Sort documents by RRF score
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    
    fused_docs = []
    for doc_id in sorted_ids:
        doc = doc_map[doc_id]
        doc["rrf_score"] = rrf_scores[doc_id]
        fused_docs.append(doc)
        
    return fused_docs
```

---

## 🔍 3. Retrieval Pipeline Execution

The `retrieve(query, collection_name, top_n)` method executes the search pipeline:

```python
def retrieve(self, query: str, collection_name: str = "rfp_chunks", top_n: int = 5) -> List[Dict[str, Any]]:
    # 1. Semantic Search
    vector_docs = self.vector_store.query(collection_name, query, n_results=10)
    
    # 2. Keyword Search
    bm25_docs = self.bm25_index.search(query, top_n=10)
    
    # 3. Reciprocal Rank Fusion (RRF)
    fused_docs = self.reciprocal_rank_fusion(vector_docs, bm25_docs)
    
    # 4. Reranking
    reranked_docs = self.reranker.rerank(query, fused_docs, top_n=top_n)
    
    return reranked_docs
```

### Pipeline Steps:
1. **Semantic Search:** Retrieves the top 10 items from Qdrant using dense vector embeddings.
2. **Keyword Search:** Retrieves the top 10 items from the BM25 index.
3. **RRF Fusion:** Combines both lists, calculating RRF scores and sorting documents by relevancy.
4. **Cross-Encoder Reranking:** Evaluates the query-chunk pairs using a reranker model to select the final `top_n` results.
