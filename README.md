# ProposalCraft AI — Proposal & Architecture Co-Pilot Agent

![ProposalCraft AI Demo](./demo.gif)

**ProposalCraft AI** is an intelligent solution architecture and project management co-pilot built with Google's Agent Development Kit (ADK) and deployed on Google Cloud Agent Platform. It assists project managers, solution architects, and technical sales teams with drafting proposal scope, retrieving proposal records, estimating effort & financial budgets, and generating visual cloud architecture blueprints.

---

## 🌟 Capabilities & Features

### 1. 🧠 Long-Term Memory (Vertex AI Memory Bank)
- Automatically persists and retrieves user/client preferences across sessions.
- Remembers target technology choices (e.g. GKE, Cloud Spanner, BigQuery, Python microservices), engagement models (Fixed Price vs. Time & Materials), and rate card preferences using `PreloadMemoryTool` and post-turn session callbacks.

### 2. 🗄️ Database Operations (Google Cloud Firestore)
- Direct integration with Google Cloud Firestore database collection (`proposals`).
- **`list_proposals`**: Queries active proposals with optional client name and status filters.
- **`get_proposal`**: Fetches full scope details, assumptions, and metadata for specific proposal IDs (e.g. `PROP-101`).
- **`save_proposal`**: Creates or updates proposal records with scope summaries, timelines, and financial estimates.

### 3. 🎨 Visual Architecture Diagram Generation
- **`generate_architecture_diagram`**: Uses Google's `gemini-3.1-flash-lite-image` model in the `global` region to render system architecture blueprints.
- Uploads generated diagram bytes directly to Google Cloud Storage (`proposalcraft-ai-assets-119ccd`) and returns public HTTPS URLs.

### 4. 🎬 Solution Architecture Video Generation
- **`generate_proposal_video`**: Uses Google's `gemini-omni-flash-preview` model in the `global` region to generate animated video walkthroughs of solution blueprints.
- Saves video artifacts to `tool_context` for Playground rendering and uploads raw bytes directly to Google Cloud Storage.

### 5. ⏱️ Effort & Financial Estimation Engine
- **`calculate_proposal_estimation`**: Calculates person-months, phase breakdowns (Discovery, Architecture, Implementation, QA), project timeline in weeks, and total budget in USD based on microservice counts and complexity multipliers.

### 6. 💱 Live Currency Conversion
- **`convert_currency`**: Fetches real-time foreign exchange rates to convert proposal estimates between global currencies (USD, EUR, GBP, CAD, INR).

### 7. 🎛️ A2UI Native Card Components
- Uses `A2uiSchemaManager` (version 0.8) and `BasicCatalog` to emit structured display cards (Cards, Columns, Rows, Text, Images) for rich UI display.

### 8. 🔒 Agent Engine Sandbox Execution
- Executes secure Python sandbox operations using `AgentEngineSandboxCodeExecutor`.

---

## 📋 Planned, Not Yet Implemented

- 📄 **PDF / DOCX Scope Exporter**: Currently exports proposal scope directly as Markdown (`.md`); automated binary document generation is planned for a future release.
- ✍️ **Multi-Signer Client Approval Workflow**: Automated email routing for client signatures is planned for a future release.

---

## 🛠️ Local Development & Setup Instructions

### Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`) authenticated with target GCP project

### 1. Clone & Install Dependencies
```bash
git clone <your-repository-url>
cd proposalcraft-ai
pip install -r requirements.txt
```

### 2. Run Agent Locally via ADK Web UI
```bash
adk web app
```

### 3. Run Custom FastAPI Chat Frontend Locally
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_ID>/locations/<REGION>/reasoningEngines/<ENGINE_ID>"
export AGENT_DIRECTORY="app"
python main.py
```
