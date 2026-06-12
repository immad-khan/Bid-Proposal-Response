# File: Frontend Presentation & Dashboard Components

This document describes the design and UI logic of the React / Next.js presentation components in the `frontend/components/` directory.

---

## 🆚 1. Version Differential Component (`VersionDiff.tsx`)

The `VersionDiff` component compares workspace versions at the text line level.

### A. Slate JSON Extraction
- **`slateJsonToText`**: Standard Slate editor content is serialized as JSON structures. The utility parses the string payload, extracts nested leaf text blocks, and joins them using newline characters (`\n`). Non-JSON inputs are caught and processed as plain text.

### B. Longest Common Subsequence (LCS) Algorithm
- **`computeLineDiff`**: Computes the line-by-line diff using dynamic programming.
  - Builds an $O(M \times N)$ DP matrix to find the LCS between `oldLines` and `newLines`.
  - Walks backwards through the matrix to construct a list of `DiffLine` records marked as `added`, `removed`, or `unchanged`.
- **Change Metrics**: Aggregates total added and removed lines to render stats banners.
- **Rendering**: Outputs line numbers next to text blocks, using color styles (emerald for additions, rose for deletions) and indicators (+ or - icons) to denote changes.

---

## 📊 2. Strategic Win Probability Gauge (`WinProbabilityChart.tsx`)

This component displays a win likelihood dashboard using Recharts.

- **Win Likelihood Gauge**: Formats an SVG circle with a dashed stroke length computed using the win probability value ($2\pi R \times [1 - probability]$) to draw a smooth radial gauge.
- **SHAP Feature Attributions**: Pulls the top SHAP features and maps them to human-readable names. It renders a horizontal bar chart where green bars indicate positive attributions and red bars show negative parameters.
- **Financial Alignment Panel**: Evaluates RFP budgets against company costs to project gross margins.

---

## 📋 3. Neo4j Compliance Mapping (`ComplianceMatrix.tsx`)

Pulls requirement listings from the Neo4j Graph database.

- **Status Filters**: Renders button controls to filter items by compliance status: `ALL`, `COMPLIANT`, `PARTIAL`, or `NON_COMPLIANT`.
- **Visual Mapping**: Highlights requirement descriptors with colored badges indicating compliance status, alongside resolution evidence blocks.
- **Direct Requirement Injection**: Includes a quick-add form that allows users to mock and inject new requirements directly into the database.

---

## 🎛️ 4. ML Go/No-Go Viability Sliders (`GoNoGoEvaluator.tsx`)

Allows users to test win scenarios using sliders.

- **Slidable Parameters**: Controls capability matching, budget alignment, delivery schedules, win history, competitive density, and strategic value.
- **Calculations**:
  - **Model Inference**: Submits the slider values to `apiClient.evaluateGoNoGo` to run live Random Forest predictions.
  - **Simulation Fallback**: If the API call fails, it uses a weighted formula to calculate viability:
    $$Score = Cap \times 0.3 + Bud \times 0.2 + Time \times 0.15 + Win \times 0.1 + Comp \times 0.1 + Strat \times 0.15$$
  - **SHAP Explanations**: Renders horizontal bars to visualize feature impacts.

---

## 🗃️ 5. Project Library & Swarm Workspace

### A. Library Index (`Overview.tsx`)
Renders the list of uploaded RFPs. It handles selection actions, dates, and status badges (e.g. `"Ingestion"`, `"Drafting"`, `"Completed"`).

### B. Swarm Orchestrator Workspace (`ProposalSwarmWorkspace.tsx`)
Provides a visual interface for running the multi-agent generation swarm:
- **Pipeline Progress**: Tracks each step (Strategy Plan, RAG Drafting, Guardrails, Scoring) with status colors (e.g. blue animation for processing, emerald for success, rose for errors).
- **Consolidated Outputs**: Combines the planner checklist, gatekeeper warnings, judge scorecard, and drafted section previews into a single workspace view.
