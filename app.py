import os
import re
import html
import json
import requests
from collections import Counter
from urllib.parse import urlparse

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="달로썸 원고 검수기 v2",
    page_icon="📝",
    layout="wide",
)

# =============================
# 기본 데이터
# =============================

PURPOSES = [
    "포트폴리오용 샘플 원고",
    "마케팅 회사 테스트 원고",
    "실제 병원 광고 원고",
    "실제 법률 광고 원고",
    "일반 정보성 원고",
]

FIELDS = [
    "에스테틱 / 피부관리",
    "병원 / 의료",
    "법률",
    "기타 전문업종",
]

SOURCE_TYPES = [
    "자동분류",
    "공식기관/법령/학회/장비 공식자료",
    "의사/변호사 직접 콘텐츠",
    "병원/법무법인 공식 홈페이지·블로그",
    "일반 블로그/카페/후기",
    "광고/출처불명/후기성 자료",
]

AI_SMELL_PATTERNS = {
    "메타 문장": [
        "설명합니다", "안내합니다", "마무리합니다", "알아보겠습니다",
        "정리해보겠습니다", "살펴보겠습니다", "이번 글에서는",
        "이 글에서는", "오늘은"
    ],
    "AI식 반복 표현": [
        "중요합니다", "필요합니다", "도움이 됩니다", "도움이 될 수 있습니다",
        "검토할 수 있습니다", "고려할 수 있습니다", "확인하는 것이 좋습니다",
        "첫걸음", "단순히"
    ],
    "강한 광고 표현": [
        "100%", "무조건", "반드시", "확실하게", "완벽하게",
        "최고", "유일", "1위", "즉시", "단기간"
    ],
}

MEDICAL_RISK_PATTERNS = [
    "완치", "치료됩니다", "치료가 됩니다", "효과 보장", "부작용 없음",
    "통증 없음", "흉터 없음", "100%", "무조건 좋아집니다",
    "반드시 좋아집니다", "병변이 사라졌습니다", "재발 없음",
    "환자 후기", "치료 경험담", "전후사진", "비포애프터",
    "무조건 개선", "확실한 개선", "즉각 개선"
]

LEGAL_RISK_PATTERNS = [
    "승소율", "성공률", "무혐의율", "무조건 승소", "반드시 승소",
    "무조건 해결", "100% 승소", "패소 시 환불", "환불 보장",
    "무료상담 쿠폰", "최저가", "대형 로펌보다", "전관",
    "판사 출신", "검사 출신", "최고의 변호사", "유일한 해결사",
    "무조건 감형", "반드시 무혐의"
]

GLOSSARY_TERMS = {
    "에스테틱 / 피부관리": [
        "피부 턴오버 주기", "유수분 균형", "피부 장벽", "각질",
        "피지", "속건조", "복합성 피부"
    ],
    "병원 / 의료": [
        "비급여", "고주파", "초음파", "HIFU", "RF",
        "콜라겐", "염증", "재생"
    ],
    "법률": [
        "내용증명", "지급명령", "가압류", "소멸시효",
        "소액사건", "기망행위", "불기소", "무혐의"
    ],
    "기타 전문업종": [],
}

TITLE_TYPES = {
    "숫자형": r"\d|[0-9]|가지|단계|분|개월|년",
    "질문형": r"\?|까요|왜|무엇|어떻게|언제",
    "긴급성형": r"지금|오늘|늦기 전|놓치면|반드시|꼭",
    "궁금증형": r"이유|비밀|차이|진짜|따로",
    "반전형": r"오해|예상과 달리|뜻밖|다르다",
    "상황공감형": r"고민|힘든|걱정|불안|포기|찾고 있다면",
}

OFFICIAL_DOMAINS = [
    "law.go.kr", "scourt.go.kr", "moj.go.kr", "moleg.go.kr",
    "mohw.go.kr", "kca.go.kr", "korea.kr", "nhis.or.kr",
    "koreanbar.or.kr", "kdca.go.kr", "gov.kr", "hira.or.kr",
    "kuksiwon.or.kr", "kda.or.kr", "kams.or.kr"
]

LOW_TRUST_DOMAINS = [
    "cafe.naver.com", "kin.naver.com", "blog.naver.com",
    "tistory.com", "brunch.co.kr"
]


