# File: FastAPI Entry, ML Training, & Pydantic Schemas

This document explains the FastAPI entry point (`main.py`), the Machine Learning pipeline training scripts, and Pydantic data schemas.

---

## 🚀 1. FastAPI Application Entry Point (`ai_engine/main.py`)

`main.py` is the operational orchestrator for the FastAPI service, handling job queues and background processing.

### A. Core Configurations & Sub-routers
- **Logging**: Configured to log output to stdout and `rfp_engine.log` with a custom datetime format.
- **Lazy Imports**: Heavy packages (Qdrant, BM25, and LangGraph) are imported lazily on the first job request. This reduces startup times and saves memory.
- **Sub-routers Registered**:
  - `parsing_router` (document parsing / extraction)
  - `compliance_router` (Neo4j / Go/No-Go evaluation)
  - `proposal_router` (LangGraph proposal swarm)
  - `evaluate_rfp_router` (win probability & SHAP predictions)

### B. Background Task Processing
- **Queue System**:
  1. **`/process-rfp`**: Receives an `RfpJob` payload and logs it. It initializes the job status as `"queued"` in the in-memory `job_store` dictionary and adds the job to the FastAPI `BackgroundTasks` runner.
  2. **`process_rfp_background`**: The background runner executes the processing task:
     - **Step 1**: Runs `parse_azure_blob_hybrid` to download and parse the PDF.
     - **Step 1.5**: Segment document using parent-child chunking.
     - **Step 2**: Embeds the child chunks via the sentence-transformer and indices them in Qdrant and BM25.
     - **Step 3**: Invokes the `proposal_swarm_graph` LangGraph workflow with the initialized `AgentState`.
     - **Step 4**: Collects drafts, scores, and compliance metrics to update the `job_store` status to `"completed"`.
- **Status & Health Monitoring**:
  - **`/job-status/{job_id}`**: Retrieves the current status, errors, and metadata from the in-memory store.
  - **`/health`**: Returns the count of active and queued jobs.

---

## 📊 2. Machine Learning Training Pipelines

The Random Forest win-probability engine uses two scripts to train and serialize the Scikit-Learn model files.

### A. Excel-based Trainer (`ai_engine/train_gonogo.py`)
- **Execution Flow**:
  1. Loads historical bid results from a `Sample_Datasets.xlsx` sheet.
  2. Extracts features: `capability_score`, `budget_alignment`, `timeline_feasibility`, `past_win_rate`, `competitive_intensity`, and `strategic_value`.
  3. **Robust Fallback**: If the required columns are missing, it generates synthetic data with normal distributions based on whether the bid was won or lost.
  4. Invokes `GoNoGoEngine.train_model(training_data, save=True)` to fit the Random Forest model and save it.

### B. Local Feature Mock Trainer (`ai_engine/mock_trainer.py`)
- **Execution Flow**:
  1. Generates 500 mock bid entries with random uniform rates for compliance, tech gaps, and budget margins.
  2. Applies a feature-importance formula ($score = c \times 0.4 - g \times 0.05 + m \times 0.5$) with normal noise to assign target win/loss labels.
  3. Fits a `StandardScaler` to normalize features.
  4. Trains a `RandomForestClassifier` (100 estimators, max depth 5).
  5. Serializes the combined scaler and classifier using Joblib into `models/rf_model.joblib`.

---

## 📝 3. Pydantic Validation Schemas (`ai_engine/schemas/`)

Data transfer objects (DTOs) enforce payload compliance across API request boundaries.

### A. Compliance Schemas (`compliance.py`)
- **`RequirementCreateSchema`**: Validates the payload used to create a requirement node. Includes fields for `requirementId`, `sectionPath`, `description`, `isMandatory`, and `pageRef`.
- **`ComplianceLinkSchema`**: Enforces strict patterns (COMPLIANT, PARTIAL, NON_COMPLIANT) and validates range limits for compliance scores ($0.0 \le score \le 1.0$) when linking proposal drafts to requirements.
- **`GoNoGoEvaluateSchema`**: Defines strict boundary limits ($0.0 \le value \le 1.0$) for features sent to the Random Forest model.
- **`GoNoGoResponseSchema`**: Formats the returned decision, feature impact lists, win probability, and top factor arrays.

### B. Proposal Schemas (`proposal.py`)
- **`ProposalGenerationRequest`**: Requires the database `projectId` and parsed `rfpText`.
- **`ProposalGenerationResponse`**: Structs the output sent back to the .NET gateway, including section draft previews, approval flags, and compliance counts.

### C. RFP Schemas (`rfp.py`)
- **`RFPParseRequest`**: Validates incoming parsing jobs, requiring `jobId`, `blobUrl`, and `filename`.
- **`ParserResult`**: Formats parser metrics and outputs, returning parent section counts and raw markdown previews.
