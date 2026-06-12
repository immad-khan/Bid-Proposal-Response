# File: .NET Application Bootstrap & Database Seeding

This document explains the runtime bootstrapper, service registrations, pipeline configurations, and seed database setup defined in `backend/program.cs`.

---

## 🛠️ 1. Service Registrations & Configuration

During startup, the application configures dependency injection containers:

- **Entity Framework Store**: Configures SQLite database connections pointing to the local file `rfp.db`.
- **JWT Middleware Policy**: Declares authorization parameters verifying token lifetimes and keys.
- **Dependency Registrations**:
  - `IAuthService` -> `AuthService` (Singleton)
  - `IBlobStorageService` -> `BlobStorageService` (Scoped)
  - `IProjectManagementService` -> `ProjectManagementService` (Singleton)
  - `IDashboardService` -> `DashboardService` (Scoped)
  - `IWorkspaceService` -> `WorkspaceService` (Scoped)
  - `IEmailService` -> `EmailService` (Scoped)
  - `IDocumentGenerator` -> `DocumentGenerator` (Scoped)
- **HTTP Clients**: Registers generic HttpClients to manage requests sent to the Python AI engine.
- **Request Boundaries**: Limits multipart uploads to a maximum of 100 MB (`MultipartBodyLengthLimit = 104857600`).
- **Access Policies**: Exposes cross-origin resource sharing (CORS) rules allowing the Next.js UI client to connect.

---

## 💾 2. Database Creation & Mock Seeding

On startup, the program executes a seeding block inside a scoped database context provider:

### A. Automatic DB Migration
- Invokes `db.Database.EnsureCreated()` to generate the local SQLite database schema if the database file does not exist.

### B. Seed Records
- **Users**: Seeds an `"admin"` user and a team editor (`"jane_doe"`).
- **Projects**: Seeds three opportunities:
  1. *NASA Deep Space Communication System* (NASA JPL) with an 85% past win rate.
  2. *Pentagon Secure Cloud Migration* (DoD) with a 55% past win rate.
  3. *Global Health Informatics Upgrade* (WHO) with a 25% past win rate.
- **Workspace drafts**: Creates a shared collaborative workspace containing historical versions of document content:
  - **Version 1**: Initial layout draft.
  - **Version 2**: Updated specifications containing technical Ka-band requirements, stored as JSON string arrays matching the Slate editor schema.