# =============================
# 유틸 함수
# =============================

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


def detect_title_type(title: str):
    found = []
    for title_type, pattern in TITLE_TYPES.items():
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
        "합니다", "있습니다", "있는", "것이", "그리고", "하지만",
        "때문에", "경우", "대한", "위해", "있어", "있고", "하는"
    }
    return [(word, count) for word, count in common if count >= min_count and word not in stop_words]


def get_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except Exception:
        return ""


def get_secret(name: str):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, "")


# =============================
# 자동 검색 / 출처 등급
# =============================

def build_search_queries(keyword, topic, field, purpose):
    base = " ".join([x for x in [keyword, topic] if x]).strip()
    if not base:
        base = keyword or topic or ""

    queries = []

    if field == "법률":
        queries = [
            f"{base} 법제처 생활법령",
            f"{base} 법원 지급명령 소액사건 가압류",
            f"{base} 변호사 칼럼",
        ]
    elif field in ["병원 / 의료", "에스테틱 / 피부관리"]:
        queries = [
            f"{base} 피부과 전문의 설명",
            f"{base} 공식 자료 관리 방법",
            f"{base} 주의사항 부작용",
        ]
    else:
        queries = [
            f"{base} 공식 자료",
            f"{base} 전문가 설명",
            f"{base} 주의사항",
        ]

    # 중복 제거
    seen = set()
    unique = []
    for q in queries:
        if q and q not in seen:
            unique.append(q)
            seen.add(q)
    return unique


def tavily_search(query, max_results=5):
    api_key = get_secret("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY가 설정되지 않았습니다.")

    url = "https://api.tavily.com/search"
    payload = {
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_raw_content": False,
        "max_results": max_results,
    }

    # 최신 Tavily 방식: Authorization Bearer 헤더
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)

    # 일부 구버전 계정/환경 호환: body에 api_key 포함 재시도
    if response.status_code in [401, 403]:
        payload_with_key = dict(payload)
        payload_with_key["api_key"] = api_key
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload_with_key, timeout=30)

    response.raise_for_status()
    data = response.json()
    return data.get("results", [])


def infer_source_type(title, url, content, field):
    domain = get_domain(url)
    text = f"{title} {url} {content}"

    if any(d in domain for d in OFFICIAL_DOMAINS):
        return "공식기관/법령/학회/장비 공식자료"

    if any(d in domain for d in LOW_TRUST_DOMAINS):
        if "후기" in text or "리뷰" in text:
            return "일반 블로그/카페/후기"
        return "일반 블로그/카페/후기"

    expert_words = ["의사", "전문의", "원장", "변호사", "변호사법", "대한변호사협회", "칼럼"]
    if any(word in text for word in expert_words):
        return "의사/변호사 직접 콘텐츠"

    official_blog_words = ["병원", "의원", "클리닉", "법무법인", "법률사무소"]
    if any(word in text for word in official_blog_words):
        return "병원/법무법인 공식 홈페이지·블로그"

    risky_words = ["후기", "경험담", "리뷰", "협찬", "광고"]
    if any(word in text for word in risky_words):
        return "일반 블로그/카페/후기"

    return "일반 블로그/카페/후기"


def grade_source(title: str, url: str, source_type: str, field: str, memo: str):
    domain = get_domain(url)
    text = f"{title} {url} {memo}"

    grade = "C"
    warning = "일반 참고자료입니다. 핵심 근거로 쓰기보다는 보조 참고용으로 사용하세요."

    if any(d in domain for d in OFFICIAL_DOMAINS):
        grade = "A"
        warning = "공식기관/법령 계열 자료로 핵심 근거로 활용하기 좋습니다."
    elif source_type == "공식기관/법령/학회/장비 공식자료":
        grade = "A"
        warning = "공식성 높은 자료입니다. 단, 최신 여부는 링크에서 직접 확인하세요."
    elif source_type == "의사/변호사 직접 콘텐츠":
        grade = "A-"
        warning = "전문가 직접 콘텐츠입니다. 표현은 그대로 베끼지 말고 핵심만 요약해 활용하세요."
    elif source_type == "병원/법무법인 공식 홈페이지·블로그":
        grade = "B"
        warning = "광고주/동종업계 자료일 수 있습니다. 강점 참고용으로 활용하고 과장표현은 정제하세요."
    elif source_type == "일반 블로그/카페/후기":
        grade = "C"
        warning = "후기성/경험담 가능성이 있어 핵심 근거로 쓰기 어렵습니다. 독자 고민 파악용으로만 쓰세요."
    elif source_type == "광고/출처불명/후기성 자료":
        grade = "제외"
        warning = "출처 신뢰도가 낮거나 광고성/후기성 위험이 있어 원고 근거로 쓰지 않는 편이 좋습니다."

    risky_words = ["후기", "경험담", "완치", "100%", "무조건", "최고", "1위", "유일", "보장"]
    if any(word in text for word in risky_words):
        if grade not in ["제외"]:
            warning += " / 위험 표현 또는 후기성 단어가 감지되었습니다. 링크를 열어 직접 리체크하세요."
        if source_type in ["일반 블로그/카페/후기", "광고/출처불명/후기성 자료"]:
            grade = "제외"
            warning = "후기성/과장 가능성이 높아 실제 원고 근거로 쓰지 않는 편이 좋습니다."

    return grade, warning


