# RFP Proposal Response Engine

An automated system to parse, analyze, and construct compliant RFP responses using an agentic AI architecture powered by LangGraph multi-agent orchestration.

## Architecture & File Structure

The project is structured as a multi-service monorepo:

- **`/backend`**: .NET 10 Web API serving as the main core service (JWT Authentication, Azure Blob Storage integration, Project Management).
- **`/ai_engine`**: Python FastAPI microservice + LangGraph orchestrating the multi-agent swarm (Planner, Writer, Gatekeeper, LLM Judge).
  - Parent-Child Chunking and hybrid vector/BM25 retrieval.
  - **Qdrant Cloud** for dense vector similarity search.
  - **Neo4j** for compliance requirement tracing (knowledge graph).
  - **Cross-Encoder Reranking** via `sentence-transformers`.
  - **Go/No-Go ML Engine** using `scikit-learn` RandomForest + `SHAP` explanations.
- **`/frontend`**: React / Next.js single-page application with real-time agent monitoring and compliance dashboards.
- **`/infrastructure`**: Configuration files and Dockerfiles for supporting databases (Neo4j, Redis, Elasticsearch).
- **`/notebooks`**: Jupyter Notebooks for evaluating retrieval accuracy and compliance scoring.

## Quick Start (Docker Compose)

1. Copy `.env.example` to `.env` and fill in the required API keys:
   ```bash
   cp .env.example .env
   ```

2. Required environment variables:
   - At least one LLM provider key: `GROQ_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`
   - `QDRANT_API_KEY` — your Qdrant Cloud cluster API key
   - `AZURE_STORAGE_CONNECTION_STRING` — Azure Blob Storage connection string

3. Spin up the application stack:
   ```bash
   docker-compose up --build
   ```

4. Access the services:
   - **Frontend:** http://localhost:3000
   - **.NET API (Swagger):** http://localhost:5000/swagger
   - **AI Engine (Swagger Docs):** http://localhost:8000/docs
   - **Neo4j Browser:** http://localhost:7474

## Technology Stack

| Layer | Technology |
| --- | --- |
| Orchestration | Docker Compose |
| AI Engine | Python 3.11, FastAPI, LangGraph |
| LLM Providers | OpenAI, Groq, Anthropic (configurable) |
| Vector DB | Qdrant Cloud |
| Embeddings | BAAI/bge-small-en-v1.5 (SentenceTransformers) |
| Reranking | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Graph DB | Neo4j 5 |
| Keyword Search | rank-bm25 (BM25Okapi) |
| Backend API | .NET 10, C# |
| Frontend | Next.js 15, React 19, TypeScript |
| Object Storage | Azure Blob Storage |
| Caching | Redis |
