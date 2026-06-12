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
    Supports multiple collections.
    """

    def __init__(self):
        # Maps collection_name -> {"documents": [...], "bm25": BM25Okapi}
        self.collections: Dict[str, Dict[str, Any]] = {}

    def index_documents(self, documents: List[Dict[str, Any]], collection_name: str = "default"):
        """
        Build the BM25 inverted index from a list of document dicts.
        Each document should have 'text_for_embedding' or 'original_text'.

        Args:
            documents: List of chunk dicts.
            collection_name: The name of the collection to index into.
        """
        logger.info(f"BM25Index: Indexing {len(documents)} documents into '{collection_name}'.")

        corpus_tokens = [
            _tokenize(doc.get("text_for_embedding", doc.get("original_text", "")))
            for doc in documents
        ]

        bm25 = BM25Okapi(corpus_tokens)
        
        self.collections[collection_name] = {
            "documents": documents,
            "bm25": bm25
        }
        logger.info(f"BM25Index: Index built for '{collection_name}'. Vocab coverage across {len(corpus_tokens)} docs.")

    def search(self, query: str, collection_name: str = "default", top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search over the indexed corpus.

        Args:
            query: The search query string.
            collection_name: The name of the collection to search.
            top_n: Number of top results to return.

        Returns:
            List of document dicts sorted by descending BM25 score.
        """
        collection = self.collections.get(collection_name)
        if not collection:
            logger.warning(f"BM25Index: search() called for unknown collection '{collection_name}'. Returning empty.")
            return []

        bm25 = collection["bm25"]
        documents = collection["documents"]

        query_tokens = _tokenize(query)
        logger.info(f"BM25Index: Searching '{collection_name}' for tokens: {query_tokens[:10]}...")

        scores = bm25.get_scores(query_tokens)

        # Pair each document with its BM25 score and sort descending
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc, score in scored_docs[:top_n]:
            if score <= 0:
                continue
            result = dict(doc)  # shallow copy
            result["bm25_score"] = float(score)
            results.append(result)

        logger.info(f"BM25Index: Returning top {len(results)} results (best score: {results[0]['bm25_score']:.4f})." if results else "BM25Index: No results.")
        return results