def result_to_source(result, field):
    title = result.get("title", "")
    url = result.get("url", "")
    content = result.get("content", "") or result.get("snippet", "") or ""
    source_type = infer_source_type(title, url, content, field)
    grade, warning = grade_source(title, url, source_type, field, content)
    return {
        "사용": grade in ["A", "A-", "B"],
        "등급": grade,
        "자료명": title,
        "URL": url,
        "출처유형": source_type,
        "핵심내용": content[:500],
        "주의사항": warning,
        "리체크": "링크 열어 최신성/후기성/과장표현 확인",
    }


def init_sources():
    if "sources" not in st.session_state:
        st.session_state.sources = []


def add_source_row(title, url, source_type, memo, field):
    if source_type == "자동분류":
        source_type = infer_source_type(title, url, memo, field)
    grade, warning = grade_source(title, url, source_type, field, memo)
    st.session_state.sources.append({
        "사용": grade in ["A", "A-", "B"],
        "등급": grade,
        "자료명": title,
        "URL": url,
        "출처유형": source_type,
        "핵심내용": memo,
        "주의사항": warning,
        "리체크": "링크 열어 최신성/후기성/과장표현 확인",
    })


def make_gpts_materials(df: pd.DataFrame):
    used = df[df["사용"] == True].copy()
    if used.empty:
        return "사용할 자료를 체크하면 GPTs에 넣을 핵심자료가 여기에 정리됩니다."

    lines = []
    lines.append("[GPTs 입력용 핵심자료]")
    lines.append("")
    for idx, row in used.iterrows():
        lines.append(f"{idx + 1}. {row['자료명']} ({row['등급']})")
        if row["URL"]:
            lines.append(f"- 출처: {row['URL']}")
        lines.append(f"- 핵심내용: {row['핵심내용']}")
        lines.append(f"- 사용주의: {row['주의사항']}")
        lines.append("")
    lines.append("[작성 지시]")
    lines.append("- 위 자료를 참고하되, 표현은 그대로 베끼지 말고 자연스러운 블로그 원고로 재구성한다.")
    lines.append("- 의료/법률/광고 위험표현은 피한다.")
    lines.append("- 독자의 고민을 먼저 짚고, 정보는 쉽게 풀어쓴다.")
    lines.append("- 테스트 원고라면 실제 병원명/법무법인명/원장명/변호사명을 임의로 만들지 않는다.")
    return "\n".join(lines)


# =============================
# 원고 검수 함수
# =============================

def check_title(title, keyword, draft):
    issues = []
    score = 15

    if not title:
        issues.append(("제목 없음", "제목을 입력해야 합니다."))
        return issues, 0, []

    title_len = korean_char_count(title)
    keyword_count = count_keyword(title, keyword)
    found_title_types = detect_title_type(title)

    if keyword and not title.startswith(keyword):
        issues.append(("키워드 위치", "키워드는 제목 맨 앞에 배치하는 것이 좋습니다."))
        score -= 3

    if keyword and keyword_count != 1:
        issues.append(("키워드 횟수", f"제목 내 키워드 횟수는 1회가 적정합니다. 현재 {keyword_count}회입니다."))
        score -= 2

    if title_len > 30:
        issues.append(("제목 길이", f"제목은 30자 이내가 좋습니다. 현재 {title_len}자입니다."))
        score -= 2

    if not found_title_types:
        issues.append(("클릭 요소", "숫자형, 질문형, 궁금증형, 상황공감형 중 하나를 활용하면 클릭률에 도움이 됩니다."))
        score -= 2

    if keyword and keyword not in draft:
        issues.append(("제목/본문 연결", "제목 키워드가 본문에 충분히 연결되지 않았습니다."))
        score -= 2

    return issues, max(score, 0), found_title_types


