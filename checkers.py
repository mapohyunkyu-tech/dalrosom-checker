import re
from .constants import (
    AI_SMELL_PATTERNS,
    MEDICAL_RISK_PATTERNS,
    LEGAL_RISK_PATTERNS,
    GLOSSARY_TERMS,
    TITLE_TYPES,
)
from .utils import (
    count_keyword,
    korean_char_count,
    get_intro,
    get_ending,
    detect_title_type,
    find_repeated_words,
)


def check_title(title, keyword, draft):
    issues = []
    score = 15

    if not title:
        issues.append(("제목 없음", "제목을 입력해야 합니다."))
        return issues, 0, []

    title_len = korean_char_count(title)
    keyword_count = count_keyword(title, keyword)
    found_title_types = detect_title_type(title, TITLE_TYPES)

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
        if not line:
            continue
        if 4 <= len(line) <= 35 and not line.endswith(("다.", "요.", "니다.", ".", "?", "!")):
            heading_count += 1
        elif re.search(r"^\s*#{1,3}\s+", line):
            heading_count += 1
        elif re.search(r"^\s*\d+\.\s+", line):
            heading_count += 1
        elif re.search(r"^\s*\[.+?\]", line):
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
