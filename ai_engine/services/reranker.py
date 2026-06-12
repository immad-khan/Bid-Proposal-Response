"""
Reranker — Cross-encoder reranking service using sentence-transformers.
Takes candidate documents from the RRF fusion stage and reorders them
by true query-document relevance using a trained cross-encoder model.
"""

import logging
from typing import List, Dict, Any

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class Reranker:
    """
    Reranker service using a Cross-Encoder model to re-evaluate
    and re-rank the hybrid query results with high-precision relevance scoring.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        logger.info(f"Reranker: Loading cross-encoder model '{self.model_name}'...")
        self.model = CrossEncoder(self.model_name, max_length=512)
        logger.info(f"Reranker: Model loaded successfully.")

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 5,
        text_key: str = "original_text",
    ) -> List[Dict[str, Any]]:
        """
        Rerank a set of retrieved documents based on semantic relevance to the query.

        Args:
            query: The search query.
            documents: List of candidate document dicts from the RRF stage.
            top_n: Number of top results to return after reranking.
            text_key: Key in each doc dict containing the text to score against.

        Returns:
            Top-N documents sorted by descending cross-encoder relevance score,
            each augmented with a 'rerank_score' key.
        """
        if not documents:
            return []

        logger.info(f"Reranker: Re-ranking {len(documents)} documents for query: '{query[:80]}...'")

        # Build (query, document_text) pairs for the cross-encoder
        pairs = []
        for doc in documents:
            doc_text = doc.get(text_key, doc.get("text", ""))
            pairs.append([query, doc_text])

        # Score all pairs in a single batch
        scores = self.model.predict(pairs)

        # Attach scores and sort
        for idx, score in enumerate(scores):
            documents[idx]["rerank_score"] = float(score)

        documents.sort(key=lambda x: x["rerank_score"], reverse=True)

        top_results = documents[:top_n]
        logger.info(
            f"Reranker: Top result score={top_results[0]['rerank_score']:.4f}, "
            f"Lowest returned={top_results[-1]['rerank_score']:.4f}"
            if top_results else "Reranker: No results."
        )
        return top_results