def check_intro(draft):
    intro = get_intro(draft)
    issues = []
    score = 20

    weak_patterns = [
        "이번 글에서는", "이 글에서는", "오늘은",
        "알아보겠습니다", "설명합니다", "정리해보겠습니다"
    ]
    empathy_patterns = [
        "고민", "불안", "걱정", "헷갈", "어려",
        "궁금", "답답", "무너", "당기", "번들"
    ]

    if any(pattern in intro for pattern in weak_patterns):
        issues.append(("AI식 도입", "도입부가 설명형으로 시작합니다. 독자의 고민이나 상황부터 건드리는 편이 좋습니다."))
        score -= 5

    if not any(pattern in intro for pattern in empathy_patterns):
        issues.append(("독자 공감 부족", "첫 3~5문장 안에 독자의 불안, 고민, 궁금증이 약합니다."))
        score -= 4

    if len(intro) < 150:
        issues.append(("도입 짧음", "도입부가 짧아 기대감을 만들기 어렵습니다."))
        score -= 3

    if "?" not in intro and "☑" not in intro and "✔" not in intro:
        issues.append(("도입 장치 부족", "질문형 문장이나 체크리스트형 도입을 고려해볼 수 있습니다."))
        score -= 2

    return issues, max(score, 0), intro


def check_body_seo(draft, keyword):
    issues = []
    score = 15

    char_count = korean_char_count(draft)
    body_keyword_count = count_keyword(draft, keyword)

    if char_count < 1500:
        issues.append(("분량 부족", f"본문은 1,500자 이상이 좋습니다. 현재 약 {char_count}자입니다."))
        score -= 4
    elif char_count > 2500:
        issues.append(("분량 과다", f"테스트 원고 기준으로는 다소 길 수 있습니다. 현재 약 {char_count}자입니다."))
        score -= 2

    if keyword and body_keyword_count < 5:
        issues.append(("키워드 부족", f"본문 키워드는 5회 이상 자연스럽게 들어가는 것이 좋습니다. 현재 {body_keyword_count}회입니다."))
        score -= 3

    heading_count = 0
    for line in draft.splitlines():
        line = line.strip()
        if 4 <= len(line) <= 35 and not line.endswith((".", "다", "요")):
            heading_count += 1

    if heading_count < 3:
        issues.append(("소제목 부족", "본문에 소제목이 부족합니다. 모바일 가독성을 위해 3~5개 정도 권장합니다."))
        score -= 3

    if "\n\n" not in draft:
        issues.append(("줄바꿈 부족", "문단 구분이 부족합니다. 모바일에서는 짧은 문단이 읽기 좋습니다."))
        score -= 2

    season_words = ["봄", "여름", "가을", "겨울", "요즘", "최근", "환절기", "습도", "기온", "찬바람"]
    if not any(word in draft for word in season_words):
        issues.append(("시의성 부족", "계절이나 최근 상황을 자연스럽게 넣으면 공감과 SEO에 도움이 됩니다."))
        score -= 1

    return issues, max(score, 0), char_count, body_keyword_count, heading_count


