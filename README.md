# RFP Proposal Response Engine

An automated system to parse, analyze, and construct compliant RFP responses using an agentic AI architecture.

## Architecture & File Structure

The project is structured as a multi-service monorepo:

- **`/backend`**: .NET 10 Web API serving as the main core service (Authentication, Blob Storage integration, Project Management).
- **`/ai_engine`**: Python FastAPI microservice + LangGraph orchestrating the multi-agent swarm (Planner, Writer, Gatekeeper, LLM Judge).
  - Parent-Child Chunking and hybrid vector/BM25 retrieval.
- **`/frontend`**: React / Next.js single-page application.
- **`/infrastructure`**: Configuration files and Dockerfiles for development-supporting databases (ChromaDB, Neo4j, Redis, Elasticsearch).
- **`/notebooks`**: Jupyter Notebooks for local evaluation of retrieval accuracy and compliance scoring.

## Quick Start (Docker Compose)

1. Copy `.env.example` to `.env` and fill in the required LLM API keys:
   ```bash
   cp .env.example .env
   ```

2. Spin up the application stack:
   ```bash
   docker-compose up --build
   ```

3. Access the services:
   - **Frontend:** http://localhost:3000
   - **.NET API:** http://localhost:5000
   - **AI Engine (Swagger Docs):** http://localhost:8000/docs
