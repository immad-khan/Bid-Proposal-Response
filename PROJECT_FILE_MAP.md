# Detailed Project File Map & Source Code Reference

This document provides a comprehensive, file-by-file breakdown of the entire **Bid Proposal Response Engine** codebase, explaining the exact purpose and details of every major directory, C# service, React component, and Python FastAPI route.

---

## 📁 Repository Structure Overview

```
├── ai_engine/                    # Python FastAPI AI Engine & Agent Swarm
│   ├── agents/                   # LangGraph Multi-Agent Swarm Definitions
│   ├── models/                   # ML Joblib Files (RandomForest)
│   ├── routes/                   # HTTP Endpoints (FastAPI)
│   ├── services/                 # Extractors, Chunkers, Vector Stores, ML Engines
│   ├── tests/                    # Agent Swarm & Parser Tests
│   └── main.py                   # FastAPI Application Entrypoint
│
├── backend/                      # C# .NET 10 Web API Core Orchestration
│   ├── Controllers/              # Auth, Dashboard, Workspace, Proposal Controllers
│   ├── Data/                     # EF Core Database Mappings & Seed Contexts
│   ├── Models/                   # Data transfer objects & Database entities
│   ├── Services/                 # Collaboration, DB writes, storage, mail services
│   └── program.cs                # Web API Core Entrypoint & Config Mappings
│
├── frontend/                     # Next.js 15 App Client Presentation Layer
│   ├── app/                      # Page Routing, Global Layout, Styling
│   │   ├── page.tsx              # Application Main Shell
│   │   └── layout.tsx            # Global Layout Wrapper
│   ├── components/               # Presentation & Interactive Components
│   │   ├── compliance_matrix/    # Go/No-Go and Compliance Panels
│   │   ├── dashboard/            # High-Level Project Dashboard Views
│   │   ├── editor/               # Agent Workspace Panels
│   │   ├── InlineDocumentEditor  # Slate.js Rich text interface
│   │   ├── VersionDiff           # Character Comparison Visualizer
│   │   └── WinProbabilityChart   # Recharts Line & Area Visuals
│   └── services/                 # Centralized apiClient providers
```

---

## 🎨 Frontend Presentation Layer (`frontend/`)

### 1. Root Application & Page Structure
* **`frontend/app/page.tsx`**
  - **Purpose:** The main application container shell.
  - **Details:** Manages the user session state, selected active project context, and top-level view tabs (`viewMode === 'upload' | 'dashboard'`). It conditionally displays either the global Win Probability Dashboard or the local Project Ingestion workspace panels.
* **`frontend/app/layout.tsx`**
  - **Purpose:** Next.js root layout wrapper.
  - **Details:** Handles global CSS fonts, sets HTML metadata tags, and applies Tailwind CSS class parameters.
* **`frontend/services/apiClient.ts`**
  - **Purpose:** Central HTTP proxy service client.
  - **Details:** Standardizes fetching across the project, manages JWT bearer token injection, and routes requests to either the ASP.NET Core backend or the FastAPI engine proxy.

### 2. Interactive Presentation Components (`frontend/components/`)
* **`frontend/components/WinProbabilityChart.tsx`**
  - **Purpose:** Detailed win probability diagnostic chart.
  - **Details:** Uses Recharts to render complex visualizations including line trends, area charts, and SHAP force-plot bars representing the direct influence of compliance rates, gaps, and cost margins.
* **`frontend/components/InlineDocumentEditor.tsx`**
  - **Purpose:** WYSIWYG rich text editor.
  - **Details:** A full implementation of Slate.js supporting rich-text nodes, paragraph blocks, and real-time HTTP drafts autosave with commenting.
* **`frontend/components/VersionDiff.tsx`**
  - **Purpose:** Version comparative visualizer.
  - **Details:** Implements a character-matching diff engine that lists previous draft snapshots and displays visual color codings (red highlighting for deleted words, green for added text).

### 3. Sub-Component Groups
* **`frontend/components/dashboard/WinProbabilityDashboard.tsx`**
  - **Purpose:** Executive review panel.
  - **Details:** Lists all projects, deadlines, client descriptions, and win probability outcomes side-by-side to allow managers to quickly identify promising prospects.