def check_ai_smell(draft):
    issues = []
    found_phrases = []
    score = 15

    for category, patterns in AI_SMELL_PATTERNS.items():
        for phrase in patterns:
            count = draft.count(phrase)
            if count > 0:
                found_phrases.append(phrase)

                if category == "메타 문장":
                    issues.append((category, f"'{phrase}' 표현이 감지되었습니다. 작성자 해설문처럼 보일 수 있습니다."))
                    score -= 2
                elif count >= 3:
                    issues.append((category, f"'{phrase}' 표현이 {count}회 반복됩니다. 문장 패턴을 바꾸는 것이 좋습니다."))
                    score -= 1

    colon_count = draft.count(":") + draft.count("：")
    quote_count = (
        draft.count("'") + draft.count('"') + draft.count("“") +
        draft.count("”") + draft.count("‘") + draft.count("’")
    )

    if colon_count >= 5:
        issues.append(("콜론 과다", f"콜론(:)이 {colon_count}회 사용되었습니다. AI식 정리문처럼 보일 수 있습니다."))
        score -= 2

    if quote_count >= 10:
        issues.append(("따옴표 과다", f"따옴표가 {quote_count}회 사용되었습니다. 강조 표현이 과해 보일 수 있습니다."))
        score -= 2

    repeated = find_repeated_words(draft)
    for word, count in repeated[:5]:
        issues.append(("반복 단어", f"'{word}' 단어가 {count}회 반복됩니다."))
        score -= 1
        found_phrases.append(word)

    return issues, max(score, 0), found_phrases


def check_compliance(draft, purpose, field):
    issues = []
    score = 15
    found_phrases = []
    patterns = []

    if field in ["에스테틱 / 피부관리", "병원 / 의료"] or purpose == "실제 병원 광고 원고":
        patterns += MEDICAL_RISK_PATTERNS

    if field == "법률" or purpose == "실제 법률 광고 원고":
        patterns += LEGAL_RISK_PATTERNS

    for phrase in patterns:
        if phrase in draft:
            found_phrases.append(phrase)
            issues.append(("위험 표현", f"'{phrase}' 표현은 광고 규정상 위험하거나 과장으로 보일 수 있습니다."))
            score -= 2

    if purpose == "포트폴리오용 샘플 원고":
        if "포트폴리오" not in draft and "샘플" not in draft:
            issues.append(("포폴 고지문", "포트폴리오용이라면 샘플 원고 고지문을 넣는 것이 안전합니다."))
            score -= 2

        fake_client_words = ["저희 병원", "본원은", "저희 법무법인", "본 법무법인"]
        for word in fake_client_words:
            if word in draft:
                found_phrases.append(word)
                issues.append(("포폴 위험", f"'{word}' 표현은 실제 광고주인 척 보일 수 있습니다."))
                score -= 2

    if purpose == "마케팅 회사 테스트 원고":
        fake_specific_words = ["OO병원", "OO의원", "OO법무법인", "OO변호사"]
        for word in fake_specific_words:
            if word in draft:
                issues.append(("테스트 원고 주의", f"'{word}'처럼 가짜 광고주 정보가 들어간 경우 제출 전 삭제하는 것이 좋습니다."))
                score -= 1

    if purpose == "실제 법률 광고 원고":
        if "광고책임 변호사" not in draft:
            issues.append(("광고책임 변호사", "실제 법률 광고 원고라면 광고책임 변호사 표시가 필요할 수 있습니다."))
            score -= 3

    return issues, max(score, 0), found_phrases


def check_glossary(draft, field):
    terms = GLOSSARY_TERMS.get(field, [])
    suggestions = []

    for term in terms:
        if term in draft:
            has_explanation = (
                f"{term}란" in draft or
                f"{term}이란" in draft or
                "여기서 잠깐" in draft
            )
            if not has_explanation:
                suggestions.append(term)

    return suggestions


def check_ending(draft):
    ending = get_ending(draft)
    issues = []
    score = 5

    if len(ending) < 120:
        issues.append(("마무리 약함", "마무리 문단이 짧거나 부족합니다."))
        score -= 2

    connect_words = [
        "상담", "점검", "확인", "관리 방향", "대응 방향",
        "전문가", "의료진", "변호사"
    ]
    if not any(word in ending for word in connect_words):
        issues.append(("상담 연결 부족", "마무리가 단순 요약으로 끝날 수 있습니다. 현재 상황 점검이나 상담 연결 문장을 고려해보세요."))
        score -= 2

    guarantee_words = ["반드시", "무조건", "확실히", "100%"]
    if any(word in ending for word in guarantee_words):
        issues.append(("마무리 위험", "마무리에서 결과를 단정하는 표현이 감지되었습니다."))
        score -= 1

    return issues, max(score, 0), ending


def estimate_price(score):
    if score >= 94:
        return "5만 원 이상급 가능"
    if score >= 92:
        return "4~5만 원급 테스트/포폴 원고"
    if score >= 89:
        return "4만 원급 가능"
    if score >= 86:
        return "3만 원급 가능"
    if score >= 80:
        return "1.5~2만 원급 저단가 납품 가능"
    return "수정 필요"


