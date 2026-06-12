# File: AI Service Infrastructure & Data Clients

This document describes the design, configuration, and API interfaces for the low-level data clients and service classes in the `ai_engine/services/` directory.

---

## 🔗 1. Neo4j Graph Database Client (`compliance_matrix.py`)

The `ComplianceMatrixService` class connects to Neo4j to manage requirement nodes, proposal section nodes, and evidence linkages.

### A. Initialization
- **Environment Variables**:
  - `NEO4J_URI` (defaults to `bolt://localhost:7687`)
  - `NEO4J_USERNAME` (defaults to `neo4j`)
  - `NEO4J_PASSWORD` (defaults to `password`)
- **Connection Lifecycle**: Initializes a standard `GraphDatabase.driver` instance and calls `verify_connectivity()` to validate database availability on startup. A `close()` method is provided to tear down connections.

### B. Graph Schema
- **Requirement Node (`Requirement`)**: Contains `id` (e.g. `REQ_001`), `section_path`, `description`, `is_mandatory`, `page_reference`, and `updated_at`.
- **Proposal Section Node (`ProposalSection`)**: Contains `id`, `title`, `content_preview`, and `updated_at`.
- **Evidence Node (`Evidence`)**: Contains `id`, `title`, `document_url`, and `updated_at`.
- **Relationships**:
  - `(ProposalSection)-[:COMPLIES_WITH {status, score, evidence}]->(Requirement)`: Records the compliance evaluation of a drafted proposal section against a requirement.
  - `(Evidence)-[:SATISFIED_BY]->(Requirement)`: Identifies verified evidence documents supporting a requirement.

### C. Queries & Export
- **Matrix Extraction**: `get_compliance_matrix()` executes a Cypher query retrieving linked proposal sections and requirements sorted by section path.
- **Gap Analysis**: `get_missing_requirements()` returns all requirements that lack a incoming `COMPLIES_WITH` relationship, prioritizing mandatory requirements.
- **CSV Export**: `export_to_csv()` compiles the compliance matrix into a CSV format with detailed column mappings for auditing.

---

## 🗄️ 2. Vector DB Client (`vector_store.py`)

The `VectorStore` class wraps the Qdrant Cloud client to manage document embeddings.

- **Embedding Model**: Uses a local `SentenceTransformer` loading `"BAAI/bge-small-en-v1.5"` (384 dimensions, cosine distance metric) to compute dense vector embeddings.
- **Point ID Resolution**: Qdrant requires UUIDs for database point identifiers. `_resolve_point_id()` converts arbitrary input keys into UUIDv5 objects under the DNS namespace to guarantee idempotency.
- **Upsert Batches**: Document payloads are embedded and upserted in batches of 100 to optimize write throughput.
- **Similarity Queries**: Computes a cosine similarity search on query embeddings, returning matching payloads paired with search scores.

---

## 🔤 3. Keyword Search Index (`bm25_index.py`)

The `BM25Index` class handles sparse keyword retrieval using the `rank_bm25` library.

- **Tokenizer**: Features an alphanumeric tokenizer (`re.findall(r"\w+", text.lower())`) to prepare clean tokens for the Okapi BM25 engine.
- **In-Memory Store**: Holds document lists and token arrays in memory, allowing for fast TF-IDF scoring.
- **Retrieval leg**: Combines with Qdrant inside `retrieval_service.py` to support hybrid search.

---

## 🔄 4. Semantic Reranker (`reranker.py`)

The `Reranker` class utilizes a Cross-Encoder model to refine candidate lists.

- **Model**: Loads `"cross-encoder/ms-marco-MiniLM-L-6-v2"` with a 512-token limit.
- **Batch Evaluation**: Evaluates all candidate (query, text) pairs in a single model execution.
- **Re-sorting**: Re-orders candidate documents by descending relevance score to minimize retrieval noise before context is forwarded to the LLM writer.

---

## 🤖 5. Unified LLM Client (`llm_client.py`)

The `LLMClient` coordinates API calls across multiple LLM providers.

- **Lazy Initialization**: Postpones provider SDK imports and client initialization until the first `generate()` call. This prevents initialization errors when optional SDK packages are absent.
- **Providers Supported**:
  - **OpenAI**: Uses the chat completions API (defaults to `gpt-4o-mini`).
  - **Groq**: Configures high-speed inference (defaults to `llama-3.3-70b-versatile`).
  - **Anthropic**: Interfaces with the Messages API (defaults to `claude-3-5-sonnet-20241022`).
- **Structured JSON Support**: `generate_json()` prompts models to return JSON content, parses outputs, and automatically strips markdown block tags (e.g., ` ```json `) prior to decoding.
