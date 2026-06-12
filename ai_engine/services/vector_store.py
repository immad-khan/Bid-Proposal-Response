import os
import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Qdrant Client wrapper for managing document embeddings.
    """
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        self.url = url or os.getenv("QDRANT_URL", "https://94c5ebf0-8087-421a-a94c-f8f0a86585d0.us-east-2-0.aws.cloud.qdrant.io")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        
        logger.info(f"VectorStore: Initializing Qdrant client pointing to {self.url}")
        self.client = QdrantClient(url=self.url, api_key=self.api_key)

    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]):
        """
        Add documents to the specified Qdrant collection.
        If the collection doesn't exist, it creates it.
        """
        logger.info(f"VectorStore: Adding {len(documents)} documents to Qdrant collection '{collection_name}'")
        
        # Ensure collection exists (assume vector size of 1536 for standard embeddings like OpenAI text-embedding-3-small)
        vector_size = 1536
        
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                logger.info(f"VectorStore: Creating collection '{collection_name}' with vector size {vector_size}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                
            points = []
            for doc in documents:
                embedding = doc.get("embedding")
                if not embedding:
                    # Mock embedding (1536 dimensions)
                    import random
                    embedding = [random.uniform(-0.1, 0.1) for _ in range(vector_size)]
                    
                # Qdrant requires uuid or int for point ID
                point_id = doc.get("id")
                try:
                    # Validate if it's already a valid UUID
                    point_id = str(uuid.UUID(point_id))
                except (ValueError, TypeError):
                    # Fallback: create a deterministic UUID from the string ID
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(point_id)))
                    
                payload = {
                    "text": doc.get("text_for_embedding", doc.get("original_text", "")),
                    "original_text": doc.get("original_text", ""),
                    **doc.get("metadata", {})
                }
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                )
                
            if points:
                self.client.upsert(
                    collection_name=collection_name,
                    wait=True,
                    points=points
                )
                logger.info(f"VectorStore: Successfully upserted {len(points)} points.")
        except Exception as e:
            logger.error(f"VectorStore: Failed to add documents to Qdrant: {str(e)}")

    def query(self, collection_name: str, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query the Qdrant collection for matching documents.
        """
        logger.info(f"VectorStore: Querying collection '{collection_name}' with: '{query_text}'")
        
        # Mock embedding of query text (1536 dimensions)
        import random
        query_vector = [random.uniform(-0.1, 0.1) for _ in range(1536)]
        
        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=n_results
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "id": str(hit.id),
                    "text": hit.payload.get("text", ""),
                    "original_text": hit.payload.get("original_text", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k not in ["text", "original_text"]},
                    "score": hit.score
                })
            return results
        except Exception as e:
            logger.error(f"VectorStore: Error querying Qdrant: {str(e)}")
            # Fallback if connection fails or collection is empty/missing
            return [
                {
                    "id": f"fallback_{i}",
                    "text": f"Fallback matching content for {query_text} (Result {i})",
                    "metadata": {"score": 0.85 - (i * 0.05)},
                    "score": 0.85 - (i * 0.05)
                }
                for i in range(n_results)
            ]