def final_judgement(score):
    if score >= 92:
        return "제출 가능 수준입니다. 작은 표현만 다듬으면 됩니다.", "success"
    if score >= 86:
        return "기본기는 괜찮습니다. 도입부, 반복 표현, 마무리를 보강하면 점수가 올라갑니다.", "info"
    return "수정이 필요합니다. 제목, 도입부, 위험표현, 본문 구조를 먼저 손보세요.", "error"


def recommend_intro_type(field):
    if field in ["에스테틱 / 피부관리", "병원 / 의료"]:
        return [
            ("체크리스트형", "독자가 자신의 증상이나 피부 상태를 바로 대입할 수 있어 이탈을 줄입니다."),
            ("질문형", "피부 고민이나 치료 고민을 바로 건드려 클릭 의도를 이어갑니다."),
            ("상황공감형", "원장이나 전문가가 직접 상담하는 듯한 느낌을 줄 수 있습니다."),
        ]

    if field == "법률":
        return [
            ("체크리스트형", "독자가 자신의 사건 상황을 바로 대입할 수 있습니다."),
            ("질문형", "차용증, 증거, 경찰조사처럼 핵심 불안을 바로 건드립니다."),
            ("위기인식형", "방치하면 생길 수 있는 문제를 과하지 않게 알려줄 수 있습니다."),
        ]

    return [
        ("질문형", "독자의 궁금증을 자연스럽게 유도합니다."),
        ("체크리스트형", "상황 대입이 쉬워집니다."),
        ("비교형", "선택 고민이 있는 주제에 적합합니다."),
    ]


# =============================
# UI
# =============================

init_sources()

st.title("📝 달로썸 원고 검수기 v2")
st.caption("자동 자료수집/출처등급 → 링크 리체크 → GPTs 핵심자료 → 초안 검수 순서로 진행합니다.")

with st.sidebar:
    st.header("기본 설정")
    purpose = st.radio("원고 목적", PURPOSES, index=1)
    field = st.radio("분야", FIELDS, index=0)

    keyword = st.text_input("키워드", placeholder="예: 복합성 피부 좋아지는 방법")
    title = st.text_input("제목", placeholder="예: 복합성 피부 좋아지는 방법 5가지 관리 기준")
    topic = st.text_input("주제", placeholder="예: 복합성 피부 관리 방법")
    target = st.text_input("타깃 독자", placeholder="예: 유분과 속건조가 동시에 고민인 20~40대 여성")
    tone = st.text_input("원고 톤", placeholder="예: 에스테틱 원장이 설명하는 친절한 전문 톤")

    st.divider()
    api_key_status = "설정됨" if get_secret("TAVILY_API_KEY") else "없음"
    st.caption(f"Tavily API 키: {api_key_status}")

tab1, tab2, tab3 = st.tabs(["① 자동 자료수집 / 출처등급", "② GPTs 핵심자료", "③ 초안 검수"])

