import re
import html
from collections import Counter


def clean_text(text: str) -> str:
    return text.strip()


def count_keyword(text: str, keyword: str) -> int:
    if not keyword:
        return 0
    return text.count(keyword)


def korean_char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def split_sentences(text: str):
    sentences = re.split(r"(?<=[.!?。！？\n])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def get_intro(text: str) -> str:
    sentences = split_sentences(text)
    return " ".join(sentences[:5])[:500]


def get_ending(text: str) -> str:
    return text[-500:] if len(text) > 500 else text


def detect_title_type(title: str, title_types: dict):
    found = []
    for title_type, pattern in title_types.items():
        if re.search(pattern, title):
            found.append(title_type)
    return found


def highlight_text(text: str, phrases):
    safe = html.escape(text)
    unique_phrases = sorted(set([p for p in phrases if p]), key=len, reverse=True)

    for phrase in unique_phrases:
        escaped_phrase = html.escape(phrase)
        safe = safe.replace(
            escaped_phrase,
            f"<mark style='background-color:#fff3a3; padding:2px 4px; border-radius:4px;'>{escaped_phrase}</mark>"
        )
    return safe


def find_repeated_words(text: str, min_count: int = 8):
    words = re.findall(r"[가-힣A-Za-z0-9]{2,}", text)
    common = Counter(words).most_common(20)
    stop_words = {
        "합니다", "있습니다", "있는", "것이", "수", "그리고", "하지만",
        "때문에", "경우", "대한", "위해", "있어", "있고", "하는"
    }
    return [(word, count) for word, count in common if count >= min_count and word not in stop_words]
