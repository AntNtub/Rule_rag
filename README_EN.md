# Clause-Grounded Campus Policy Assistant

[繁體中文](README.md) | [English](README_EN.md)

## Setup and Operation

### 1. Clone the Repository

```powershell
git clone https://github.com/AntNtub/Rule_rag.git
cd Rule_rag
```

### 2. Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

Open `.env` and enter the Azure OpenAI and Azure Cosmos DB endpoints, deployment names, and credentials. API key fields may remain empty when using `az login` or Azure Managed Identity.

`EMBEDDING_DIMENSIONS` must match the output dimensions of the Azure OpenAI embedding deployment.

### 3. Start the Backend

Python 3.12 or later is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

Verify the backend at <http://localhost:8000/health>.

### 4. Ingest Regulation Documents

The ingestion pipeline supports `.txt`, `.md`, `.docx`, and `.pdf`. Place non-public regulations in `data/private/`.

Each document may have a same-name metadata file, such as `leave-policy.pdf.metadata.json`:

```json
{
  "title": "Faculty Leave Regulations",
  "category": "Human Resources",
  "issued_at": "2026-08-01",
  "source_url": "https://example.edu/policies/leave",
  "version": "2026-08-01"
}
```

Preview the document chunks first:

```powershell
$env:PYTHONPATH="backend"
python -m app.cli preview data\private
```

Then create or update the Cosmos DB knowledge base:

```powershell
$env:PYTHONPATH="backend"
python -m app.cli ingest data\private
```

### 5. Start the Frontend

Node.js 22 and pnpm are required.

Open another PowerShell window in the project root:

```powershell
cd frontend
pnpm install
pnpm run dev
```

Open <http://localhost:5173> to use the application.

### 6. Start with Docker (Alternative)

After configuring `.env`, run the following command from the project root:

```powershell
docker compose up --build
```

Open <http://localhost:5173>.

### 7. Run Tests

Backend tests:

```powershell
pip install -r backend\requirements-dev.txt
pytest -q
```

Frontend build test:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm run build
```
