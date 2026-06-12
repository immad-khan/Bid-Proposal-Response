# File: Backend Data Models & Entity Framework Context

This document explains the data models, entity schemas, and relational configurations of the backend storage layer.

---

## 💾 1. Data Models (`backend/Models/DbModels.cs`)

The system maps its domain entities to an relational database (SQLite in development, PostgreSQL in production) using EF Core annotations.

### A. `User` Entity
Represents an authenticated user in the proposal response engine.
- `Id` (`string`, Primary Key): Automatically initialized with a unique UUID string.
- `Username` (`string`): Unique credential label (e.g., `admin`).
- `Email` (`string`): Primary communication handle for notification routing.

### B. `Project` Entity
Represents the target RFP response request.
- `Id` (`string`, Primary Key): Automatically generated UUID.
- `Name` (`string`): The name of the project (e.g., `NASA Jet Propulsion Lab RFQ`).
- `ClientName` (`string`): Target client or federal agency.
- `SubmissionDeadline` (`DateTime`): Expiration target date.
- `SimilarPastWinRate` (`double`): Historical baseline probability metric between `0.0` and `1.0`. Used in the weighted win-prediction model.
- `OwnerId` (`string`): Foreign key mapping the project owner.
- `Members` (`ICollection<ProjectMember>`): Navigational collection for project-level access control.

### C. `ProjectMember` Entity
A join table facilitating many-to-many associations between users and projects.
- `Id` (`string`, Primary Key): Automatically generated UUID.
- `ProjectId` (`string`): Foreign key referencing `Project`.
- `UserId` (`string`): Target user identifier.

### D. `Workspace` Entity
Represents the collaborative editor area linked to a project.
- `Id` (`string`, Primary Key): Corresponds directly to the parent `ProjectId` for simpler path routing.
- `Name` (`string`): Collaborative workspace name.
- `Description` (`string`): Explanatory workspace text.
- `OwnerId` (`string`): The user who created the workspace.
- `CreatedAt` / `UpdatedAt` (`DateTime`): Timestamp tracking metadata.
- `Members` (`ICollection<WorkspaceMember>`): Workspace-level collaborators.
- `Versions` (`ICollection<ProposalVersion>`): Historical draft tracking snapshots.

### E. `WorkspaceMember` Entity
Defines user permissions inside a workspace.
- `Id` (`string`, Key): Automatically generated UUID.
- `WorkspaceId` (`string`): Foreign key referencing the parent `Workspace`.
- `UserId` (`string`): Target user identifier.
- `Role` (`string`): Role mapping:
  - `Admin`: Full write, deletion, and user management rights.
  - `Editor`: Standard write and save-draft operations.
  - `Viewer`: Read-only permissions.
  - `ComplianceOfficer`: Focuses on auditing requirements.

### F. `ProposalVersion` Entity
Stores snapshot history for proposal drafts.
- `Id` (`string`, Key): Automatically generated UUID.
- `WorkspaceId` (`string`): References the workspace.
- `VersionNumber` (`int`): Sequential index (1, 2, 3...) for tracking progress.
- `Content` (`string`): Slate JSON string representing the draft text.
- `CreatedBy` (`string`): Author user ID.
- `CreatedAt` (`DateTime`): Timestamp.
- `Comment` (`string`): A brief explanation of the changes made (e.g., "Added section 1.1 with Ka-band specifications").

### G. `PendingInvite` Entity
Tracks invitations sent to email addresses that do not yet have user accounts.
- `Id` (`string`, Key): Automatically generated UUID.
- `WorkspaceId` (`string`): Target workspace.
- `Email` (`string`): Target email.
- `Role` (`string`): Assigned role if the invitation is accepted.
- `InvitedBy` (`string`): Inviting user.
- `ExpiresAt` (`DateTime`): Expiration timestamp.

---

## 🗄️ 2. Entity Framework Context (`backend/Data/ApplicationDbContext.cs`)

This context configures EF Core database tables and establishes relationships between entities.

### Table Configurations (`DbSet`)
- `Users` -> Maps `User` records.
- `Projects` -> Maps `Project` records.
- `ProjectMembers` -> Join table for project access.
- `Workspaces` -> Maps the collaborative workspaces.
- `WorkspaceMembers` -> Maps workspace membership and roles.
- `ProposalVersions` -> Tracks version history.
- `PendingInvites` -> Maps workspace invitations.

### Relationship Modeling (`OnModelCreating`)
EF Core fluent API configurations establish relational keys:
1. **Workspace Members:**
   ```csharp
   modelBuilder.Entity<WorkspaceMember>()
       .HasOne(m => m.Workspace)
       .WithMany(w => w.Members)
       .HasForeignKey(m => m.WorkspaceId);
   ```
   Specifies that a workspace can have multiple members, and each member is linked via `WorkspaceId`.

2. **Proposal Versions:**
   ```csharp
   modelBuilder.Entity<ProposalVersion>()
       .HasOne(v => v.Workspace)
       .WithMany(w => w.Versions)
       .HasForeignKey(v => v.WorkspaceId);
   ```
   Configures the relationship where a workspace can have multiple versions.

3. **Project Members:**
   ```csharp
   modelBuilder.Entity<ProjectMember>()
       .HasOne(pm => pm.Project)
       .WithMany(p => p.Members)
       .HasForeignKey(pm => pm.ProjectId);
   ```
   Configures the relationship where a project has multiple team members.
