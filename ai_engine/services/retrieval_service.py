import logging
from typing import List, Dict, Any, Optional
from services.vector_store import VectorStore
from services.bm25_index import BM25Index
from services.reranker import Reranker

logger = logging.getLogger(__name__)

class RetrievalService:
    """
    Orchestrates Hybrid Search by executing:
      1. Semantic query via VectorStore (ChromaDB)
      2. Keyword query via BM25Index (or Elasticsearch)
      3. Reciprocal Rank Fusion (RRF) to merge ranks
      4. Reranker (Cross-Encoder) validation to get top results
    """
    def __init__(self, vector_store: VectorStore, bm25_index: BM25Index, reranker: Reranker):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.reranker = reranker

    def reciprocal_rank_fusion(self, vector_results: List[Dict[str, Any]], bm25_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        """
        Calculates RRF score for documents found across multiple search types.
        Score = Sum(1 / (k + rank))
        """
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

    def retrieve(self, query: str, collection_name: str = "rfp_chunks", top_n: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"RetrievalService: Performing hybrid retrieval for: '{query}'")
        
        # 1. Semantic Search
        vector_docs = self.vector_store.query(collection_name, query, n_results=10)
        
        # 2. Keyword Search
        bm25_docs = self.bm25_index.search(query, top_n=10)
        
        # 3. Reciprocal Rank Fusion (RRF)
        fused_docs = self.reciprocal_rank_fusion(vector_docs, bm25_docs)
        
        # 4. Rerank
        reranked_docs = self.reranker.rerank(query, fused_docs, top_n=top_n)
        
        return reranked_docs
