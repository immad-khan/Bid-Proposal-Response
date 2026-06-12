# File: `frontend/app/page.tsx` — Main Application Shell

This is the **root client component** of the entire Next.js application. Every feature, view, and interaction is managed or initialized here.

---

## Directive & Imports

```ts
'use client';
```
Marks this as a React Client Component so it can use browser APIs, hooks, and event handlers.

### React Hooks
| Hook | Purpose |
|---|---|
| `useState` | Creates reactive local state variables |
| `useEffect` | Runs side effects (auto-login, data fetch) on mount |
| `useCallback` | Memoizes functions to prevent unnecessary re-renders |

### Third-Party Imports
- **`framer-motion`** (`motion`, `AnimatePresence`): Smooth animation wrappers for entering/leaving elements.
- **`lucide-react`**: Icon library providing SVG icons like `Upload`, `Loader2`, `CheckCircle2`, etc.
- **`WinProbabilityDashboard`**: The executive overview chart component.
- **`WinProbabilityChart`**: Per-project detailed chart.
- **`InlineDocumentEditor`**: The Slate.js rich text editor.
- **`VersionDiff`**: The version comparison visualizer.
- **`apiClient`**: The centralized HTTP fetch service from `services/apiClient.ts`.

---

## TypeScript Interfaces

### `Project`
```ts
interface Project {
  id: string;          // unique project ID, e.g. "nasa-rfp"
  name: string;        // display name
  clientName?: string; // optional client label
  rfpBlobUrl: string;  // Azure Blob Storage URL to the uploaded PDF
  createdAt: string;   // ISO timestamp
  status: string;      // "Created", "Processing", "Completed"
}
```

---

## Animation Variant Constants

```ts
const containerVariants: any = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.2 } }
};
```
Used by Framer Motion to animate a parent container — children appear sequentially with a 0.1s stagger.

```ts
const itemVariants: any = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 15 } }
};
```
Each child item slides up 20px with a spring physics animation.

```ts
const pulseRing: any = {
  scale: [1, 1.2, 1],
  opacity: [0.5, 0, 0.5],
  transition: { duration: 2, repeat: Infinity, ease: "easeInOut" }
};
```
Repeating pulse keyframe animation used on the upload zone indicator dot.

---

## State Variables

| Variable | Type | Purpose |
|---|---|---|
| `viewMode` | `'upload' \| 'dashboard'` | Controls the top-level view: RFP upload console vs. executive dashboard |
| `file` | `File \| null` | Currently selected PDF/DOCX file for upload |
| `status` | `string` | Human-readable status message displayed in the status bar |
| `statusType` | `'idle' \| 'loading' \| 'success' \| 'error'` | Controls color + icon of the status indicator |
| `projects` | `Project[]` | Array of all active projects from backend |
| `activeProjectId` | `string \| null` | Currently selected project ID |
| `isDragging` | `boolean` | True when a file is being dragged over the drop zone |
| `uploadProgress` | `number` | 0–100 progress bar value during file upload |
| `activeTab` | `'analytics' \| 'editor' \| 'versions' \| 'collab'` | Active tab inside the project workspace panel |
| `analysis` | `any \| null` | Detailed win probability + SHAP data for active project |
| `workspace` | `any \| null` | Workspace object (members, version info) for active project |
| `versions` | `any[]` | List of draft snapshots for the active workspace |
| `isWorkspaceLoading` | `boolean` | Loading state for workspace fetch |
| `isAnalysisLoading` | `boolean` | Loading state for analysis fetch |
| `isActionRunning` | `boolean` | Blocks buttons during async actions |
| `inviteEmail` | `string` | Controlled input for team invite email address |
| `inviteRole` | `string` | Controlled select for invite role (`"Editor"` default) |
| `inviteMsg` | `string` | Feedback message after invite send |
| `compareVer1/Ver2` | `string` | Version IDs selected for diff comparison |
| `ver1Content/ver2Content` | `string` | Fetched Slate JSON content for each selected version |
| `showDiff` | `boolean` | Whether the diff viewer panel is rendered |

---

## Core Functions

### `useEffect` — Auto-Login on Mount
```ts
useEffect(() => {
  const autoLogin = async () => {
    const authData = await apiClient.login('admin', 'password');
    if (authData?.token) apiClient.setToken(authData.token);
  };
  autoLogin();
}, []);
```
On component mount, silently logs in as `admin` and stores the JWT token in the `apiClient` singleton so all subsequent requests are authenticated.

---

