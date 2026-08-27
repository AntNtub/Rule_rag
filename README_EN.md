# Clause-Grounded Campus Policy Assistant

[繁體中文](README.md) | [English](README_EN.md)


1. Normalize university regulations and split them into overlapping chunks along paragraph and section boundaries.
2. Preserve document titles, article identifiers, issue dates, categories, and source URLs for clause-level citations and versioned updates.
3. Generate embeddings with Azure OpenAI and store them in an Azure Cosmos DB for NoSQL vector index.
4. Retrieve semantically relevant clauses before asking GPT-4 to answer strictly from those sources, cite each substantive claim, and explicitly refuse unsupported questions.
5. Provide three modes—regulation search, plain-language explanation, and regulation-guided drafting—through a Vue conversation interface.

> The paper does not disclose the embedding model, vector dimensions, index type, top-k value, distance threshold, prompts, or complete source code. This implementation therefore exposes those values as environment variables. Its defaults are reproducible engineering choices and are not claimed to be the paper's original settings.

## Project Structure

```text
backend/                 FastAPI, document chunking, vector retrieval, and citation-constrained generation
frontend/                Vue 3 + TypeScript user interface
data/sample/             Fictional regulations for format demonstration only
tests/                   Unit tests that do not require cloud credentials
docker-compose.yml       Local frontend and backend containers
```

## Security

- `.env`, private data, and key files are excluded through `.gitignore`.
- The repository includes only `.env.example`, which contains no usable credentials.
- API keys may be used for local development. For production, leave the key fields empty and use Azure Managed Identity instead.
- Do not place real regulations in `data/sample/`. Put non-public documents in the ignored `data/private/` directory.

If a credential has ever been committed, deleting it in a later commit is not sufficient. Rotate the credential in Azure immediately and remove it from the Git history.

## 1. Azure Prerequisites

You need:

- An Azure OpenAI GPT-4-class chat deployment and an embedding deployment.
- An Azure Cosmos DB account with vector search for NoSQL enabled.
- Appropriate RBAC roles for Azure OpenAI inference and Cosmos DB read/write access when using Managed Identity.

The vector policy and index are configured when the Cosmos DB container is created. `EMBEDDING_DIMENSIONS` must exactly match the output dimensions of the embedding deployment. Create a new container if you need to change the dimensions or vector-index configuration.

## 2. Start the Backend

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

Add the Azure resource endpoints and deployment names to `.env`. When using `az login` or Managed Identity, leave both key fields empty.

Health check: `GET http://localhost:8000/health`

## 3. Build the Knowledge Base

The ingestion pipeline supports `.txt`, `.md`, `.docx`, and `.pdf` files. Each document may have a same-name metadata sidecar, such as `leave-policy.pdf.metadata.json`:

```json
{
  "title": "Faculty Leave Regulations",
  "category": "Human Resources",
  "issued_at": "2026-08-01",
  "source_url": "https://example.edu/policies/leave",
  "version": "2026-08-01"
}
```

Preview document chunks without connecting to Azure:

```powershell
$env:PYTHONPATH="backend"
python -m app.cli preview data\sample
```

Create or update the Cosmos DB knowledge base:

```powershell
$env:PYTHONPATH="backend"
python -m app.cli ingest data\private
```

Each document receives a stable `document_id`, and repeated ingestion upserts matching chunks. When a policy changes, update the `version` field in its metadata sidecar before ingesting it again.

## 4. Start the Frontend

```powershell
cd frontend
pnpm install
pnpm run dev
```

Open `http://localhost:5173`. The development server proxies `/api` and `/health` to `http://localhost:8000`.

## 5. Docker Compose

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The interface is available at `http://localhost:5173`. Docker Compose reads the local `.env` file but does not copy it into either image.

## API

`POST /api/chat`

```json
{
  "question": "Which documents are required for faculty leave?",
  "mode": "explain",
  "history": []
}
```

`mode` accepts `search`, `explain`, or `draft`. The response contains `answer`, the actually cited `sources`, `grounded`, and `warnings`. The backend rejects source markers that were not supplied to the model. If retrieval returns insufficient evidence, it produces an out-of-scope response without calling the generation model.

## Tests

```powershell
pip install -r backend\requirements-dev.txt
pytest -q
cd frontend
pnpm install --frozen-lockfile
pnpm run build
```

The tests do not load a populated `.env` file or connect to Azure.


## Data Governance and Compliance

- Ingest only regulation documents that you are authorized to process and publish.
- Citation links should point to official versions. Generated answers do not replace an institution's formal interpretation.
- Before production use, retain item-level queries, retrieved passages, model outputs, and human annotations so retrieval, citation, and generation errors can be analyzed independently.