* **`frontend/components/dashboard/Overview.tsx`**
  - **Purpose:** Performance tracking dashboard.
  - **Details:** Computes general metrics across projects (average win rate, total compliance gaps, pending decisions).
* **`frontend/components/editor/ProposalSwarmWorkspace.tsx`**
  - **Purpose:** Agent workflow interface.
  - **Details:** Interacts with the LangGraph backend to display running agent status updates, planning outlines, drafts, and reviews.
* **`frontend/components/compliance_matrix/workspace/ComplianceMatrix.tsx`**
  - **Purpose:** Interactive compliance checklist.
  - **Details:** Shows specific requirements, compliant vs non-compliant parameters, and missing evidence files.
* **`frontend/components/compliance_matrix/workspace/GoNoGoEvaluator.tsx`**
  - **Purpose:** Parametric Go/No-Go evaluator.
  - **Details:** Provides slider controls (compliance rating, cost margins, budget limits) to query the Python ML models dynamically and display real-time predictions.

---

## ⚡ Backend Orchestration Layer (`backend/`)

### 1. ASP.NET MVC Core Controllers (`backend/Controllers/`)
* **`AuthController.cs`**
  - **Purpose:** User session initialization.
  - **Details:** Validates user login requests and returns a signed JSON Web Token (JWT) containing mock claims.
* **`ProjectController.cs`**
  - **Purpose:** Active RFP project catalog endpoints.
  - **Details:** Manages fetching projects, adding project records, and updating their active statuses.
* **`RfpUploadController.cs`**
  - **Purpose:** Handles new document uploads.
  - **Details:** Receives raw file multi-part uploads, saves files to Azure Blob Storage, and triggers parsing.
* **`DashboardController.cs`**
  - **Purpose:** Aggregates executive dashboard data.
  - **Details:** Fetches backend projects, queries the FastAPI service endpoints, calculates sorted statistics, and returns them to the React frontend.
* **`WorkspaceController.cs`**
  - **Purpose:** Collaborator workspace router.
  - **Details:** Manages team creation, auto-saves draft snapshots, lists version history logs, processes workspace invites, and triggers PDF downloads.
* **`ComplianceController.cs`**
  - **Purpose:** Relays compliance matrices.
  - **Details:** Pulls compliance requirements and maps relationship nodes.
* **`ProposalController.cs`**
  - **Purpose:** Swarm generation controller.
  - **Details:** Acts as an endpoint gateway to start, execute, and retrieve output from the LangGraph agent swarms.

### 2. Service Pipeline Implementation (`backend/Services/`)
* **`WorkspaceService.cs`**
  - **Purpose:** Project workspace manager.
  - **Details:** Handles creating team workspaces, adding user members, storing new versions, sending emails, and rendering document outputs.
* **`DashboardService.cs`**
  - **Purpose:** Win probability analytics calculator.
  - **Details:** Queries FastAPI compliance score and Go/No-Go prediction endpoints, maps SHAP values, and applies the weighted win probability formula.
* **`BlobStorageService.cs`**
  - **Purpose:** Cloud file storage provider.
  - **Details:** Integrates Azure Blob Storage, with fallbacks to local filesystems when storage variables are omitted.
* **`DocumentGenerator.cs`**
  - **Purpose:** Document exporter.
  - **Details:** Converts HTML / Slate JSON text strings into downloadable PDF or Docx byte streams.
* **`EmailService.cs`**
  - **Purpose:** Workspace notifications.
  - **Details:** Sends signup invitations and collaborator notification emails.
* **`AuthService.cs`**
  - **Purpose:** Secure JWT constructor.
  - **Details:** Signs and packages encryption payloads for client handshakes.
* **`ProjectManagementService.cs`**
  - **Purpose:** General project CRUD service.
  - **Details:** Handles project status state transitions and metadata tracking.