### `fetchProjects` (`useCallback`)
Calls `apiClient.getProjects()` and populates the `projects` state. If the backend is offline, it falls back to a **hardcoded mock list** of 2 demo projects:
- `nasa-rfp` — NASA Deep Space Communication System
- `dod-cloud` — Pentagon Secure Cloud Migration

Auto-selects the first project in the list if none is selected.

---

### `loadProjectData(projectId)` (`useCallback`)
Runs in two parallel tracks when a project is selected:

**Track 1 — Win Probability Analysis:**
- Calls `apiClient.getDetailedAnalysis(projectId)`.
- On failure, generates a mock analysis object with hardcoded values per project ID (82% win for NASA, 55% for DoD, 25% for WHO).

**Track 2 — Workspace & Version History:**
- Calls `apiClient.getWorkspace(projectId)` to load members/workspace info.
- Calls `apiClient.getVersionHistory(projectId)` to populate version list.
- Pre-selects the two most recent versions in `compareVer1` and `compareVer2` dropdowns.

---

### `handleCreateWorkspace()`
- Finds the active project object.
- Calls `apiClient.createWorkspace(name, description, projectId)` to create a new workspace linked to the project.
- Immediately creates a version 1 draft by calling `apiClient.saveDraft()` with a default Slate JSON paragraph.
- Reloads the project data after creation.

---

### `handleSaveWorkspaceDraft(contentJson, comment)`
- Called by the `InlineDocumentEditor` when auto-save fires.
- Calls `apiClient.saveDraft(workspaceId, contentJson, comment)`.
- Refreshes the `versions` state and updates `workspace.currentVersion`.

---

### `handleCompareVersions()`
- Fetches full content for both selected versions via `apiClient.getVersion(id)`.
- Stores results in `ver1Content` and `ver2Content`.
- Sets `showDiff = true` to render the `<VersionDiff />` component.

---

### `handleExport(format)`
- Calls `apiClient.exportProposal(projectId, format)` where format is `"pdf"` or `"docx"`.
- Opens the returned `downloadUrl` in a new browser tab.

---

### `handleInvite(e)`
- Prevents default form submit.
- Calls `apiClient.inviteMember(workspaceId, inviteEmail, inviteRole)`.
- Displays success/failure message in `inviteMsg`.
- Reloads project data after 2 seconds to refresh member list.

---

### Drag-and-Drop Handlers
| Function | Trigger | Action |
|---|---|---|
| `handleDragOver(e)` | File dragged over zone | `e.preventDefault()`, sets `isDragging = true` |
| `handleDragLeave(e)` | File leaves zone | Sets `isDragging = false` |
| `handleDrop(e)` | File dropped | Validates `.pdf` or `.docx` extension, sets `file` state |

---

### `handleUpload()`
1. Guards against no file selected.
2. Sets `statusType = 'loading'` and starts a fake progress interval (`setInterval`) that increments `uploadProgress` by a random 0–15% every 300ms (capped at 90%).
3. Calls `apiClient.uploadRfp(file)`.
4. On success: clears interval, sets progress to 100%, displays job ID in status.
5. After 500ms, calls `fetchProjects()` to refresh the list.
6. On failure: clears interval, resets progress to 0, shows error.

---

### `clearFile()`
Resets `file`, `status`, `statusType`, and `uploadProgress` to default idle states.

---

### `getStatusIcon()` / `getStatusColor()`
Switch functions that return the correct Lucide icon component or Tailwind CSS class string based on `statusType`:
- `loading` → spinning `Loader2` icon, cyan colors
- `success` → `CheckCircle2` icon, emerald colors
- `error` → `AlertCircle` icon, rose colors

---

## Render Output (JSX Structure)

| Section | Description |
|---|---|
| Animated Background | 3 fixed blurred gradient orbs (cyan, violet, blue) that `animate-pulse` |
| Grid Overlay | Subtle CSS grid pattern overlay at 2% opacity |
| Header | Logo + nav tabs for "RFP Ingestion" and "Executive Dashboard" |
| Upload Panel | Drag-drop zone + file list + upload progress bar |
| Project List | Sidebar cards for each project, click to select |
| Workspace Tabs | Four tabs: Analytics, Editor, Versions, Collaboration |
| Analytics Tab | Renders `WinProbabilityChart` + compliance gap list + budget breakdown |
| Editor Tab | Renders `InlineDocumentEditor` with `onSave` = `handleSaveWorkspaceDraft` |
| Versions Tab | Lists version history, two dropdowns + "Compare" button, renders `VersionDiff` |
| Collaboration Tab | Member list + invite form |
| Executive Dashboard View | Renders `WinProbabilityDashboard` global project overview |
