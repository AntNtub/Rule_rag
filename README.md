# Clause-Grounded Campus Policy Assistant

[繁體中文](README.md) | [English](README_EN.md)

這是一個可直接推送到 GitHub 的參考實作，依據論文 *From Policy to Practice: Clause-Grounded Answers with Retrieval-Augmented Generation* 所描述的方法建立：

1. 將大學法規正規化，依段落／章節切成重疊片段。
2. 保留文件名稱、條號、發布日期、分類與來源網址，以支援條款級引用及版本更新。
3. 使用 Azure OpenAI 建立向量，存入 Azure Cosmos DB for NoSQL 的向量索引。
4. 查詢時先做語意檢索，再要求 GPT-4 僅依檢索內容回答、逐項引用，無依據時明確拒答。
5. 提供法規搜尋、條文解釋、法規引導草稿三種模式，以及 Vue 對話管理介面。

> 論文未公開嵌入模型、向量維度、索引類型、top-k、距離門檻、提示詞與完整程式碼。本專案因此將這些值做成環境變數；預設值是可重現的工程選擇，不宣稱是論文原始設定。

## 專案結構

```text
backend/                 FastAPI、文件切分、向量檢索、引用約束生成
frontend/                Vue 3 + TypeScript 使用者介面
data/sample/             僅供格式示範的虛構法規（不可作為真實規定）
tests/                   不需要雲端金鑰的單元測試
docker-compose.yml       本機前後端容器
```

## 安全設定

- `.env`、私有資料、金鑰檔案均已列入 `.gitignore`。
- 儲存庫只提供 `.env.example`，裡面沒有可用憑證。
- 本機可使用 API key；正式部署建議不要設定 key，改用 Azure Managed Identity。
- 請勿將真實校規放入 `data/sample/`；未公開文件請放在已忽略的 `data/private/`。

若金鑰曾經被提交過，單純刪除檔案仍不夠，必須立即在 Azure 旋轉金鑰並清理 Git 歷史。

## 1. Azure 前置作業

需要：

- Azure OpenAI 的 GPT-4 類聊天部署及 embedding 部署。
- 已啟用 NoSQL 向量搜尋的 Azure Cosmos DB 帳戶。
- 若使用 Managed Identity，執行環境須具有呼叫 Azure OpenAI 與讀寫 Cosmos DB 的適當 RBAC 角色。

向量索引只能在建立 Cosmos container 時設定；`EMBEDDING_DIMENSIONS` 必須和 embedding 部署輸出完全一致。若維度或索引策略要更換，請建立新的 container。

## 2. 後端啟動

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

在 `.env` 填入資源端點與部署名稱。若使用 `az login`／Managed Identity，保留兩個 key 欄位為空白。

健康檢查：`GET http://localhost:8000/health`

## 3. 建立知識庫

支援 `.txt`、`.md`、`.docx`、`.pdf`。可以為每個文件建立同名 sidecar，例如 `leave-policy.pdf.metadata.json`：

```json
{
  "title": "教師請假辦法",
  "category": "人事",
  "issued_at": "2026-08-01",
  "source_url": "https://example.edu/policies/leave",
  "version": "2026-08-01"
}
```

先預覽切分，不連線 Azure：

```powershell
$env:PYTHONPATH="backend"
python -m app.cli preview data\sample
```

實際建立／更新 Cosmos DB 知識庫：

```powershell
$env:PYTHONPATH="backend"
python -m app.cli ingest data\private
```

同一文件使用穩定的 `document_id`；再次匯入會 upsert 相同片段。政策版本變更時，請在 sidecar 更新 `version`，再重新匯入。

## 4. 前端啟動

```powershell
cd frontend
pnpm install
pnpm run dev
```

瀏覽 `http://localhost:5173`。開發伺服器會把 `/api` 與 `/health` 代理到 `http://localhost:8000`。

## 5. Docker Compose

```powershell
Copy-Item .env.example .env
docker compose up --build
```

介面位於 `http://localhost:5173`。Compose 會讀取本機 `.env`，但不會把它打包進映像檔。

## API

`POST /api/chat`

```json
{
  "question": "教師請假需要哪些文件？",
  "mode": "explain",
  "history": []
}
```

模式可為 `search`、`explain`、`draft`。回應包含 `answer`、實際被引用的 `sources`、`grounded` 與 `warnings`。後端會拒絕模型捏造不存在的引用標記；若沒有足夠檢索內容，會回傳範圍外訊息而不呼叫生成模型。

## 測試

```powershell
pip install -r backend\requirements-dev.txt
pytest -q
cd frontend
pnpm install --frozen-lockfile
pnpm run build
```

測試不會讀取真實 `.env`，也不會連線 Azure。

## 實作與論文證據的界線

論文明確支持：Azure OpenAI GPT-4、Azure Cosmos DB、Vue、REST API、段落／章節邊界重疊切分、條款中繼資料、檢索後生成、強制引用與範圍外拒答。本文只報告 51 份文件、1,742 個 QA、1,644 答對（94.37%）的人工判定總體結果。

本專案自行補足、但論文未指定：embedding 部署、維度、Cosmos 索引類型、top-k、距離門檻、chunk 字元數、API schema、提示詞與引用驗證。因此若要重現論文數字，仍需要原始 51 份法規、1,742 筆逐題資料、原始部署與評分流程；本儲存庫不聲稱能單獨重現 94.37%。

## 資料與法遵

- 只匯入你有權處理與公開的法規文件。
- 引用連結應指向官方版本；回答不取代承辦單位的正式解釋。
- 正式使用前需保存逐題查詢、檢索片段、模型輸出與人工標註，才能分析檢索、引用及生成錯誤。