with tab1:
    st.subheader("1. 자동 자료수집 / 출처등급")
    st.caption("키워드와 주제를 기준으로 자료를 긁어오고, A/B/C/제외 등급을 매깁니다. 이후 링크를 직접 열어 리체크하세요.")

    api_key = get_secret("TAVILY_API_KEY")
    if not api_key:
        st.error("TAVILY_API_KEY가 없습니다. Streamlit Cloud의 App settings → Secrets에 API 키를 넣어야 자동 자료수집이 됩니다.")
        st.code('TAVILY_API_KEY = "tvly-본인키"', language="toml")

    search_queries = build_search_queries(keyword, topic, field, purpose)
    query_text = st.text_area(
        "검색 쿼리",
        value="\n".join(search_queries),
        height=120,
        help="한 줄에 하나씩 검색합니다. 필요하면 직접 수정하세요."
    )

    col_search1, col_search2, col_search3 = st.columns([1, 1, 2])
    with col_search1:
        max_results = st.number_input("쿼리당 결과 수", min_value=1, max_value=10, value=4, step=1)
    with col_search2:
        run_search = st.button("자동 자료수집 실행", type="primary")
    with col_search3:
        st.caption("검색 결과는 자동 등급화되지만, 최종 사용 여부는 반드시 링크를 열어 확인하세요.")

    if run_search:
        if not api_key:
            st.stop()

        queries = [q.strip() for q in query_text.splitlines() if q.strip()]
        if not queries:
            st.warning("검색 쿼리를 입력하세요.")
            st.stop()

        found = []
        seen_urls = set()

        with st.spinner("자료를 검색하고 등급을 매기는 중입니다..."):
            for q in queries:
                try:
                    results = tavily_search(q, max_results=max_results)
                    for result in results:
                        url = result.get("url", "")
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        row = result_to_source(result, field)
                        found.append(row)
                except Exception as e:
                    st.error(f"검색 실패: {q} / {e}")

        if found:
            st.session_state.sources = found + st.session_state.sources
            st.success(f"{len(found)}개 자료를 수집했습니다.")
        else:
            st.warning("검색 결과가 없습니다. 쿼리를 바꿔보세요.")

    st.divider()
    st.write("### 수동 자료 추가")
    with st.form("source_form", clear_on_submit=True):
        source_title = st.text_input("자료명", placeholder="예: 법제처 대여금 관련 생활법령정보 / 피부과 전문의 칼럼")
        source_url = st.text_input("URL", placeholder="https://...")
        source_type = st.selectbox("출처 유형", SOURCE_TYPES)
        source_memo = st.text_area("핵심내용", height=120, placeholder="이 자료에서 원고에 쓸 핵심 내용만 요약")
        submitted = st.form_submit_button("수동 자료 추가")

        if submitted:
            if not source_title and not source_memo:
                st.warning("자료명 또는 핵심내용을 입력하세요.")
            else:
                add_source_row(source_title, source_url, source_type, source_memo, field)
                st.success("자료가 추가되었습니다.")

    st.divider()

    if st.session_state.sources:
        st.write("### 수집 자료표")
        df = pd.DataFrame(st.session_state.sources)

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "사용": st.column_config.CheckboxColumn("사용", default=True),
                "URL": st.column_config.LinkColumn("URL"),
                "핵심내용": st.column_config.TextColumn("핵심내용", width="large"),
                "주의사항": st.column_config.TextColumn("주의사항", width="large"),
                "리체크": st.column_config.TextColumn("리체크", width="medium"),
            },
            key="source_editor",
        )
        st.session_state.sources = edited_df.to_dict("records")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("전체 자료 삭제"):
                st.session_state.sources = []
                st.rerun()
        with col_b:
            used_count = int(pd.DataFrame(st.session_state.sources)["사용"].sum())
            st.metric("사용 체크", f"{used_count}개")
        with col_c:
            st.info("A/A-/B 위주로 사용하고, C/제외는 보조 참고만 하세요.")
    else:
        st.info("아직 수집된 자료가 없습니다. 자동 자료수집을 실행하거나 수동으로 자료를 추가하세요.")

with tab2:
    st.subheader("2. GPTs에 넣을 핵심자료")
    st.caption("①에서 사용 체크한 자료만 모아 GPTs에 붙여넣기 좋은 형태로 정리합니다.")

    if st.session_state.sources:
        df = pd.DataFrame(st.session_state.sources)
        materials = make_gpts_materials(df)
        st.text_area("복사해서 GPTs에 넣을 자료", value=materials, height=480)
        st.info("이 자료를 달로썸 GPTs에 넣어 초안을 받은 뒤, ③ 초안 검수 탭에 붙여넣으면 됩니다.")
    else:
        st.warning("먼저 ① 자동 자료수집 탭에서 자료를 수집하세요.")

