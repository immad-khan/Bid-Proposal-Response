# File: Backend Controllers & Services Layer

This document breaks down the C# .NET 10 orchestration layer, specifically detailing the Controllers, Services, and Program configurations.

---

## 🏗️ 1. Root Setup: `backend/program.cs`

This is the entrypoint of the ASP.NET Core application. It configures the dependency injection (DI) container, authentication policies, CORS settings, database seeding, and the HTTP request pipeline.

### Active Configuration Keys
- `Jwt:Key`: The symmetric key used to sign and validate tokens (defaults to a static 32-byte security key if not configured in `appsettings.json` or `.env`).
- `Jwt:Issuer` / `Jwt:Audience`: Validates token provenance, ensuring they were issued by and for the correct domains.
- `DefaultConnection`: SQLite database connection string (defaults to `Data Source=rfp.db`).

### Dependency Injection Registrations
- **`ApplicationDbContext`**: Registers EF Core with `UseSqlite`.
- **`IAuthService` / `AuthService`**: Registered as a **Singleton** to handle JWT creation.
- **`IBlobStorageService` / `BlobStorageService`**: Scoped service handling uploads.
- **`IProjectManagementService` / `ProjectManagementService`**: Registered as a **Singleton** for project metadata CRUD operations.
- **`IDashboardService` / `DashboardService`**: Scoped service for win probability mathematical calculations.
- **`IWorkspaceService` / `WorkspaceService`**: Scoped service for versioning, drafting, and inviting.
- **`IEmailService` / `EmailService`**: Scoped service for SMTP notifications.
- **`IDocumentGenerator` / `DocumentGenerator`**: Scoped service for rendering file exports.

### Database Seeding Mechanism
On startup, `program.cs` initiates an active service scope to run EF Core's `db.Database.EnsureCreated()`. If the tables are empty, it seeds:
- **Users**: Creates `admin` and `jane_doe` rows.
- **Projects**: Inserts NASA Deep Space JPL, Pentagon DoD Cloud, and World Health Organization informatics projects.
- **Workspaces**: Inserts the main NASA JPL collaborative workspace, pre-configuring two draft history versions.

---

## 🚪 2. MVC API Controllers (`backend/Controllers/`)

All controllers inherit from `ControllerBase` and carry the `[ApiController]` attribute to enable automatic model state validation and binding.

### A. `AuthController.cs`
Handles user session authorization.
* **`[HttpPost("login")]`**: Receives username and password credentials inside a JSON payload, calls `ValidateUserAsync`, and (if valid) calls `GenerateTokenAsync` to return a signed JWT bearer string.

### B. `ProjectController.cs`
Provides project metadata access.
* **`[HttpGet]`**: Returns a list of active RFP projects.
* **`[HttpPost]`**: Inserts a new project metadata record into the DB.
* **`[HttpGet("{projectId}")]`**: Retrieves details for a specific project.

### C. `WorkspaceController.cs`
The workspace collaboration hub. It carries the `[Authorize]` attribute, meaning requests must present a valid JWT header.
* **`[HttpPost]` (`CreateWorkspace`)**: Extracts the user identifier from the JWT context claims (`ClaimTypes.NameIdentifier` or `ClaimTypes.Name`), then calls `_workspaceService.CreateWorkspaceAsync`.
* **`[HttpGet("{workspaceId}")]`**: Returns the workspace matching `workspaceId`, loading members and historical draft metadata.
* **`[HttpPost("{workspaceId}/draft")]` (`SaveDraft`)**: Receives a Slate JSON string representing the new draft. It extracts user claims, saves the version with an incremental version index, and returns the newly saved `ProposalVersion` object.
* **`[HttpGet("{workspaceId}/versions")]`**: Returns a list of all versions saved for this workspace, ordered newest to oldest.
* **`[HttpGet("version/{versionId}")]`**: Fetches the content of a specific version for comparison.
* **`[HttpPost("{workspaceId}/invite")]`**: Receives an email and role (Admin, Editor, Viewer). Resolves whether the user exists. If yes, binds them to the workspace. If no, sends a pending invite email link.

---

## ⚙️ 3. Implementation Services (`backend/Services/`)

### A. `WorkspaceService.cs`
Orchestrates database changes for the collaboration layer.
* **`CreateWorkspaceAsync(name, description, ownerId, workspaceId)`**: Inserts a new `Workspace` row, then creates a `WorkspaceMember` record mapping the `ownerId` to the `Admin` role.
* **`SaveDraftAsync(workspaceId, content, userId, comment)`**: Finds the target workspace. Queries the database to find the highest existing `VersionNumber` for the workspace, increments it by 1, and saves the new draft content with a timestamp and change comment.
* **`ExportProposalAsync(workspaceId, format)`**: Fetches the latest draft of the workspace, calls `_documentGenerator.GenerateAsync` to convert the Slate HTML/JSON content into a binary file (PDF or DOCX), uploads it via `_blobStorage.UploadGeneratedFileAsync`, and returns the download link.
* **`InviteMemberAsync(workspaceId, email, role, invitedBy)`**: Searches the database for a user with the specified email.
  - If found: Inserts a new `WorkspaceMember` record.
  - If not found: Generates a `PendingInvite` record with a 7-day expiration time and sends an invitation email via `_emailService`.

### B. `DashboardService.cs`
Calculates executive metrics and integrates with the Python AI engine.
* **`GetWinProbabilitiesAsync(userId)`**:
  1. Loads all projects owned by or shared with the user.
  2. For each project, calls `GetComplianceScoreFromAiEngine(projectId)` and `GetGoNoGoFromAiEngine(projectId)` via `IHttpClientFactory` to retrieve metrics from the FastAPI service.
  3. Computes the composite win probability using the weighted formula:
     $$\text{Win Probability} = (\text{Compliance Score} \times 0.5) + (\text{Go/No-Go ML Score} \times 0.3) + (\text{Historical Win Rate} \times 0.2)$$
  4. Returns the sorted list of projects. If the AI Engine is offline, the service catches the exception and falls back to default values to keep the UI operational.
