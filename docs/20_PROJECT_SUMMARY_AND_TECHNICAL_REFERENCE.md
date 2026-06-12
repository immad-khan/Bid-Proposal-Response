# Technical Summary & System Reference

This document serves as the master index and architectural overview for the **Bid Proposal Response Engine**, summarizing the technical designs and linking the deep-dive manuals.

---

## 🗺️ Documentation Index

For exhaustive breakdowns of specific system areas, refer to the following guides:

1. **API Mappings & Extractors**: [`10_AI_FASTAPI_ROUTES_AND_EXTRACTION.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/10_AI_FASTAPI_ROUTES_AND_EXTRACTION.md)
2. **LangGraph Multi-Agent Swarm**: [`11_AI_MULTI_AGENT_SWARM.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/11_AI_MULTI_AGENT_SWARM.md)
3. **Core AI Service Infrastructure**: [`12_AI_SERVICE_INFRASTRUCTURE.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/12_AI_SERVICE_INFRASTRUCTURE.md)
4. **App Entry, ML Training, & Schemas**: [`13_AI_FASTAPI_ENTRY_TRAINING_AND_SCHEMAS.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/13_AI_FASTAPI_ENTRY_TRAINING_AND_SCHEMAS.md)
5. **Frontend Presentation Components**: [`14_FRONTEND_DASHBOARD_COMPONENTS.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/14_FRONTEND_DASHBOARD_COMPONENTS.md)
6. **Frontend API Client & Communication**: [`15_FRONTEND_SERVICES_AND_API_CLIENT.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/15_FRONTEND_SERVICES_AND_API_CLIENT.md)
7. **C# Backend Services**: [`16_BACKEND_SERVICES_AND_ORCHESTRATION.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/16_BACKEND_SERVICES_AND_ORCHESTRATION.md)
8. **C# Schemas & Database Entities**: [`17_BACKEND_MODELS_AND_DATA_SCHEMAS.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/17_BACKEND_MODELS_AND_DATA_SCHEMAS.md)
9. **C# Application Startup & Bootstrapping**: [`18_BACKEND_BOOTSTRAP_AND_SEEDING.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/18_BACKEND_BOOTSTRAP_AND_SEEDING.md)
10. **Deployment Configurations & Containers**: [`19_ROOT_DEPLOYMENT_AND_DOCKER.md`](file:///home/ziki/Unity%20user%20templates/Bid-Proposal-Response/docs/19_ROOT_DEPLOYMENT_AND_DOCKER.md)

---

## 🏗️ Architectural Blueprint

The application uses a three-tier architecture:

```
[ Next.js 15 UI Client ] 
        │
        ▼ (JWT Bearer Auth)
[ .NET 10 Gateway API ] <=====> SQLite (rfp.db) / Postgres
        │
        ▼ (Internal Proxy REST)
[ FastAPI AI & ML Swarm Engine ]
   ├── Qdrant (Dense Retrieval)
   ├── Neo4j (Graph Compliance Relations)
   └── Scikit-Learn (Random Forest Viability)
```

---

## 💡 Key Design Patterns & Engineering Decisions

1. **Lazy Dependency Ingestion**:
   - Python modules connect to vector and graph storage endpoints on-demand.
   - Prevents startup crashes if services load out of order.

2. **RRF & Dense-Sparse Retrieval**:
   - Combines vector search (Qdrant) and term matching (BM25) using Reciprocal Rank Fusion (RRF).
   - Results are prioritized using a cross-encoder reranker.

3. **Strict Gatekeeper Compliance Guardrails**:
   - Evaluates draft compliance using validation checks (contradiction checks, draft placeholders, empty sections) before completing a workflow.
   - Logs audit events directly to Neo4j.

4. **Bi-directional SHAP Explanations**:
   - Computes local feature impacts using a Random Forest model.
   - Outputs attributions indicating positive or negative impact.

5. **Slate JSON Version Differentials**:
   - Compares document drafts at the line level.
   - Implements a Longest Common Subsequence (LCS) algorithm to compute differences.
