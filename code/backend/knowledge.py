"""Local search over the reference project's curriculum and exam excerpts."""

import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

INDEX_FILE = Path(__file__).parent / "resources" / "knowledge_index.json"
INDEX_VERSION = "aqg-2026-05-11"
STOP_TERMS = {"物理", "高中", "初中", "习题", "生成", "一道", "关于", "选择", "出题"}


def _groups(text):
    return re.findall(r"[\u3400-\u9fff]+|[a-z0-9]+", unicodedata.normalize("NFKC", text).lower())


def _terms(text):
    terms = set()
    for group in _groups(text):
        if group.isascii():
            if group.isalpha() and len(group) >= 2:
                terms.add(group)
            continue
        for size in (2, 3):
            terms.update(group[i:i + size] for i in range(len(group) - size + 1))
    return terms - STOP_TERMS


@lru_cache(maxsize=1)
def _load_index():
    fragments = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    entries = []
    frequencies = Counter()
    for fragment in fragments:
        text = f"{fragment.get('section') or ''} {fragment['content']}"
        terms = _terms(text)
        frequencies.update(terms)
        entries.append((fragment, terms, unicodedata.normalize("NFKC", text).lower()))
    return entries, frequencies


def knowledge_status():
    try:
        count = len(_load_index()[0])
    except (OSError, ValueError, TypeError, KeyError):
        count = 0
    return {
        "kb_enabled": bool(count),
        "kb_version": INDEX_VERSION,
        "kb_status": "可用" if count else "不可用",
        "kb_fragments": count,
    }


def retrieve_evidence(knowledge_point, grade, limit=4):
    entries, frequencies = _load_index()
    groups = _groups(knowledge_point)
    phrases = {group for group in groups if not group.isascii() and 2 <= len(group) <= 30} - STOP_TERMS
    query_terms = _terms(knowledge_point)
    weights = {
        term: math.log((len(entries) + 1) / (frequencies[term] + 1))
        for term in query_terms if frequencies[term]
    }
    high_school = grade.startswith(("高", "普通高中"))
    middle_school = grade.startswith(("初", "七", "八", "九"))
    candidates = []
    for fragment, terms, text in entries:
        source = fragment["source_file"]
        curriculum = fragment.get("doc_type") == "课标"
        if high_school and curriculum and "义务教育" in source:
            continue
        if middle_school and (not curriculum or "普通高中" in source):
            continue
        matches = terms & weights.keys()
        phrase_length = max((len(phrase) for phrase in phrases if phrase in text), default=0)
        if phrase_length == 0 and not any(len(term) >= 3 for term in matches):
            continue
        score = math.fsum(weights[term] for term in matches) + 3 * phrase_length
        candidates.append((score * (1.1 if curriculum else 1), fragment))
    candidates.sort(key=lambda item: item[0], reverse=True)
    if not candidates:
        return []
    threshold = candidates[0][0] * 0.45
    return [
        {
            "source": fragment["source_file"].replace("\\", "/"),
            "fragment_id": fragment["chunk_id"],
            "index_version": INDEX_VERSION,
            "content": fragment["content"],
        }
        for score, fragment in candidates[:limit]
        if score >= threshold
    ]
