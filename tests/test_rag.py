from types import SimpleNamespace

from app.config import Settings
from app.models import ChatRequest
from app.rag import REFUSAL, RagService


class FakeStore:
    def __init__(self, rows):
        self.rows = rows

    def search(self, embedding, top_k):
        return self.rows[:top_k]


class FakeCompletions:
    def __init__(self, answer):
        self.answer = answer

    def create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.answer))]
        )


def fake_client(answer):
    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(answer)))


ROW = {
    "id": "chunk-1",
    "document_id": "doc-1",
    "title": "測試辦法",
    "section_id": "第1條",
    "issued_at": "2026-01-01",
    "source_url": "https://example.edu/policy",
    "content": "第1條 申請人應於七日內辦理。",
    "distance": 0.1,
}


def service(answer, rows=None):
    return RagService(
        Settings(retrieval_top_k=3),
        fake_client(answer),
        FakeStore([ROW] if rows is None else rows),
        embed=lambda _: [0.1, 0.2],
    )


def test_grounded_answer_keeps_only_used_sources() -> None:
    result = service("申請人應於七日內辦理。[S1]").answer(ChatRequest(question="期限？"))
    assert result.grounded is True
    assert [source.citation_id for source in result.sources] == ["S1"]


def test_uncited_answer_is_replaced_with_refusal() -> None:
    result = service("申請人應於七日內辦理。").answer(ChatRequest(question="期限？"))
    assert result.answer == REFUSAL
    assert result.grounded is False
    assert result.warnings


def test_no_retrieval_skips_generation() -> None:
    result = service("unused", rows=[]).answer(ChatRequest(question="校外問題"))
    assert result.answer == REFUSAL
    assert result.sources == []

