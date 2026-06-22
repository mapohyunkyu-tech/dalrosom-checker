
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="달로썸 원고 검수기 v3.4", layout="wide")

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

INTRO_TYPES = [
    "1. 독자의 상황을 찔러주는 체크리스트 활용",
    "2. 비교 표 활용",
    "3. 대화체 문구",
    "4. 뉴스 기사 활용",
    "5. 독자에게 질문 던지기",
    "6. 많이 묻는 질문 인용",
    "7. 검색만으로는 모르는 알짜 정보 예고",
    "8. 간단한 웹툰 만들어 넣기",
]

ENDING_TYPES = [
    "관리 철학형",
    "상담 유도형",
    "체크리스트 요약형",
    "부드러운 CTA형",
    "철학 없이 정보 마무리",
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


def default_philosophy_by_field(field, writer_perspective):
    if writer_perspective == "에스테틱 원장":
        return "피부를 무리하게 바꾸기보다, 지금 피부가 편안하게 받아들일 수 있는 균형을 찾는 것을 중요하게 생각합니다."
    if field == "법률":
        return "사건을 단정하기보다 자료와 절차를 차분히 확인해 현실적인 대응 방향을 찾는 것을 중요하게 생각합니다."
    if field == "병원 / 의료":
        return "개인의 상태를 먼저 살피고, 무리한 기대보다 안전한 방향으로 설명하는 것을 중요하게 생각합니다."
    return "과장된 표현보다 현실적인 기준과 꾸준한 관리를 중요하게 생각합니다."


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


def body_seo_check(body, keyword, target_len_min, target_len_max, title=""):
    issues = []
    score = 20
    no_space_len = len(re.sub(r"\s+", "", body))
    body_keyword_count = count_keyword(body, keyword)
    title_keyword_count = count_keyword(title, keyword)
    total_keyword_count = body_keyword_count + title_keyword_count

    if no_space_len < 1200:
        issues.append(("본문 길이 부족", f"공백 제외 {no_space_len}자입니다. 최소 1,300자 이상은 맞추는 편이 좋습니다."))
        score -= 6
    elif no_space_len < target_len_min:
        issues.append(("본문이 약간 짧음", f"공백 제외 {no_space_len}자입니다. 큰 문제는 아니지만 100~200자 정도 보강하면 더 안정적입니다."))
        score -= 2
    elif no_space_len > target_len_max:
        issues.append(("본문이 김", f"공백 제외 {no_space_len}자입니다. 권장 최대 {target_len_max}자를 넘습니다."))
        score -= 4

    if keyword and total_keyword_count < 5:
        issues.append(("키워드 부족", f"제목 포함 키워드가 {total_keyword_count}회입니다. 자연스럽게 총 5회 안팎을 권장합니다."))
        score -= 4
    elif keyword and body_keyword_count < 4:
        issues.append(("본문 키워드 약간 부족", f"본문 키워드가 {body_keyword_count}회입니다. 본문에 1회 정도 더 넣으면 안정적입니다."))
        score -= 2
    elif keyword and total_keyword_count > 9:
        issues.append(("키워드 과다", f"제목 포함 키워드가 {total_keyword_count}회입니다. 반복 티가 날 수 있습니다."))
        score -= 3

    lines = [l.strip() for l in body.splitlines() if l.strip()]
    subheads = []
    for line in lines:
        if len(line) <= 38 and not line.endswith(("다.", "요.", "니다.", "죠.", "?")) and not line.startswith("☑"):
            subheads.append(line)

    if len(subheads) < 3:
        issues.append(("소제목 부족", f"소제목으로 보이는 줄이 {len(subheads)}개입니다. 3~5개가 읽기 좋습니다."))
        score -= 3

    return issues, max(score, 0), no_space_len, body_keyword_count, total_keyword_count, len(subheads)


def detect_intro_types(body):
    intro = body.strip()[:900]
    detected = []

    # 1. 체크리스트
    if "☑" in intro or "□" in intro or len([l for l in intro.splitlines() if l.strip().startswith(("-", "·", "•", "✓", "✔"))]) >= 2:
        detected.append("1. 독자의 상황을 찔러주는 체크리스트 활용")

    # 2. 비교 표
    if "|" in intro or "비교" in intro or "차이" in intro or "반면" in intro or "표로" in intro:
        detected.append("2. 비교 표 활용")

    # 3. 대화체
    if any(w in intro for w in ['"저는', '"혹시', '"왜', '"어떻게', "라고 하시는", "라고 묻는", "하시죠", "있으실 거예요", "아시나요"]):
        detected.append("3. 대화체 문구")

    # 4. 뉴스 기사 활용
    if any(w in intro for w in ["뉴스", "기사", "보도", "최근", "언론", "자료에 따르면"]):
        detected.append("4. 뉴스 기사 활용")

    # 5. 질문 던지기
    if "?" in intro or "않으신가요" in intro or "적 있으" in intro or "궁금" in intro:
        detected.append("5. 독자에게 질문 던지기")

    # 6. 많이 묻는 질문 인용
    if any(w in intro for w in ["많이 받는 질문", "자주 받는 질문", "많이 묻는", "자주 묻는", "FAQ", "질문 중 하나"]):
        detected.append("6. 많이 묻는 질문 인용")

    # 7. 알짜 정보 예고
    if any(w in intro for w in ["검색만으로", "잘 알려지지", "알짜", "현장에서", "실제로", "놓치기 쉬운", "여기서", "핵심은"]):
        detected.append("7. 검색만으로는 모르는 알짜 정보 예고")

    # 8. 웹툰
    if any(w in intro for w in ["웹툰", "컷", "만화", "그림", "장면", "[컷", "1컷", "2컷"]):
        detected.append("8. 간단한 웹툰 만들어 넣기")

    return detected


def intro_check(body, intro_type):
    issues = []
    score = 15
    intro = body.strip()[:900]
    detected = detect_intro_types(body)

    empathy_words = ["당기", "번들", "헷갈", "속상", "고민", "푸석", "예민", "답답", "불안", "막막"]
    if not any(w in intro for w in empathy_words):
        issues.append(("공감 부족", "도입부에서 독자의 실제 고민이 약합니다."))
        score -= 3

    if intro_type not in detected:
        issues.append(("도입 방식 불일치", f"선택한 달로썸 도입 방식은 '{intro_type}'인데, 현재 감지된 방식은 {', '.join(detected) if detected else '뚜렷한 유형 없음'}입니다."))
        score -= 3

    # 달로썸식 도입은 독자가 계속 읽을 이유가 보여야 함
    reason_words = ["그래서", "하지만", "다만", "핵심", "기준", "알아두", "확인", "오늘은", "이번 글"]
    if not any(w in intro for w in reason_words):
        issues.append(("계속 읽을 이유 약함", "도입부에서 이 글을 읽으면 무엇을 얻는지 조금 더 보여주면 좋습니다."))
        score -= 2

    weak_starts = ["오늘은", "이번 글에서는", "알아보겠습니다", "설명드리겠습니다"]
    if any(intro.startswith(w) for w in weak_starts):
        issues.append(("뻔한 시작", "도입 첫 문장이 흔한 AI식 시작입니다. 독자 상황이나 질문부터 시작하는 편이 좋습니다."))
        score -= 3

    return issues, max(score, 0), detected


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


def is_safe_risk_context(body, phrase):
    safe_markers = ["아니", "않", "없", "피하", "보다", "있지 않습니다", "권하지", "주의", "무조건 없애", "무조건 두껍"]
    for match in re.finditer(re.escape(phrase), body):
        start = max(0, match.start() - 20)
        end = min(len(body), match.end() + 40)
        window = body[start:end]
        if any(marker in window for marker in safe_markers):
            return True
    return False


def compliance_check(body, field, purpose):
    issues = []
    score = 15
    targets = RISK_PHRASES.get("공통", []) + RISK_PHRASES.get(field, [])
    found = sorted(set([phrase for phrase in targets if phrase in body and not is_safe_risk_context(body, phrase)]))

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


def ending_check(body, ending_type="관리 철학형", include_philosophy=True, philosophy_text=""):
    issues = []
    score = 10
    ending = body[-600:]

    if len(ending.strip()) < 180:
        issues.append(("마무리 짧음", "마무리에서 독자 행동 기준이나 관리 방향을 조금 더 정리하면 좋습니다."))
        score -= 3

    action_words = ["확인", "상담", "점검", "관리", "살펴", "조절", "찾아"]
    if ending_type in ["상담 유도형", "부드러운 CTA형"] and not any(w in ending for w in action_words):
        issues.append(("행동 유도 약함", "선택한 마무리 방식상 독자가 다음에 무엇을 하면 좋을지 한 문장 정도 필요합니다."))
        score -= 2

    philosophy_words = ["중요하게 생각", "지향", "철학", "원칙", "무리", "편안", "균형", "정직", "섬세"]
    if include_philosophy and ending_type != "철학 없이 정보 마무리":
        if not any(w in ending for w in philosophy_words):
            issues.append(("철학 반영 부족", "마지막 문단에 원장의 관리 철학이나 상담 기준이 약합니다."))
            score -= 3
        if philosophy_text:
            key_tokens = [w for w in re.findall(r"[가-힣A-Za-z0-9]{2,}", philosophy_text) if w not in ["피부", "관리", "생각합니다", "중요하게"]]
            if key_tokens and not any(t in ending for t in key_tokens[:5]):
                issues.append(("입력 철학 미반영", "입력한 철학 문구의 핵심 표현이 마지막 문단에 충분히 반영되지 않았습니다."))
                score -= 2

    if ending_type == "체크리스트 요약형" and not any(w in ending for w in ["첫째", "둘째", "정리하면", "기억해"]):
        issues.append(("요약형 마무리 부족", "체크리스트 요약형이면 마지막에 핵심 기준 2~3개를 정리해주는 문장이 좋습니다."))
        score -= 2

    return issues, max(score, 0)


def price_estimate(score):
    if score >= 94:
        return "5만 원 이상 포트폴리오급"
    if score >= 92:
        return "4~5만 원 테스트 합격권"
    if score >= 88:
        return "3~4만 원 실무 가능권"
    if score >= 82:
        return "부분 보완 필요"
    return "초안 재작성 권장"


def show_issues(title, issues):
    st.write(f"### {title}")
    if not issues:
        st.success("통과")
    else:
        for name, desc in issues:
            st.warning(f"**{name}** — {desc}")


st.title("📝 달로썸 원고 검수기 v3.4")
st.caption("검수 전용 보정 버전입니다. 달로썸 8가지 도입 방식과 마지막 문단 철학 반영까지 봅니다.")

with st.sidebar:
    st.header("원고 조건")
    purpose = st.selectbox("원고 목적", PURPOSES, index=0)
    field = st.selectbox("분야", FIELDS, index=0)
    writer_perspective = st.selectbox("작성자 관점", WRITER_PERSPECTIVES, index=0)
    keyword = st.text_input("키워드", value="복합성 피부 좋아지는 방법")
    title_input = st.text_input("제목", placeholder="제목을 따로 넣거나, 본문 첫 줄에 넣어도 됩니다.")
    intro_type = st.selectbox("도입 방식", INTRO_TYPES, index=0)
    ending_type = st.selectbox("마무리 방식", ENDING_TYPES, index=0)
    include_philosophy = st.checkbox("마지막 문단에 철학/강점 반영", value=True)
    philosophy_text = st.text_area("철학/강점 문구", value=default_philosophy_by_field(field, writer_perspective), height=100)
    target_len_min = st.number_input("권장 최소 글자수(공백 제외)", min_value=800, max_value=3000, value=1300, step=100)
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
    st.caption(f"선택한 달로썸 도입 방식: {intro_type} / 마무리 방식: {ending_type} / 철학 반영: {'예' if include_philosophy else '아니오'}")

    title_issues, title_score = title_check(title, keyword)
    body_issues, body_score, no_space_len, body_kw_count, total_kw_count, subhead_count = body_seo_check(body, keyword, target_len_min, target_len_max, title)
    intro_issues, intro_score, detected_intro_types = intro_check(body, intro_type)
    ai_issues, ai_score = ai_smell_check(body)
    compliance_issues, compliance_score = compliance_check(body, field, purpose)
    persona_issues, persona_score = persona_check(body, writer_perspective)
    ending_issues, ending_score = ending_check(body, ending_type, include_philosophy, philosophy_text)
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
    metric_cols[1].metric("키워드 횟수", f"본문 {body_kw_count} / 제목포함 {total_kw_count}")
    metric_cols[2].metric("소제목 수", subhead_count)
    metric_cols[3].metric("감지 도입", ", ".join(detected_intro_types) if detected_intro_types else "없음")

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

    st.write("### 보완 문장 제안")
    intro_examples = {
        "1. 독자의 상황을 찔러주는 체크리스트 활용": "☑ 아침엔 볼이 당기는데 오후엔 T존이 번들거린다 / ☑ 수분크림은 답답하고 안 바르면 건조하다 / ☑ 지성인지 건성인지 헷갈린다",
        "2. 비교 표 활용": "비교 표 예시: T존은 피지 정리 중심, U존은 수분과 보호감 중심으로 나누어 관리합니다.",
        "3. 대화체 문구": "대화체 예시: “원장님, 저는 지성인가요 건성인가요?” 에스테틱 현장에서 정말 자주 듣는 질문입니다.",
        "4. 뉴스 기사 활용": "뉴스 기사 활용 예시: 최근 여름철 자외선 차단과 피부 관리에 대한 관심이 높아지면서, 자외선 차단제 사용법을 다시 확인하는 분들이 많습니다.",
        "5. 독자에게 질문 던지기": "질문형 예시: 아침에는 볼이 당기는데 오후에는 코와 이마가 번들거린다면, 내 피부를 단순히 지성이라고 봐도 될까요?",
        "6. 많이 묻는 질문 인용": "FAQ 인용 예시: “저는 피부가 지성인지 건성인지 모르겠어요.” 복합성 피부 상담에서 가장 많이 나오는 질문 중 하나입니다.",
        "7. 검색만으로는 모르는 알짜 정보 예고": "알짜 정보 예시: 검색하면 제품 추천은 많지만, 실제 관리에서는 어느 부위에 어떤 제형을 얼마나 쓰는지가 더 중요합니다.",
        "8. 간단한 웹툰 만들어 넣기": "웹툰 예시: 1컷: 아침엔 볼이 당기는 고객 / 2컷: 오후엔 T존이 번들거리는 고객 / 3컷: 원장이 부위별 관리법을 설명하는 장면",
    }
    st.info(intro_examples.get(intro_type, "선택한 도입 방식에 맞춰 첫 문단을 보완하세요."))

    if include_philosophy and ending_type != "철학 없이 정보 마무리":
        st.info("마무리 철학 예시: 에스테틱 관리는 피부를 무리하게 바꾸는 일이 아니라, 지금 피부가 편안하게 받아들일 수 있는 균형을 찾는 과정이라고 생각합니다.")

    st.write("## 제출 판단")
    if total >= 92:
        st.success("제출 가능권입니다. 오탈자와 줄바꿈만 확인하세요.")
    elif total >= 88:
        st.info("실무 가능권입니다. 한두 문장만 보완하면 제출권에 가깝습니다.")
    elif total >= 82:
        st.warning("부분 보완 필요입니다. 재작성까지는 아니고 길이/키워드/도입만 손보세요.")
    else:
        st.error("재작성 권장입니다. 구조부터 다시 잡는 편이 빠릅니다.")
else:
    st.info("왼쪽 조건을 입력하고 원고를 붙여넣은 뒤 검수 시작을 누르세요.")
