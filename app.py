
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="달로썸 원고 검수기 v3", layout="wide")

PURPOSES = [
    "마케팅 회사 테스트 원고",
    "포트폴리오용 샘플 원고",
    "실제 에스테틱 광고 원고",
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

WRITER_PERSPECTIVES = [
    "에스테틱 원장",
    "피부과 원장/전문의",
    "변호사",
    "전문업종 대표",
    "정보성 블로그 작성자",
]

RISK_PHRASES = {
    "공통": [
        "100%", "무조건", "반드시 개선", "확실히 개선", "완벽하게", "부작용 없음",
        "효과 보장", "즉시 효과", "영구적", "완치", "최고", "유일한", "단 하나"
    ],
    "에스테틱 / 피부관리": [
        "치료", "진단", "처방", "의료진", "병변", "질환 치료", "재생된다",
        "피부가 완전히 바뀝니다", "무조건 좋아집니다"
    ],
    "병원 / 의료": [
        "완치", "부작용 없음", "통증 없음", "흉터 없음", "재발 없음",
        "무조건 개선", "100% 개선"
    ],
    "법률": [
        "무조건 승소", "반드시 승소", "100% 승소", "확실히 받아냅니다",
        "무조건 받을 수 있습니다"
    ],
}

AI_PATTERNS = [
    "이 글에서는", "오늘은", "알아보겠습니다", "설명드리겠습니다", "중요합니다",
    "필요합니다", "도움이 됩니다", "도움이 될 수 있습니다", "확인해야 합니다",
    "정리해보겠습니다", "살펴보겠습니다", "바로", "핵심은"
]

GLOSSARY_TERMS = {
    "에스테틱 / 피부관리": ["T존", "U존", "유수분", "피부 장벽", "각질", "피지", "자외선 차단제", "홈케어"],
    "병원 / 의료": ["진피", "표피", "염증", "색소침착", "회복기간", "부작용"],
    "법률": ["소멸시효", "지급명령", "가압류", "집행권원", "입증", "내용증명"],
}


def extract_title(title_input, draft):
    title_input = (title_input or "").strip()
    draft = draft or ""

    if title_input:
        title = re.sub(r"^제목\s*[:：]\s*", "", title_input).strip()
        return title, draft.strip(), "제목 입력칸"

    lines = [l.strip() for l in draft.splitlines() if l.strip()]
    if not lines:
        return "", draft.strip(), "없음"

    first = lines[0]
    if first.startswith("#"):
        title = first.lstrip("#").strip()
        body = "\n".join(lines[1:]).strip()
        return title, body, "본문 첫 줄"

    match = re.match(r"^제목\s*[:：]\s*(.+)$", first)
    if match:
        title = match.group(1).strip()
        body = "\n".join(lines[1:]).strip()
        return title, body, "본문 제목표기"

    if len(first) <= 40 and not first.endswith(("다.", "요.", "니다.", "죠.", "?")):
        title = first
        body = "\n".join(lines[1:]).strip()
        return title, body, "본문 첫 줄 자동추출"

    return "", draft.strip(), "없음"


def count_keyword(text, keyword):
    if not keyword:
        return 0
    return text.count(keyword)


def title_check(title, keyword):
    issues = []
    score = 15

    if not title:
        return [("제목 없음", "제목 입력칸 또는 본문 첫 줄에서 제목을 찾지 못했습니다.")], 0

    if keyword:
        if keyword not in title:
            issues.append(("제목 키워드 누락", f"제목에 키워드 '{keyword}'가 정확히 들어가지 않았습니다."))
            score -= 6
        elif not title.startswith(keyword):
            issues.append(("키워드 위치", "제목 키워드는 가능하면 맨 앞에 두는 것이 좋습니다."))
            score -= 2

    if len(title) > 30:
        issues.append(("제목 길이", f"제목이 {len(title)}자로 30자를 넘습니다."))
        score -= 3

    if keyword and title.count(keyword) > 1:
        issues.append(("키워드 반복", "제목에는 키워드를 1회만 넣는 편이 자연스럽습니다."))
        score -= 2

    return issues, max(score, 0)


def body_seo_check(body, keyword, target_len_min, target_len_max):
    issues = []
    score = 20
    no_space_len = len(re.sub(r"\s+", "", body))
    keyword_count = count_keyword(body, keyword)

    if no_space_len < target_len_min:
        issues.append(("본문 길이 부족", f"공백 제외 {no_space_len}자입니다. 권장 최소 {target_len_min}자보다 짧습니다."))
        score -= 6
    elif no_space_len > target_len_max:
        issues.append(("본문이 김", f"공백 제외 {no_space_len}자입니다. 권장 최대 {target_len_max}자를 넘습니다."))
        score -= 5

    if keyword and keyword_count < 5:
        issues.append(("본문 키워드 부족", f"본문 키워드가 {keyword_count}회입니다. 자연스럽게 5회 안팎을 권장합니다."))
        score -= 5
    elif keyword and keyword_count > 8:
        issues.append(("본문 키워드 과다", f"본문 키워드가 {keyword_count}회입니다. 반복 티가 날 수 있습니다."))
        score -= 3

    lines = [l.strip() for l in body.splitlines() if l.strip()]
    subheads = []
    for line in lines:
        if len(line) <= 38 and not line.endswith(("다.", "요.", "니다.", "죠.", "?")) and not line.startswith("☑"):
            subheads.append(line)

    if len(subheads) < 3:
        issues.append(("소제목 부족", f"소제목으로 보이는 줄이 {len(subheads)}개입니다. 3~5개가 읽기 좋습니다."))
        score -= 3

    return issues, max(score, 0), no_space_len, keyword_count, len(subheads)


def intro_check(body):
    issues = []
    score = 15
    intro = body.strip()[:500]

    empathy_words = ["당기", "번들", "헷갈", "속상", "고민", "푸석", "예민", "답답"]
    if not any(w in intro for w in empathy_words):
        issues.append(("공감 부족", "도입부에서 독자의 실제 고민이 약합니다."))
        score -= 4

    if "☑" not in intro and "?" not in intro and "적 있으" not in intro:
        issues.append(("도입 장치 약함", "체크리스트형, 질문형, 상황 묘사 중 하나가 들어가면 집중도가 올라갑니다."))
        score -= 3

    weak_starts = ["오늘은", "이번 글에서는", "알아보겠습니다", "설명드리겠습니다"]
    if any(intro.startswith(w) for w in weak_starts):
        issues.append(("뻔한 시작", "도입 첫 문장이 흔한 AI식 시작입니다. 독자 고민부터 시작하는 편이 좋습니다."))
        score -= 4

    return issues, max(score, 0)


def ai_smell_check(body):
    issues = []
    score = 15
    found = []

    for pattern in AI_PATTERNS:
        count = body.count(pattern)
        if count >= 3:
            found.append(f"{pattern}({count})")

    if found:
        issues.append(("반복 표현", ", ".join(found)))
        score -= min(7, len(found) * 2)

    colon_count = body.count(":")
    quote_count = body.count('"') + body.count("'")
    if colon_count >= 5:
        issues.append(("콜론 과다", f"콜론(:)이 {colon_count}회입니다. AI 원고 느낌이 날 수 있습니다."))
        score -= 3
    if quote_count >= 10:
        issues.append(("따옴표 과다", f"따옴표가 {quote_count}회입니다. 인터뷰체가 아니라면 줄이는 편이 좋습니다."))
        score -= 2

    return issues, max(score, 0)


def compliance_check(body, field, purpose):
    issues = []
    score = 15
    targets = RISK_PHRASES.get("공통", []) + RISK_PHRASES.get(field, [])
    found = sorted(set([phrase for phrase in targets if phrase in body]))

    if found:
        issues.append(("위험표현 감지", ", ".join(found)))
        score -= min(10, len(found) * 2)

    if "테스트" in purpose:
        fake_names = ["저희 병원", "본원", "대표원장", "전문의가 직접", "법무법인", "변호사 사무실"]
        detected = [w for w in fake_names if w in body]
        if detected:
            issues.append(("테스트 원고 주의", f"실제 업체 정보가 없으면 임의 기관 표현은 피하는 편이 안전합니다: {', '.join(detected)}"))
            score -= 4

    return issues, max(score, 0)


def persona_check(body, writer_perspective):
    issues = []
    score = 10

    if writer_perspective == "에스테틱 원장":
        medical_heavy = ["진단", "처방", "치료", "완치", "병변", "진료", "의료진"]
        detected = [w for w in medical_heavy if w in body]
        if detected:
            issues.append(("에스테틱 톤 이탈", f"의료행위처럼 보일 수 있는 표현: {', '.join(detected)}"))
            score -= min(5, len(detected))

        esthetic_words = ["원장", "에스테틱", "관리", "홈케어", "피부 상태", "유수분", "상담", "피부 컨디션"]
        if sum(1 for w in esthetic_words if w in body) < 3:
            issues.append(("원장 관점 약함", "에스테틱 원장이 상담하듯 말하는 표현이 조금 더 필요합니다."))
            score -= 3

    return issues, max(score, 0)


def glossary_check(body, field):
    suggestions = []
    terms = GLOSSARY_TERMS.get(field, [])

    for term in terms:
        if term in body:
            idx = body.find(term)
            window = body[max(0, idx - 50):idx + 120]
            if "란" not in window and "뜻" not in window and "말합니다" not in window and "부위" not in window:
                suggestions.append(term)

    return sorted(set(suggestions))


def ending_check(body):
    issues = []
    score = 10
    ending = body[-500:]

    if len(ending.strip()) < 180:
        issues.append(("마무리 짧음", "마무리에서 독자 행동 기준이나 관리 방향을 조금 더 정리하면 좋습니다."))
        score -= 3

    action_words = ["확인", "상담", "점검", "관리", "살펴", "조절", "찾아"]
    if not any(w in ending for w in action_words):
        issues.append(("행동 유도 약함", "마지막에 독자가 다음에 무엇을 하면 좋을지 약합니다."))
        score -= 3

    return issues, max(score, 0)


def price_estimate(score):
    if score >= 94:
        return "5만 원 이상 포트폴리오급"
    if score >= 92:
        return "4~5만 원 테스트 합격권"
    if score >= 89:
        return "3~4만 원 실무 가능권"
    if score >= 85:
        return "2~3만 원 보완 필요"
    return "초안 재작성 권장"


def show_issues(title, issues):
    st.write(f"### {title}")
    if not issues:
        st.success("통과")
    else:
        for name, desc in issues:
            st.warning(f"**{name}** — {desc}")


st.title("📝 달로썸 원고 검수기 v3")
st.caption("자료수집 기능을 빼고, 테스트 원고 검수에 필요한 제목/키워드/길이/위험표현/작성자 관점만 정확하게 봅니다.")

with st.sidebar:
    st.header("원고 조건")
    purpose = st.selectbox("원고 목적", PURPOSES, index=0)
    field = st.selectbox("분야", FIELDS, index=0)
    writer_perspective = st.selectbox("작성자 관점", WRITER_PERSPECTIVES, index=0)
    keyword = st.text_input("키워드", value="복합성 피부 좋아지는 방법")
    title_input = st.text_input("제목", placeholder="제목을 따로 넣거나, 본문 첫 줄에 넣어도 됩니다.")
    target_len_min = st.number_input("권장 최소 글자수(공백 제외)", min_value=800, max_value=3000, value=1500, step=100)
    target_len_max = st.number_input("권장 최대 글자수(공백 제외)", min_value=1000, max_value=4000, value=2200, step=100)

draft = st.text_area("검수할 원고를 붙여넣으세요", height=520, placeholder="제목 포함 원고를 그대로 붙여넣어도 됩니다.")

if st.button("검수 시작", type="primary"):
    title, body, title_source = extract_title(title_input, draft)

    if not body:
        st.error("본문이 비어 있습니다.")
        st.stop()

    st.write("## 추출 결과")
    col1, col2, col3 = st.columns(3)
    col1.metric("제목 인식", "성공" if title else "실패")
    col2.metric("제목 출처", title_source)
    col3.metric("제목 글자수", len(title) if title else 0)
    st.info(f"인식된 제목: {title if title else '없음'}")

    title_issues, title_score = title_check(title, keyword)
    body_issues, body_score, no_space_len, kw_count, subhead_count = body_seo_check(body, keyword, target_len_min, target_len_max)
    intro_issues, intro_score = intro_check(body)
    ai_issues, ai_score = ai_smell_check(body)
    compliance_issues, compliance_score = compliance_check(body, field, purpose)
    persona_issues, persona_score = persona_check(body, writer_perspective)
    ending_issues, ending_score = ending_check(body)
    glossary_terms = glossary_check(body, field)

    total = title_score + body_score + intro_score + ai_score + compliance_score + persona_score + ending_score
    total = min(max(total, 0), 100)

    st.write("## 점수")
    st.metric("총점", f"{total}점", price_estimate(total))

    score_df = pd.DataFrame([
        {"항목": "제목", "점수": f"{title_score}/15"},
        {"항목": "본문 SEO/길이/키워드", "점수": f"{body_score}/20"},
        {"항목": "도입부", "점수": f"{intro_score}/15"},
        {"항목": "AI티", "점수": f"{ai_score}/15"},
        {"항목": "위험표현", "점수": f"{compliance_score}/15"},
        {"항목": "작성자 관점", "점수": f"{persona_score}/10"},
        {"항목": "마무리", "점수": f"{ending_score}/10"},
    ])
    st.table(score_df)

    st.write("## 핵심 수치")
    metric_cols = st.columns(4)
    metric_cols[0].metric("공백 제외 글자수", no_space_len)
    metric_cols[1].metric("본문 키워드 횟수", kw_count)
    metric_cols[2].metric("소제목 수", subhead_count)
    metric_cols[3].metric("분야", field)

    show_issues("제목 검수", title_issues)
    show_issues("본문 SEO/길이/키워드", body_issues)
    show_issues("도입부 검수", intro_issues)
    show_issues("AI티 검수", ai_issues)
    show_issues("위험표현 검수", compliance_issues)
    show_issues("작성자 관점 검수", persona_issues)
    show_issues("마무리 검수", ending_issues)

    st.write("### 용어 설명 제안")
    if glossary_terms:
        st.info("본문에 나오지만 초보 독자에게 설명이 있으면 좋은 용어: " + ", ".join(glossary_terms))
    else:
        st.success("용어 설명 제안 없음")

    st.write("## 제출 판단")
    if total >= 92:
        st.success("제출 가능권입니다. 오탈자와 줄바꿈만 확인하세요.")
    elif total >= 89:
        st.info("실무 가능권입니다. 제목/도입/키워드 중 하나만 보완하면 제출권에 가까워집니다.")
    elif total >= 85:
        st.warning("보완 필요입니다. 길이, 제목 키워드, 도입부를 먼저 고치세요.")
    else:
        st.error("재작성 권장입니다. 구조부터 다시 잡는 편이 빠릅니다.")
else:
    st.info("왼쪽 조건을 입력하고 원고를 붙여넣은 뒤 검수 시작을 누르세요.")
