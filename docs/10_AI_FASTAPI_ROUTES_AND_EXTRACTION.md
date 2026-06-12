# File: FastAPI Routes & Extraction Service

This document describes the FastAPI routing layer and entity extraction service in the AI engine.

---

## 🛣️ 1. FastAPI Routers (`ai_engine/routes/`)

The FastAPI application mounts specialized sub-routers to expose modular endpoints to the .NET gateway.

### A. Compliance Routes (`ai_engine/routes/compliance.py`)
Interfaces with the Neo4j compliance graph and runs Go/No-Go bid evaluations.
* **`[POST] /compliance/requirement`**: Unpacks `RequirementCreateSchema` and calls `neo4j_service.create_requirement_node` to register a requirement with its description, page reference, and mandatory flag.
* **`[POST] /compliance/link`**: Takes `ComplianceLinkSchema` to create a relationship mapping a proposal section node to a requirement node (`COMPLIES_WITH`).
* **`[GET] /compliance/matrix`**: Retrieves the active requirements-evidence matrix from Neo4j.
* **`[GET] /compliance/summary`**: Aggregates compliance stats and lists unsatisfied requirements.
* **`[POST] /compliance/evaluate-bid`**: Evaluates RFP criteria (budget alignment, past win rate, strategic value) via the Go/No-Go machine learning model.
* **`[GET] /compliance/export`**: Compiles the Neo4j compliance data into a CSV file and streams the output as a downloadable attachment.

### B. RFP Evaluation Routes (`ai_engine/routes/evaluate_rfp.py`)
Computes win probabilities and exports SHAP parameters for visual charting.
* **`[POST] /api/v1/evaluate-rfp`**: Receives an evaluation request payload (compliance gaps list, budget, base costs), maps the parameters to the internal `AgentState` format, and returns the computed Random Forest decision.
* **`[GET] /compliance/{project_id}/score`**: Returns the compliance score for a specific project. Seeds predefined responses for mock dashboard projects:
  - `nasa-rfp` -> `0.92` (92%)
  - `dod-cloud` -> `0.74` (74%)
  - `who-system` -> `0.45` (45%)
* **`[GET] /go-nogo/{project_id}`**: Retrieves SHAP contribution data to populate the React dashboard charts:
  - Pre-seeded datasets for `nasa-rfp`, `dod-cloud`, and `who-system` supply high-fidelity mock data.
  - Dynamically generated project IDs trigger the random forest classifier on-demand, transforming SHAP feature coordinates into visual structures.

### C. Parsing Routes (`ai_engine/routes/parsing.py`)
Handles parsing and NER extraction.
* **`[POST] /parsing/parse`**: Orchestrates structural document analysis.
  1. Calls `parse_azure_blob_hybrid` to download and parse the file from Azure Storage.
  2. Runs `process_markdown_pipeline` to segment the document into parent and child chunks.
  3. Prepares chunks for vector DB indexing and returns a section count overview.
* **`[POST] /parsing/extract`**: Accepts raw RFP text, routes it to the `ExtractionService`, and returns structured JSON entities.

### D. Proposal Swarm Routes (`ai_engine/routes/proposal.py`)
Starts the multi-agent proposal generation workflow.
* **`[POST] /proposal/generate`**: Runs the LangGraph agent swarm.
  1. **Chunking**: Segments the incoming text into parent-child markdown blocks.
  2. **Indexing**: Indexes child chunks into the Qdrant vector database and BM25 index.
  3. **Swarm Execution**: Initializes the `AgentState` schema and invokes `proposal_swarm_graph.invoke(initial_state)`.
  4. **State Collection**: Compiles the draft outputs, overall scores, and compliance metrics into a structured API response.

---

## 🔍 2. Entity Extraction (`ai_engine/services/extractor_service.py`)

This service parses raw RFP text and extracts structured intelligence points (Named Entity Recognition).

```python
class ExtractionService:
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()
```

### Prompt Mechanics
- **System Prompt**: Configures the LLM to output valid JSON only, without markdown wrapping blocks.
- **Extraction Template**: Instructs the model to extract and categorize entities from the RFP text into five specific keys:
  1. `deadlines_and_dates`: Submission deadlines, Q&A cutoffs, start dates.
  2. `mandatory_verbs`: Sentences containing "must", "shall", or "required".
  3. `kpis_and_metrics`: Performance metrics, SLA requirements, and numeric targets.
  4. `budget_and_pricing`: Budget caps, pricing structures, and financial constraints.
  5. `compliance_standards`: Compliance frameworks (e.g., SOC 2, HIPAA, FedRAMP).

### Content Capping
- **Input Guard**: If the input text is empty, it returns an empty dataset.
- **Context Limit**: Truncates the incoming RFP text to **6,000 characters** (`rfp_text[:6000]`) to protect LLM context windows and control token costs.
