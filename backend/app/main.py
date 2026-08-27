from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .dependencies import get_rag_service
from .models import ChatRequest, ChatResponse, HealthResponse, SearchResponse
from .rag import RagService


settings = get_settings()
app = FastAPI(
    title="Clause-Grounded Campus Policy Assistant",
    version="1.0.0",
    description="Retrieval-first university regulation QA with mandatory citations.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.app_env)


@app.post("/api/search", response_model=SearchResponse)
def search(
    request: ChatRequest, service: RagService = Depends(get_rag_service)
) -> SearchResponse:
    try:
        return SearchResponse(sources=service.retrieve(request.question))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="檢索服務目前無法使用。") from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest, service: RagService = Depends(get_rag_service)
) -> ChatResponse:
    try:
        return service.answer(request)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="回答服務目前無法使用。") from exc
