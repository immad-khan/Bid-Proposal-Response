# File: Backend Integration Controllers

This document explains the backend API controllers that integrate the .NET application with the FastAPI AI engine.

---

## 🧭 1. Compliance Controller (`backend/Controllers/ComplianceController.cs`)

This controller retrieves compliance data and evaluates bid metrics from the AI engine.

```csharp
[ApiController]
[Route("api/[controller]")]
public class ComplianceController : ControllerBase
```

### Endpoints

#### A. `[HttpGet("matrix")]` (`GetMatrix`)
Retrieves the requirements compliance matrix.
- **Python Engine Routing**: Queries the FastAPI endpoint `{PythonEngine:Url}/compliance/matrix`.
- **Response**: Returns the deserialized JSON compliance grid mapping requirements to supporting evidence.
- **Error Handling**: Logs failures and returns standard HTTP status codes (e.g. 500) if the AI engine is unreachable.

#### B. `[HttpPost("go-nogo")]` (`EvaluateGoNoGo`)
Evaluates win probability metrics for a set of features.
- **Request Body**: Accepts a dictionary of feature names and float values:
  `Dictionary<string, float> features`
- **Python Engine Routing**: Forwards the payload to `{PythonEngine:Url}/compliance/evaluate-bid`.
- **Response**: Returns the prediction output containing probability and decision results.

---

## 📝 2. Proposal Controller (`backend/Controllers/ProposalController.cs`)

This controller exposes endpoints to trigger the multi-agent proposal generation swarm.

### Endpoint: `[HttpPost("generate")]` (`GenerateProposal`)
- **Payload Schema**:
  ```csharp
  public class ProposalRequest
  {
      public string project_id { get; set; }
      public string rfp_text { get; set; }
  }
  ```
- **Proxy Timeout Config**: Configures the HTTP client with a **10-minute timeout** (`TimeSpan.FromMinutes(10)`) to accommodate the processing time of the LangGraph agent swarm.
- **Python Engine Routing**: Proxies the payload as JSON to `{PythonEngine:Url}/proposal/generate`.
- **Response**: Returns the generated drafts on success.

---

## 📤 3. RFP Upload Controller (`backend/Controllers/RfpUploadController.cs`)

This controller manages file uploads, initiates parsing, and tracks project creation.

### Endpoint: `[HttpPost("upload")]` (`UploadRfp`)
- **Request Type**: Accepts `IFormFile file` from a multi-part form upload.

#### Execution Pipeline:
1. **Validation**: Verifies the file stream exists and has a non-zero length.
2. **Blob Storage**: Opens the file read stream and uploads it to Azure Blob Storage via `_blobStorageService.UploadFileAsync`.
3. **Project Creation**: Uses `_projectManagementService.CreateProjectAsync` to register a new project entity using the filename (sans extension) and the Azure Blob URL.
4. **AI Parsing Trigger**: Configures a **5-minute timeout** HTTP client and sends the tracking payload to the Python engine's `/parsing/parse` endpoint:
   ```json
   {
       "jobId": "project-uuid",
       "blobUrl": "azure-blob-storage-link",
       "filename": "proposal.pdf"
   }
   ```
5. **State Updates**:
   - On success: Transitions project status to `"ParsingStarted"`.
   - On failure: Transitions project status to `"ParsingFailed"`.
