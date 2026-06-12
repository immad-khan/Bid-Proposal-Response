"""
Vector Store — Qdrant client with real sentence-transformer embeddings.
Manages collection lifecycle, document upsert with dense vectors,
and similarity search against Qdrant Cloud.
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Default embedding model — compact (33M params, 384-dim) and fast
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_VECTOR_SIZE = 384


class VectorStore:
    """
    Qdrant Cloud client wrapper for managing document embeddings.
    Uses a local SentenceTransformer model to generate dense vectors
    and upserts them into Qdrant collections.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        self.url = url or os.getenv(
            "QDRANT_URL",
            "https://94c5ebf0-8087-421a-a94c-f8f0a86585d0.us-east-2-0.aws.cloud.qdrant.io",
        )
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")

        logger.info(f"VectorStore: Initializing Qdrant client → {self.url}")
        self.client = QdrantClient(url=self.url, api_key=self.api_key)

        # Load embedding model
        model_name = embedding_model or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        logger.info(f"VectorStore: Loading embedding model '{model_name}'...")
        self.embedding_model = SentenceTransformer(model_name)
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"VectorStore: Ready. Vector dimension = {self.vector_size}")

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Generate dense embeddings for a batch of texts."""
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()

    def _ensure_collection(self, collection_name: str):
        """Create the collection if it does not exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)

        if not exists:
            logger.info(
                f"VectorStore: Creating collection '{collection_name}' "
                f"(dim={self.vector_size}, distance=Cosine)"
            )
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=Distance.COSINE
                ),
            )

    def _resolve_point_id(self, raw_id: Any) -> str:
        """Convert an arbitrary ID into a valid UUID string for Qdrant."""
        try:
            return str(uuid.UUID(str(raw_id)))
        except (ValueError, TypeError):
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_id)))

    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]):
        """
        Embed and upsert documents into the specified Qdrant collection.

        Each document dict should contain:
            - id: Unique chunk identifier.
            - text_for_embedding: Text that will be embedded.
            - original_text: Original unmodified chunk text (stored in payload).
            - metadata: Dict of additional metadata fields.

        Args:
            collection_name: Name of the Qdrant collection.
            documents: List of chunk dicts from chunking_service.prepare_for_vector_db().
        """
        if not documents:
            logger.warning("VectorStore: add_documents() called with empty list.")
            return

        logger.info(f"VectorStore: Embedding and upserting {len(documents)} documents → '{collection_name}'")
        self._ensure_collection(collection_name)

        # Batch embed all texts
        texts_to_embed = [
            doc.get("text_for_embedding", doc.get("original_text", ""))
            for doc in documents
        ]
        embeddings = self._embed(texts_to_embed)

        # Build Qdrant points
        points = []
        for doc, embedding in zip(documents, embeddings):
            point_id = self._resolve_point_id(doc.get("id", uuid.uuid4()))
            payload = {
                "text": doc.get("text_for_embedding", ""),
                "original_text": doc.get("original_text", ""),
                **doc.get("metadata", {}),
            }
            points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(
                collection_name=collection_name, wait=True, points=batch
            )

        logger.info(f"VectorStore: Successfully upserted {len(points)} points.")

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Embed the query and perform similarity search against the Qdrant collection.

        Args:
            collection_name: Name of the collection to search.
            query_text: The search query string.
            n_results: Number of nearest neighbors to return.

        Returns:
            List of result dicts with id, text, original_text, metadata, and score.
        """
        logger.info(f"VectorStore: Querying '{collection_name}' with: '{query_text[:80]}...'")

        # Embed the query
        query_vector = self._embed([query_text])[0]

        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=n_results,
            )

            results = []
            for hit in search_result:
                results.append(
                    {
                        "id": str(hit.id),
                        "text": hit.payload.get("text", ""),
                        "original_text": hit.payload.get("original_text", ""),
                        "metadata": {
                            k: v
                            for k, v in hit.payload.items()
                            if k not in ("text", "original_text")
                        },
                        "score": hit.score,
                    }
                )
            logger.info(f"VectorStore: Returned {len(results)} results.")
            return results

        except Exception as e:
            logger.error(f"VectorStore: Search failed — {type(e).__name__}: {e}")
            raise
