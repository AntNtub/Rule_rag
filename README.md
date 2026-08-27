# Clause-Grounded Campus Policy Assistant

[繁體中文](README.md) | [English](README_EN.md)

## 操作流程

### 1. 下載專案

```powershell
git clone https://github.com/AntNtub/Rule_rag.git
cd Rule_rag
```

### 2. 設定環境變數

```powershell
Copy-Item .env.example .env
```

開啟 `.env`，填入 Azure OpenAI 與 Azure Cosmos DB 的端點、部署名稱及憑證。若使用 `az login` 或 Azure Managed Identity，API key 欄位可以留空。

`EMBEDDING_DIMENSIONS` 必須與 Azure OpenAI embedding 部署的輸出維度一致。

### 3. 啟動後端

需要 Python 3.12 或更新版本。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

確認後端正常：<http://localhost:8000/health>

### 4. 匯入法規文件

支援 `.txt`、`.md`、`.docx` 與 `.pdf`。請將不公開的法規放入 `data/private/`。

每份文件可以搭配同名的 metadata 檔案，例如 `leave-policy.pdf.metadata.json`：

```json
{
  "title": "教師請假辦法",
  "category": "人事",
  "issued_at": "2026-08-01",
  "source_url": "https://example.edu/policies/leave",
  "version": "2026-08-01"
}
```

先預覽文件切分結果：

```powershell
$env:PYTHONPATH="backend"
python -m app.cli preview data\private
```

確認後建立或更新 Cosmos DB 知識庫：

```powershell
$env:PYTHONPATH="backend"
python -m app.cli ingest data\private
```

### 5. 啟動前端

需要 Node.js 22 與 pnpm。

在專案根目錄另開一個 PowerShell 視窗：

```powershell
cd frontend
pnpm install
pnpm run dev
```

開啟 <http://localhost:5173> 即可使用。

### 6. 使用 Docker 啟動（替代方式）

完成 `.env` 設定後，在專案根目錄執行：

```powershell
docker compose up --build
```

開啟 <http://localhost:5173>。

### 7. 執行測試

後端測試：

```powershell
pip install -r backend\requirements-dev.txt
pytest -q
```

前端建置測試：

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm run build
```
