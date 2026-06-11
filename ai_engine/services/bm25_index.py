import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BM25Index:
    """
    BM25 Wrapper for keyword-based search over the proposal and RFP chunks.
    Can use an in-memory ranker (rank_bm25) or Elasticsearch.
    """
    def __init__(self):
        self.corpus: List[str] = []
        self.documents: List[Dict[str, Any]] = []

    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the BM25 index.
        """
        logger.info(f"BM25Index: Indexing {len(documents)} documents.")
        self.documents = documents
        self.corpus = [doc.get("text_for_embedding", doc.get("original_text", "")) for doc in documents]
        # In a real implementation:
        # tokenized_corpus = [doc.lower().split() for doc in self.corpus]
        # self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search.
        """
        logger.info(f"BM25Index: Searching index for: '{query}'")
        if not self.documents:
            return []
            
        # Return mock matching documents (simple substring search fallback for mock)
        results = []
        for doc in self.documents:
            text = doc.get("original_text", "").lower()
            if any(word in text for word in query.lower().split()):
                results.append(doc)
            if len(results) >= top_n:
                break
                
        # If no substring matches, just return the first few
        if not results:
            results = self.documents[:top_n]
            
        return results
