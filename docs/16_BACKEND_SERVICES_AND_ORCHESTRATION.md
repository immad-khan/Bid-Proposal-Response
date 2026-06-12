# File: .NET Services & Orchestration Layer

This document details the business logic services, helper interfaces, and integrations implemented within the `backend/Services/` folder.

---

## 🔐 1. Authentication Service (`AuthService.cs`)

Handles credential verification and authorization tokens.

- **JWT Token Construction**: Configures key parameters (Issuer, Audience, Signing Key) from application configuration.
- **Claim Processing**: Embeds name identifiers and roles (e.g., `"Admin"`) into token payloads.
- **Expiration Controls**: Sets the default lifespan of tokens to 4 hours.

---

## 🗄️ 2. Blob Storage Integrations (`BlobStorageService.cs`)

Manages raw file uploads and downloads.

- **Azure SDK Integration**: Uses `BlobServiceClient` to target the `"rfp-uploads"` storage container.
- **Local Fallback Mode**: If Azure connection strings are missing, it generates mock storage URLs to prevent ingestion failures during development:
  `http://localhost:5000/mock-storage/{Guid}_{FileName}`
- **Generation Export**: Provides methods to upload generated document byte arrays as octet-streams.

---

## 📈 3. Win Probability Dashboard Orchestrator (`DashboardService.cs`)

Integrates data from compliance records, ML models, and historical datasets.

- **Data Querying**: Fetches projects belonging to or shared with the target user.
- **Weighted Analytics Algorithm**: Integrates multiple metrics using a weighted formula:
  $$Probability = Compliance \times 0.5 + GoNoGo \times 0.3 + PastWinRate \times 0.2$$
- **Integration Points**: Calls Python FastAPI routes `/compliance/{projectId}/score` and `/go-nogo/{projectId}` to retrieve SHAP features and compliance metrics.

---

## 📄 4. Document Assembly Engine (`DocumentGenerator.cs`)

Formats final documents.

- **Output Generation**: Transforms raw HTML strings into byte arrays formatted as PDF or DOCX files.
- **Headers & Footers**: Automatically appends metadata, generation timestamps, and structure formats.

---

## 📧 5. Collaborative Invites (`EmailService.cs` & `WorkspaceService.cs`)

Manages team invite workflows.

- **Invite Flow**:
  - Checks if the user is registered in the database.
  - If registered, it adds them as a `WorkspaceMember` with a defined role.
  - If unregistered, it generates a `PendingInvite` record and invokes `EmailService` to send an email invitation.
- **Role Assignment**: Supports roles such as `Admin`, `Editor`, `Viewer`, and `ComplianceOfficer`.
