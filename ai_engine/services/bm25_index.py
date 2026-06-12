"""
BM25 Index — Keyword-based search using rank_bm25 (BM25Okapi).
Provides an in-memory inverted index over tokenized document text
for the keyword retrieval leg of the hybrid search pipeline.
"""

import logging
import re
from typing import List, Dict, Any

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> List[str]:
    """
    Simple whitespace + punctuation tokenizer.
    Lowercases and strips non-alphanumeric characters.
    """
    return re.findall(r"\w+", text.lower())


class BM25Index:
    """
    BM25 Wrapper for keyword-based search over proposal and RFP chunks.
    Uses rank_bm25.BM25Okapi for proper TF-IDF-style BM25 scoring.
    """

    def __init__(self):
        self.corpus_tokens: List[List[str]] = []
        self.documents: List[Dict[str, Any]] = []
        self.bm25: BM25Okapi | None = None

    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Build the BM25 inverted index from a list of document dicts.
        Each document should have 'text_for_embedding' or 'original_text'.

        Args:
            documents: List of chunk dicts from chunking_service.prepare_for_vector_db().
        """
        logger.info(f"BM25Index: Indexing {len(documents)} documents.")
        self.documents = documents

        self.corpus_tokens = [
            _tokenize(doc.get("text_for_embedding", doc.get("original_text", "")))
            for doc in documents
        ]

        self.bm25 = BM25Okapi(self.corpus_tokens)
        logger.info(f"BM25Index: Index built. Vocab coverage across {len(self.corpus_tokens)} docs.")

    def search(self, query: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search over the indexed corpus.

        Args:
            query: The search query string.
            top_n: Number of top results to return.

        Returns:
            List of document dicts sorted by descending BM25 score,
            each augmented with a 'bm25_score' key.
        """
        if not self.bm25 or not self.documents:
            logger.warning("BM25Index: search() called before index_documents(). Returning empty.")
            return []

        query_tokens = _tokenize(query)
        logger.info(f"BM25Index: Searching for tokens: {query_tokens[:10]}...")

        scores = self.bm25.get_scores(query_tokens)

        # Pair each document with its BM25 score and sort descending
        scored_docs = list(zip(self.documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc, score in scored_docs[:top_n]:
            result = dict(doc)  # shallow copy
            result["bm25_score"] = float(score)
            results.append(result)

        logger.info(f"BM25Index: Returning top {len(results)} results (best score: {results[0]['bm25_score']:.4f})." if results else "BM25Index: No results.")
        return results
