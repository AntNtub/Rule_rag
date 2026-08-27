from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    mode: Literal["search", "explain", "draft"] = "search"
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)


class Source(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    title: str
    section_id: str | None = None
    issued_at: date | None = None
    source_url: str | None = None
    content: str
    distance: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    grounded: bool
    warnings: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    sources: list[Source]


class HealthResponse(BaseModel):
    status: str
    environment: str