with tab3:
    st.subheader("3. GPTs 초안 붙여넣기 / 최종 검수")
    draft = st.text_area("초안", height=420, placeholder="여기에 GPTs에서 받은 초안을 붙여넣으세요.")
    run = st.button("검수 시작", type="primary")

    if run:
        if not draft.strip():
            st.warning("초안을 먼저 붙여넣어야 합니다.")
            st.stop()

        draft = clean_text(draft)

        title_issues, title_score, title_types = check_title(title, keyword, draft)
        intro_issues, intro_score, intro = check_intro(draft)
        body_issues, body_score, char_count, body_keyword_count, heading_count = check_body_seo(draft, keyword)
        ai_issues, ai_score, ai_phrases = check_ai_smell(draft)
        compliance_issues, compliance_score, risk_phrases = check_compliance(draft, purpose, field)
        glossary_suggestions = check_glossary(draft, field)
        ending_issues, ending_score, ending = check_ending(draft)

        total_score = title_score + intro_score + body_score + ai_score + compliance_score + ending_score
        price = estimate_price(total_score)

        st.divider()
        st.subheader("최종 점수")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총점", f"{total_score}점")
        col2.metric("예상 단가", price)
        col3.metric("본문 글자수", f"{char_count}자")
        col4.metric("본문 키워드", f"{body_keyword_count}회")

        st.progress(min(total_score / 100, 1.0))

        st.write("### 세부 점수")
        st.table({
            "항목": ["제목", "도입부", "본문 SEO", "AI티 제거", "위험표현 안전성", "마무리"],
            "점수": [
                f"{title_score}/15",
                f"{intro_score}/20",
                f"{body_score}/15",
                f"{ai_score}/15",
                f"{compliance_score}/15",
                f"{ending_score}/5",
            ],
        })

        if title_types:
            st.caption("감지된 제목 유형: " + ", ".join(title_types))

        st.divider()
        st.subheader("하이라이트 원고")

        highlight_phrases = ai_phrases + risk_phrases
        highlighted = highlight_text(draft, highlight_phrases)
        st.markdown(
            f"<div style='line-height:1.9; font-size:16px; white-space:pre-wrap;'>{highlighted}</div>",
            unsafe_allow_html=True,
        )

        st.divider()
        st.subheader("검수 결과")

        def show_issues(title_text, issues):
            with st.expander(title_text, expanded=True):
                if not issues:
                    st.success("문제 없음")
                else:
                    for category, message in issues:
                        st.warning(f"[{category}] {message}")

        show_issues("제목 검수", title_issues)
        show_issues("도입부 검수", intro_issues)
        show_issues("본문 SEO 검수", body_issues)
        show_issues("AI티 검수", ai_issues)
        show_issues("위험표현 검수", compliance_issues)
        show_issues("마무리 검수", ending_issues)

        st.divider()
        st.subheader("도입부 추천")

        for name, effect in recommend_intro_type(field):
            st.info(f"**{name}**\n\n효과: {effect}")

        st.divider()
        st.subheader("어려운 용어 코너 추천")

        if glossary_suggestions:
            for term in glossary_suggestions:
                st.write(f"✅ **여기서 잠깐! {term}란?** 코너 추가 추천")
                st.caption("효과: 독자가 낯선 용어를 이해하기 쉬워지고, 원고가 더 친절하고 정성스러워 보입니다.")
        else:
            st.success("현재 감지된 어려운 용어 코너 추천은 없습니다.")

        st.divider()
        st.subheader("최종 납품 전 체크리스트")

        checklist = [
            f"본문 1,500자 이상 여부: {'통과' if char_count >= 1500 else '보완 필요'}",
            f"제목 키워드 1회 여부: {'통과' if keyword and count_keyword(title, keyword) == 1 else '보완 필요'}",
            f"제목 키워드 앞 배치 여부: {'통과' if keyword and title.startswith(keyword) else '보완 필요'}",
            f"본문 키워드 5회 이상 여부: {'통과' if keyword and body_keyword_count >= 5 else '보완 필요'}",
            f"소제목 3개 이상 여부: {'통과' if heading_count >= 3 else '보완 필요'}",
            f"AI티 표현 여부: {'보완 필요' if ai_issues else '통과'}",
            f"위험표현 여부: {'보완 필요' if compliance_issues else '통과'}",
            f"마무리 연결 여부: {'보완 필요' if ending_issues else '통과'}",
        ]

        for item in checklist:
            st.write("□ " + item)

        st.divider()
        st.subheader("판정")

        judgement, level = final_judgement(total_score)
        if level == "success":
            st.success(judgement)
        elif level == "info":
            st.info(judgement)
        else:
            st.error(judgement)

        with st.expander("현재 입력 정보", expanded=False):
            st.write(f"원고 목적: {purpose}")
            st.write(f"분야: {field}")
            st.write(f"키워드: {keyword}")
            st.write(f"제목: {title}")
            st.write(f"주제: {topic}")
            st.write(f"타깃: {target}")
            st.write(f"톤: {tone}")
