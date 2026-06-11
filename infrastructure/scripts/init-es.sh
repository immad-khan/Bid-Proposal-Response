#!/bin/bash
# ==============================================================================
# Elasticsearch Index Mappings & Settings Initialization Script
# ==============================================================================

ES_HOST=${ELASTICSEARCH_HOST:-"http://localhost:9200"}
INDEX_NAME="rfp_documents"

echo "Waiting for Elasticsearch to become healthy at ${ES_HOST}..."
until curl -s "${ES_HOST}/_cat/health" >/dev/null; do
    sleep 3
done
echo "Elasticsearch is ready!"

# Create index with BM25 keyword config and custom analyzer
echo "Creating Elasticsearch index '${INDEX_NAME}'..."
curl -X PUT "${ES_HOST}/${INDEX_NAME}" -H 'Content-Type: application/json' -d '{
  "settings": {
    "index": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    },
    "analysis": {
      "analyzer": {
        "rfp_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "snowball"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "chunk_id": { "type": "keyword" },
      "original_text": { "type": "text", "analyzer": "rfp_analyzer" },
      "section_path": { "type": "text" },
      "page_start": { "type": "integer" },
      "page_end": { "type": "integer" }
    }
  }
}'

echo "Index ${INDEX_NAME} initialized successfully!"
