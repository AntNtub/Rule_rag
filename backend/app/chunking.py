from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass


ARTICLE_RE = re.compile(r"(?:^|\n)\s*(第\s*[一二三四五六七八九十百千零〇兩0-9]+\s*條(?:之\s*[0-9一二三四五六七八九十]+)?)")
SPACE_RE = re.compile(r"[ \t\u3000]+")
BLANK_RE = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class TextSpan:
    content: str
    section_id: str | None
    ordinal: int


def normalize_text(text: str) -> str:
    """Normalize encoding and whitespace without deleting legal tokens."""
    text = unicodedata.normalize("NFKC", text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [SPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    return BLANK_RE.sub("\n\n", "\n".join(lines)).strip()


def detect_article(text: str) -> str | None:
    match = ARTICLE_RE.search("\n" + text)
    return SPACE_RE.sub("", match.group(1)) if match else None


def _paragraphs(text: str) -> list[str]:
    normalized = normalize_text(text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", normalized) if block.strip()]
    if len(blocks) == 1:
        blocks = [line.strip() for line in normalized.split("\n") if line.strip()]
    return blocks


def split_into_spans(text: str, max_chars: int = 1200, overlap_chars: int = 180) -> list[TextSpan]:
    if max_chars <= 0 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("Require max_chars > overlap_chars >= 0")

    paragraphs = _paragraphs(text)
    spans: list[TextSpan] = []
    current: list[str] = []
    current_len = 0
    active_article: str | None = None

    def flush(keep_overlap: bool = True) -> None:
        nonlocal current, current_len, active_article
        if not current:
            return
        content = "\n\n".join(current).strip()
        spans.append(TextSpan(content, active_article or detect_article(content), len(spans)))
        if overlap_chars == 0 or not keep_overlap:
            current = []
        else:
            tail: list[str] = []
            tail_len = 0
            for paragraph in reversed(current):
                if tail and tail_len + len(paragraph) + 2 > overlap_chars:
                    break
                tail.insert(0, paragraph)
                tail_len += len(paragraph) + (2 if tail_len else 0)
            current = tail
        current_len = len("\n\n".join(current))

    for paragraph in paragraphs:
        article = detect_article(paragraph)
        if article and current:
            # Article boundaries are hard citation boundaries. Do not carry text
            # from a previous article into the next article's span.
            flush(keep_overlap=False)
        if article:
            active_article = article

        if len(paragraph) > max_chars:
            flush(keep_overlap=False)
            start = 0
            step = max_chars - overlap_chars
            while start < len(paragraph):
                piece = paragraph[start : start + max_chars].strip()
                if piece:
                    spans.append(TextSpan(piece, active_article or detect_article(piece), len(spans)))
                start += step
            current = []
            current_len = 0
            continue

        added = len(paragraph) + (2 if current else 0)
        if current and current_len + added > max_chars:
            flush()
        current.append(paragraph)
        current_len = len("\n\n".join(current))

    flush()
    return spans


def stable_id(*parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]
