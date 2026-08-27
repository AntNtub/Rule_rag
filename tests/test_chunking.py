from app.chunking import normalize_text, split_into_spans, stable_id


def test_normalize_preserves_numbers_and_legal_phrasing() -> None:
    text = "第 1 條\r\n  申請人  應於  7 日內辦理。"
    assert normalize_text(text) == "第 1 條\n申請人 應於 7 日內辦理。"


def test_split_detects_article_and_overlap() -> None:
    text = "第1條\n總則內容。\n\n補充說明。\n\n第2條\n申請程序。"
    spans = split_into_spans(text, max_chars=24, overlap_chars=6)
    assert len(spans) == 2
    assert spans[0].section_id == "第1條"
    assert spans[-1].section_id == "第2條"
    assert "第1條" not in spans[-1].content


def test_stable_id_is_deterministic() -> None:
    assert stable_id("a", "b") == stable_id("a", "b")
    assert stable_id("a", "b") != stable_id("b", "a")
