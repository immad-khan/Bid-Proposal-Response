# File: .NET Entity Models & Data Schemas

This document defines the C# object schemas, database contexts, and Data Transfer Objects (DTOs) used in the `backend/Models/` and `backend/Data/` directories.

---

## 🗃️ 1. Database Entity Models (`DbModels.cs`)

These models map directly to SQLite / PostgreSQL database tables via Entity Framework Core:

### A. User Entity (`User`)
- Tracks system actors who can own or collaborate on proposals.
- Fields: `Id` (GUID string), `Username`, `Email`.

### B. Project Entity (`Project`)
- Represents an RFP proposal opportunity.
- Fields: `Id` (GUID string), `Name` (RFP name), `ClientName` (target client), `SubmissionDeadline`, `SimilarPastWinRate` (used in fallback probability calculations), `OwnerId` (creator of the proposal record), `Members` (navigational collection of workspace collaborators).

### C. Workspace Entity (`Workspace`)
- Orchestrates the cooperative drafting stage for generated documents.
- Fields: `Id` (GUID string), `Name`, `Description`, `OwnerId`, `CreatedAt`, `UpdatedAt`, `Members` (navigational collection of collaborators), `Versions` (navigational collection of draft snapshots).

### D. Collaboration Entities (`WorkspaceMember` & `ProjectMember`)
- Maps multi-tenant roles to individual workspaces and projects.
- Fields: `Id`, `WorkspaceId` (foreign key), `UserId` (system user), `Role` (supports roles like `"Admin"`, `"Editor"`, `"Viewer"`, `"ComplianceOfficer"`).

### E. Proposal Version Entity (`ProposalVersion`)
- Tracks incremental draft saves for diff generation.
- Fields: `Id`, `WorkspaceId` (foreign key), `VersionNumber` (integer version counter), `Content` (JSON/HTML document text), `CreatedBy` (author ID), `CreatedAt` (timestamp), `Comment` (commit comment).

### F. Pending Invitations (`PendingInvite`)
- Holds invitations for unregistered users.
- Fields: `Id`, `WorkspaceId`, `Email`, `Role`, `InvitedBy` (sender), `ExpiresAt` (lifespan of 7 days).

---

## 📨 2. Data Transfer Objects (DTOs)

Used to parse requests and structure responses.

### A. Win Probability Models (`DashboardDto.cs`)
- **`WinProbabilityDto`**: Encapsulates calculated win probabilities for project lists.
- **`ShapFeatureDto`**: Contains SHAP feature contributions (includes parameter name, raw value, and computed attribution contribution).
- **`WinProbabilityDetailDto`**: Provides detail view metrics (includes budget, base cost, and compliance gaps).

### B. Pipeline Models (`Dto.cs`)
- **`ProposalProjectDto`**: Returns metadata for active project folders.
- **`RfpUploadResponseDto`**: Confirms file parsing and returns the tracking job ID.

---

## ⚙️ 3. Entity Framework Data Context (`ApplicationDbContext.cs`)

Coordinates database access and configures relationships:
- Sets up database sets (`DbSet`) for all database models.
- Configures foreign key constraints for workspace members, project members, and document versions.
