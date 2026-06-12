# File: Frontend API Client & Communication Layer

This document details the architecture, design, and API mapping of the frontend HTTP communication layer in the `frontend/services/` folder.

---

## 🛰️ 1. Centralized HTTP Client (`apiClient.ts`)

The `apiClient` instance acts as the single point of contact for all communication between the Next.js frontend application and the .NET web API gateway.

### A. Environment Configuration
- **API Base URL**: Automatically matches `process.env.NEXT_PUBLIC_API_URL` or falls back to the default development address (`http://localhost:5282`).
- **Authorization Lifecycle**: Maintains a private, in-memory `token` variable. Authentication state is controlled through `setToken(token)` and `clearToken()` methods.

### B. Core Request Dispatcher (`request<T>`)
- **Headers Injection**: Automatically appends the `'Content-Type': 'application/json'` header to outgoing payloads and conditionally attaches the JWT token to the `Authorization` header as a `Bearer` token.
- **Payload Handling**: Converts object bodies into JSON strings for `POST`, `PUT`, `PATCH`, and `DELETE` requests.
- **Error Control**: Evaluates response status; if the response is not within the success range (non-2xx), it throws an error showing the method, URL path, HTTP status, and response details.
- **Parsing**: Automatically detects the response Content-Type and decodes JSON formats, falling back to plain text if necessary.

---

## 🗃️ 2. API Route Mappings

The client exposes type-safe methods matching the .NET controller routes:

### A. Authentication
- **`login(username, password)`**: Sends credentials to `/api/auth/login` and receives the authorized JWT token string.

### B. RFP Document Ingestion
- **`uploadRfp(file)`**: Instantiates a new `FormData` object, appends the PDF document file, and uploads the payload to the ingestion endpoint `/api/RfpUpload/upload`.

### C. Project Management
- **`getProjects()`**: Queries all proposal projects.
- **`getProject(id)`**: Retrieves details for a specific project.
- **`updateProjectStatus(id, status)`**: Submits updates (e.g. `"Ingestion"`, `"Drafting"`, `"Completed"`) to the project status controller.

### D. AI Engine Proxy Actions
- **`getCompliance()`**: Pulls the active compliance matrix.
- **`evaluateGoNoGo(features)`**: Sends capabilities and margin deltas to run Random Forest predictions.
- **`generateProposal(projectId, rfpText)`**: Initiates the LangGraph agent swarm with the target project identifier and raw text.

### E. Win Probability Analytics
- **`getWinProbability()`**: Queries win metrics across all active projects.
- **`getDetailedAnalysis(projectId)`**: Retrieves SHAP contribution vectors and compliance gap summaries.

### F. Collaborative Workspace
- **`createWorkspace(name, description, workspaceId)`**: Prepares collaborative workspace settings.
- **`getWorkspace(workspaceId)`**: Fetches workspace metadata and content drafts.
- **`saveDraft(workspaceId, content, comment)`**: Saves content snapshots with version labels.
- **`getVersionHistory(workspaceId)`**: Queries the list of historical drafts.
- **`exportProposal(workspaceId, format)`**: Sends request to export the document as a PDF or DOCX file.
- **`inviteMember(workspaceId, email, role)`**: Invites collaborators with defined roles.