### 3. Data & Entity Models (`backend/Data/` & `backend/Models/`)
* **`ApplicationDbContext.cs`**
  - **Purpose:** EF Core database context configuration.
  - **Details:** configures database tables (`Users`, `Projects`, `Workspaces`, `WorkspaceMembers`, `ProposalVersions`, `PendingInvites`) and seeds initial demonstration projects (e.g. NASA RFP, DoD Cloud System).
* **`DbModels.cs`**
  - **Purpose:** Primary database schema declarations.
  - **Details:** Configures entity classes, relationships, primary keys, and foreign keys.
* **`DashboardDto.cs`**
  - **Purpose:** Win probability data structures.
  - **Details:** Schema definitions for JSON communication of SHAP features, probabilities, and cost margins.
* **`Dto.cs`**
  - **Purpose:** Shared transfer schemas.
  - **Details:** Reusable formats for credentials, file details, and custom system outputs.

* **`backend/program.cs`**
  - **Purpose:** Main runtime entrypoint.
  - **Details:** Registers dependencies, reads environment configuration strings, applies DB migrations, configures CORS, and maps controller routes.

---

## 🤖 Python FastAPI AI Core & ML Engine (`ai_engine/`)

### 1. API Controllers & Routers (`ai_engine/routes/`)
* **`parsing.py`:** REST endpoints handling document extraction and hierarchical parsing logic.
* **`compliance.py`:** Fetches compliance checklists and queries requirements from Neo4j.
* **`proposal.py`:** Initiates agent drafts and manages swarm state updates.
* **`evaluate_rfp.py`:** Executes the ML Random Forest model, runs SHAP explanations, and returns feature attribution metrics.

### 2. Multi-Agent Swarm Orchestration (`ai_engine/agents/`)
* **`state.py`:** Defines the LangGraph state dict (`rfp_text`, `sections`, `plan`, `drafts`, `reviews`, `approved`).
* **`planner.py`:** Creates structural outlines based on parent sections.
* **`writer.py`:** Generates technical text drafts utilizing Qdrant vector retrieval.
* **`judge.py`:** Evaluates generated text for tone, quality, and accuracy.
* **`gatekeeper.py`:** Checks drafts against requirements to identify compliance gaps.
* **`workflow.py`:** Compiles the LangGraph state machine, linking nodes with conditional routing.

### 3. Infrastructure & Model Pipelines (`ai_engine/services/`)
* **`go_nogo_engine.py`**
  - **Purpose:** Machine learning decision model.
  - **Details:** Features extractor combining LangGraph metrics with Neo4j compliance rates. Scores inputs using a **Random Forest Classifier** and computes SHAP feature attributions.
* **`parser_service.py`**
  - **Purpose:** Layout-aware document extraction service.
  - **Details:** Combines Docling table structure recognition with PDFPlumber positional parsing.
* **`chunking_service.py`**
  - **Purpose:** Hierarchical document segmentation.
  - **Details:** Slices documents into parent context blocks and child retrieval nodes.
* **`vector_store.py`**
  - **Purpose:** Qdrant DB abstraction layer.
  - **Details:** Handles collection creation, embeddings generation, and vector search querying.
* **`bm25_index.py`**
  - **Purpose:** TF-IDF keyword searching.
  - **Details:** Provides exact keyword matching capabilities.
* **`compliance_matrix.py`**
  - **Purpose:** Graph database interface.
  - **Details:** Interfaces with Neo4j to store requirements and evidence relationships.
* **`llm_client.py`**
  - **Purpose:** Large Language Model connector.
  - **Details:** Handles interactions with external LLM APIs (e.g. Groq, OpenAI).
* **`reranker.py` & `retrieval_service.py`**
  - **Purpose:** Document ranking pipelines.
  - **Details:** Implements hybrid ranking by combining BM25 keyword match results with Qdrant vector scores.

---

## 🐳 Root Deployment Mappings
* **`docker-compose.yml`:** Defines the multi-container stack, setting ports, DB credentials, and linking the `frontend`, `backend`, `ai_engine`, `qdrant`, `neo4j`, and `postgres` containers.
* **`.env`:** Stores environment-specific configuration values, API URLs, and database connection strings.
