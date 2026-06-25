
import re
import hashlib
import pandas as pd
import streamlit as st

st.set_page_config(page_title="달로썸 원고 검수기 v6.4", layout="wide")

PURPOSES = [
    "마케팅 회사 테스트 원고",
    "포트폴리오용 샘플 원고",
    "실제 에스테틱 광고 원고",
    "실제 병원 광고 원고",
    "실제 법률 광고 원고",
    "일반 정보성 원고",
]

FIELDS = ["에스테틱 / 피부관리", "병원 / 의료", "법률", "청소 / 홈케어", "생활용품", "학원 / 교육", "인테리어 / 리모델링", "보험 / 금융 / 부동산", "맛집 / 여행 / 숙박", "기타 전문업종"]
WRITER_PERSPECTIVES = ["에스테틱 원장", "피부과 원장/전문의", "변호사", "전문업종 대표", "정보성 블로그 작성자"]

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
INTRO_TYPE_OPTIONS = ["자동 추천"] + INTRO_TYPES

TITLE_TYPES = [
    "1. 숫자/데이터 활용형",
    "2. 질문형",
    "3. 긴급성/한정성 강조형",
    "4. 궁금증 자극형",
    "5. 반전/의외성형",
    "6. 독자 상황 콕집기형",
]
TITLE_TYPE_OPTIONS = ["선택 안함", "자동 추천"] + TITLE_TYPES

ENDING_TYPES = ["관리 철학형", "상담 유도형", "체크리스트 요약형", "부드러운 CTA형", "철학 없이 정보 마무리"]

RISK_COMMON = ["100%", "무조건", "반드시 개선", "확실히 개선", "완벽하게", "부작용 없음", "효과 보장", "즉시 효과", "영구적", "완치", "최고", "유일한", "단 하나"]
RISK_FIELD = {
    "에스테틱 / 피부관리": ["치료", "진단", "처방", "의료진", "병변", "질환 치료", "재생된다", "무조건 좋아집니다"],
    "병원 / 의료": ["완치", "부작용 없음", "통증 없음", "흉터 없음", "재발 없음", "무조건 개선", "100% 개선"],
    "법률": ["무조건 승소", "반드시 승소", "100% 승소", "확실히 받아냅니다", "무조건 받을 수 있습니다"],
}
AI_PATTERNS = ["이 글에서는", "오늘은", "알아보겠습니다", "설명드리겠습니다", "중요합니다", "필요합니다", "도움이 됩니다", "도움이 될 수 있습니다", "확인해야 합니다", "정리해보겠습니다", "살펴보겠습니다"]
GLOSSARY_TERMS = {
    "에스테틱 / 피부관리": ["T존", "U존", "유수분", "피부 장벽", "각질", "피지", "자외선 차단제", "홈케어"],
    "병원 / 의료": ["진피", "표피", "염증", "색소침착", "회복기간", "부작용"],
    "법률": ["소멸시효", "지급명령", "가압류", "집행권원", "입증", "내용증명"],
}


def dynamic_widget_key(prefix, *parts):
    """입력값이 바뀌면 복붙용 텍스트 영역도 새로 갱신되도록 하는 위젯 키."""
    raw = "||".join(str(x) for x in parts)
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def _has_jongseong(word):
    """한글 마지막 글자 받침 여부를 간단히 확인한다."""
    word = (word or "").strip()
    for ch in reversed(word):
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            return (code - 0xAC00) % 28 != 0
    return False


def _josa(word, with_jong, without_jong):
    return with_jong if _has_jongseong(word) else without_jong


def fix_topic_josa(text, topic):
    """리라이트 생성문에서 '써마지을' 같은 조사 오류를 줄인다."""
    topic = (topic or "").strip()
    if not topic:
        return text
    repl = {
        f"{topic}은": f"{topic}{_josa(topic, '은', '는')}",
        f"{topic}을": f"{topic}{_josa(topic, '을', '를')}",
        f"{topic}이": f"{topic}{_josa(topic, '이', '가')}",
        f"{topic}과": f"{topic}{_josa(topic, '과', '와')}",
    }
    for a, b in repl.items():
        text = text.replace(a, b)
    return text


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
        return "", "", "없음"
    first = lines[0]
    if first.startswith("#"):
        return first.lstrip("#").strip(), "\n".join(lines[1:]).strip(), "본문 첫 줄"
    m = re.match(r"^제목\s*[:：]\s*(.+)$", first)
    if m:
        return m.group(1).strip(), "\n".join(lines[1:]).strip(), "본문 제목표기"
    if len(first) <= 40 and not first.endswith(("다.", "요.", "니다.", "죠.", "?")):
        return first, "\n".join(lines[1:]).strip(), "본문 첫 줄 자동추출"
    return "", draft.strip(), "없음"


def count_keyword(text, keyword):
    return text.count(keyword) if keyword else 0


def keyword_count_range_by_length(target_len):
    """Return recommended total/body keyword count ranges by target length.
    The goal is to avoid obvious repetition in short test manuscripts.
    """
    try:
        n = int(target_len)
    except Exception:
        n = 1500
    if n <= 1200:
        return (3, 5, 2, 4)  # total min/max, body min/max
    if n <= 1800:
        return (4, 6, 3, 5)
    if n <= 2400:
        return (5, 7, 4, 6)
    return (6, 9, 5, 8)


def keyword_count_instruction(keyword, target_len):
    kw = keyword or "핵심 키워드"
    tmin, tmax, bmin, bmax = keyword_count_range_by_length(target_len)
    return f"""[키워드 반복 제한]
- 핵심 키워드 “{kw}”는 제목에 1회만 넣는다.
- 본문에서는 “{kw}”를 {bmin}~{bmax}회 정도만 자연스럽게 사용한다.
- 제목 포함 전체 키워드 횟수는 {tmin}~{tmax}회 안팎을 목표로 한다.
- 같은 문단에서 키워드를 반복하지 말고, 대명사나 자연스러운 표현으로 풀어쓴다.
- 분량을 맞추기 위해 키워드를 반복하지 않는다."""


DELIVERY_MODES = ["테스트 원고", "실제 업로드 원고", "카페 업로드 알바", "병원 블로그", "법률 블로그", "일반 정보글"]
COUNT_MODE_OPTIONS = ["제목 포함 전체 기준", "본문만 기준", "제목+본문 별도 기준"]
KEYWORD_FORM_OPTIONS = ["정확히 일치", "띄어쓰기 차이 인정", "변형 키워드 허용"]
SUBTITLE_COUNT_OPTIONS = ["소제목 제외", "소제목 포함"]
ENDING_KEYWORD_OPTIONS = ["권장", "필수", "상관없음"]


def auto_keyword_defaults(target_len):
    tmin, tmax, bmin, bmax = keyword_count_range_by_length(target_len)
    return {"total_min": tmin, "total_max": tmax, "body_min": bmin, "body_max": bmax}


def render_keyword_delivery_settings(prefix, keyword, target_len, expanded=False):
    defaults = auto_keyword_defaults(target_len)
    with st.expander("0. 기본 납품 설정 / 키워드 배치 기준", expanded=expanded):
        mode = st.selectbox("작업 모드", DELIVERY_MODES, index=0, key=f"{prefix}_delivery_mode")
        use_custom = st.checkbox("키워드 요구사항 직접 설정", value=True, key=f"{prefix}_kw_custom")
        c1, c2 = st.columns(2)
        with c1:
            count_mode = st.selectbox("키워드 카운트 기준", COUNT_MODE_OPTIONS, index=0, key=f"{prefix}_count_mode")
            title_required = st.checkbox("제목에 핵심 키워드 1회 필수", value=True, key=f"{prefix}_title_required")
            first_required = st.checkbox("첫 문단에 키워드 1회 필수", value=True, key=f"{prefix}_first_required")
            ending_policy = st.selectbox("마지막 문단 키워드", ENDING_KEYWORD_OPTIONS, index=0, key=f"{prefix}_ending_policy")
        with c2:
            subtitle_policy = st.selectbox("소제목 키워드 카운트", SUBTITLE_COUNT_OPTIONS, index=0, key=f"{prefix}_subtitle_policy")
            keyword_form = st.selectbox("키워드 형태", KEYWORD_FORM_OPTIONS, index=0, key=f"{prefix}_keyword_form")
            paragraph_max = st.number_input("한 문단 키워드 최대 횟수", min_value=1, max_value=5, value=1, step=1, key=f"{prefix}_paragraph_max")
        c3, c4, c5, c6 = st.columns(4)
        with c3:
            body_min = st.number_input("본문 최소", min_value=0, max_value=30, value=defaults["body_min"], step=1, key=f"{prefix}_body_min")
        with c4:
            body_max = st.number_input("본문 최대", min_value=0, max_value=30, value=defaults["body_max"], step=1, key=f"{prefix}_body_max")
        with c5:
            total_min = st.number_input("전체 최소", min_value=0, max_value=40, value=defaults["total_min"], step=1, key=f"{prefix}_total_min")
        with c6:
            total_max = st.number_input("전체 최대", min_value=0, max_value=40, value=defaults["total_max"], step=1, key=f"{prefix}_total_max")
        st.caption("외주/테스트 요구가 있으면 여기 숫자를 그대로 맞추세요. 요구가 없으면 자동값을 써도 됩니다.")
    return {
        "mode": mode,
        "use_custom": use_custom,
        "count_mode": count_mode,
        "title_required": title_required,
        "first_required": first_required,
        "ending_policy": ending_policy,
        "subtitle_policy": subtitle_policy,
        "keyword_form": keyword_form,
        "paragraph_max": int(paragraph_max),
        "body_min": int(body_min),
        "body_max": int(body_max),
        "total_min": int(total_min),
        "total_max": int(total_max),
    }


def keyword_delivery_setting_text(keyword, target_len, settings=None):
    kw = keyword or "핵심 키워드"
    if not settings or not settings.get("use_custom", True):
        return keyword_count_instruction(kw, target_len)
    return f"""[기본 납품 설정 / 키워드 요구사항]
- 작업 모드: {settings.get('mode', '테스트 원고')}
- 핵심 키워드: “{kw}”
- 카운트 기준: {settings.get('count_mode', '제목 포함 전체 기준')}
- 제목 키워드: {'제목에 1회 필수' if settings.get('title_required') else '제목 필수 아님'}
- 본문 키워드 횟수: {settings.get('body_min')}~{settings.get('body_max')}회
- 전체 키워드 횟수: {settings.get('total_min')}~{settings.get('total_max')}회
- 첫 문단 키워드: {'1회 필수' if settings.get('first_required') else '필수 아님'}
- 마지막 문단 키워드: {settings.get('ending_policy', '권장')}
- 소제목 카운트: {settings.get('subtitle_policy', '소제목 제외')}
- 키워드 형태: {settings.get('keyword_form', '정확히 일치')}
- 한 문단 키워드 최대 횟수: {settings.get('paragraph_max', 1)}회
- 같은 문단에서 키워드를 반복하지 말고, 필요한 경우 ‘이 절차’, ‘해당 시술’, ‘진료 과정’, ‘상담 과정’, ‘이 방법’처럼 자연스럽게 대체한다.
- 키워드가 빠진 문단이 있으면 전체를 다시 쓰지 말고, 해당 문단 안의 기존 문장 1개에 키워드 1회만 자연스럽게 연결한다."""


def keyword_placement_plan_text(keyword, target_len, settings=None):
    kw = keyword or "핵심 키워드"
    if not settings:
        tmin, tmax, bmin, bmax = keyword_count_range_by_length(target_len)
        settings = {"body_min": bmin, "body_max": bmax, "total_min": tmin, "total_max": tmax, "title_required": True, "first_required": True, "ending_policy": "권장", "paragraph_max": 1}
    return f"""[키워드 배치 지도]
- 제목: “{kw}” 1회 배치 {'필수' if settings.get('title_required') else '권장'}
- 도입/첫 문단: “{kw}” 1회 배치 {'필수' if settings.get('first_required') else '권장'}
- 본문 중간 문단: 문단별 0~1회로 분산 배치
- 마무리: “{kw}” 1회 배치 {settings.get('ending_policy', '권장')}
- 본문 총량: {settings.get('body_min')}~{settings.get('body_max')}회
- 제목 포함 전체 총량: {settings.get('total_min')}~{settings.get('total_max')}회
- 한 문단에 “{kw}”가 {settings.get('paragraph_max', 1)}회를 넘으면 반복으로 보일 수 있으므로 대체어를 사용한다.

권장 위치 예시:
1) 제목 1회
2) 도입 마지막 문장 또는 도입 중반 1회
3) 본문1 중간 1회
4) 본문2 또는 본문3 중간 1회
5) 마무리 첫 문장 또는 마지막 문장 0~1회"""


def is_heading_block(block):
    block = (block or "").strip()
    if not block:
        return False
    if block.startswith("#"):
        return True
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if len(lines) != 1:
        return False
    line = re.sub(r"^#+\s*", "", lines[0]).strip()
    if len(line) > 42:
        return False
    if line.endswith(("다.", "요.", "니다.", "죠.", "습니다.", ".")):
        return False
    return True


def split_keyword_sections(body):
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body or "") if b.strip()]
    sections = []
    current = None
    for b in blocks:
        if is_heading_block(b):
            if current:
                sections.append(current)
            current = {"heading": re.sub(r"^#+\s*", "", b).strip(), "text": ""}
        else:
            if current is None:
                current = {"heading": "도입", "text": b}
            else:
                current["text"] = (current["text"] + "\n" + b).strip() if current["text"] else b
    if current:
        sections.append(current)
    if not sections and body.strip():
        sections = [{"heading": "도입", "text": body.strip()}]
    n = len(sections)
    for i, sec in enumerate(sections):
        if i == 0:
            sec["role"] = "도입"
        elif i == n - 1 and n >= 3:
            sec["role"] = "마무리"
        else:
            sec["role"] = f"본문{i}"
    return sections


def keyword_count_loose(text, keyword, form_policy="정확히 일치"):
    if not keyword:
        return 0
    text = text or ""
    if form_policy == "띄어쓰기 차이 인정":
        return re.sub(r"\s+", "", text).count(re.sub(r"\s+", "", keyword))
    return text.count(keyword)


def build_keyword_insertion_prompt(keyword, missing_sections):
    if not keyword or not missing_sections:
        return ""
    blocks = []
    for sec in missing_sections:
        text = (sec.get("text") or "").strip()
        if len(text) > 1200:
            text = text[:1200] + "..."
        blocks.append(f"""[{sec.get('role')} / {sec.get('heading')}]
{text}""")
    joined = "\n\n".join(blocks)
    return f"""아래 원고에서 키워드가 빠진 문단만 부분 수정해줘.

핵심 키워드: “{keyword}”

수정 조건:
1. 아래 표시된 문단 안에만 핵심 키워드 “{keyword}”를 정확히 1회 추가해줘.
2. 문단 전체를 다시 쓰지 말고, 기존 문장 1개에 자연스럽게 연결해줘.
3. 새 문단을 만들지 마.
4. 키워드 추가 외에는 말투와 구조를 크게 바꾸지 마.
5. 같은 문단에 키워드를 2회 이상 넣지 마.
6. 키워드가 들어간 수정 문장만 먼저 보여주고, 필요하면 수정된 문단도 함께 보여줘.

수정할 문단:
{joined}"""


def keyword_placement_report(title, body, keyword, settings=None):
    if not keyword:
        return "키워드가 없어 배치 검수를 건너뜁니다.", ""
    settings = settings or {}
    form_policy = settings.get("keyword_form", "정확히 일치")
    subtitle_included = settings.get("subtitle_policy", "소제목 제외") == "소제목 포함"
    title_count = keyword_count_loose(title, keyword, form_policy)
    sections = split_keyword_sections(body)
    rows = []
    body_count = 0
    missing_sections = []
    over_sections = []
    max_per = int(settings.get("paragraph_max", 1) or 1)
    for idx, sec in enumerate(sections):
        hcnt = keyword_count_loose(sec.get("heading", ""), keyword, form_policy)
        tcnt = keyword_count_loose(sec.get("text", ""), keyword, form_policy)
        effective = hcnt + tcnt if subtitle_included else tcnt
        body_count += effective
        rows.append({"구간": sec.get("role"), "소제목": sec.get("heading"), "소제목 횟수": hcnt, "본문 횟수": tcnt, "판정용 횟수": effective})
        if tcnt == 0 and sec.get("text", "").strip():
            if idx == 0 and settings.get("first_required"):
                missing_sections.append(sec)
            elif sec.get("role") == "마무리" and settings.get("ending_policy") == "필수":
                missing_sections.append(sec)
            elif sec.get("role", "").startswith("본문"):
                missing_sections.append(sec)
        if effective > max_per:
            over_sections.append(sec)
    total_count = title_count + body_count
    no_space_len = len(re.sub(r"\s+", "", body or ""))
    tmin, tmax, bmin, bmax = keyword_count_range_by_length(no_space_len)
    body_min = int(settings.get("body_min", bmin))
    body_max = int(settings.get("body_max", bmax))
    total_min = int(settings.get("total_min", tmin))
    total_max = int(settings.get("total_max", tmax))
    lines = []
    lines.append("### 키워드 배치 결과")
    lines.append(f"- 제목: {title_count}회 {'✅' if (not settings.get('title_required', True) or title_count == 1) else '⚠️'}")
    lines.append(f"- 본문 기준: {body_count}회 / 요구 {body_min}~{body_max}회")
    lines.append(f"- 제목 포함 전체: {total_count}회 / 요구 {total_min}~{total_max}회")
    lines.append(f"- 소제목 카운트 기준: {settings.get('subtitle_policy', '소제목 제외')}")
    lines.append("")
    lines.append("|구간|소제목|소제목 횟수|본문 횟수|판정용 횟수|")
    lines.append("|---|---|---:|---:|---:|")
    for r in rows:
        safe_heading = str(r['소제목']).replace('|', '/')
        lines.append(f"|{r['구간']}|{safe_heading}|{r['소제목 횟수']}|{r['본문 횟수']}|{r['판정용 횟수']}|")
    lines.append("")
    verdict = []
    if settings.get("title_required", True) and title_count != 1:
        verdict.append("제목에 키워드가 정확히 1회 들어가야 합니다.")
    if body_count < body_min:
        verdict.append(f"본문 키워드가 {body_min - body_count}회 부족합니다.")
    if body_count > body_max:
        verdict.append(f"본문 키워드가 {body_count - body_max}회 많습니다.")
    if total_count < total_min:
        verdict.append(f"전체 키워드가 {total_min - total_count}회 부족합니다.")
    if total_count > total_max:
        verdict.append(f"전체 키워드가 {total_count - total_max}회 많습니다.")
    if missing_sections:
        verdict.append("키워드가 빠진 문단이 있습니다: " + ", ".join([m.get("role", "문단") for m in missing_sections[:5]]))
    if over_sections:
        verdict.append("키워드가 한 문단에 몰린 구간이 있습니다: " + ", ".join([m.get("role", "문단") for m in over_sections[:5]]))
    if not verdict:
        verdict.append("키워드 횟수와 위치가 대체로 안정적입니다.")
    lines.append("판정: " + " / ".join(verdict))
    insertion_prompt = build_keyword_insertion_prompt(keyword, missing_sections[:3])
    return "\n".join(lines), insertion_prompt


def detect_intro_types(body):
    intro = body.strip()[:900]
    detected = []

    list_lines = [l for l in intro.splitlines() if l.strip().startswith(("-", "·", "•", "✓", "✔", "☑", "□"))]
    if "☑" in intro or "□" in intro or len(list_lines) >= 2:
        detected.append("1. 독자의 상황을 찔러주는 체크리스트 활용")

    if "|" in intro or ("구분" in intro and ("T존" in intro or "U존" in intro or "차이" in intro)):
        detected.append("2. 비교 표 활용")

    if any(w in intro for w in ['"저는', '"혹시', '"왜', '"어떻게', "라고 하시는", "라고 묻는", "하시죠", "있으실 거예요", "아시나요"]):
        detected.append("3. 대화체 문구")

    if any(w in intro for w in ["뉴스", "기사", "보도", "최근", "언론", "자료에 따르면"]):
        detected.append("4. 뉴스 기사 활용")

    if "?" in intro or "않으신가요" in intro or "적 있으" in intro or "궁금" in intro:
        detected.append("5. 독자에게 질문 던지기")

    quoted_questions = re.findall(r'["“][^"”]{2,90}\?[^"”]*["”]', intro)
    faq_markers = [
        "많이 받는 질문", "자주 받는 질문", "많이 묻는", "자주 묻는", "FAQ", "질문 중 하나",
        "질문을 많이", "질문을 정말 많이", "질문도 많이", "많이 듣", "자주 듣", "물어보시는 분", "궁금해하시는 분"
    ]
    if any(w in intro for w in faq_markers) or len(quoted_questions) >= 2:
        detected.append("6. 많이 묻는 질문 인용")

    if any(w in intro for w in ["검색만으로", "잘 알려지지", "알짜", "놓치기 쉬운", "이 부분을 모르면", "여기서 알 수"]):
        detected.append("7. 검색만으로는 모르는 알짜 정보 예고")

    if any(w in intro for w in ["웹툰", "컷", "만화", "그림", "장면", "[컷", "1컷", "2컷"]):
        detected.append("8. 간단한 웹툰 만들어 넣기")

    return detected



def detect_title_types(title):
    """제목이 어떤 클릭 유도 방식에 가까운지 감지한다."""
    title = title or ""
    detected = []
    if re.search(r"\d", title) or any(w in title for w in ["가지", "분", "개", "단계"]):
        detected.append("1. 숫자/데이터 활용형")
    if "?" in title or any(w in title for w in ["일까요", "할까요", "가능할까요", "왜", "어떻게", "언제"]):
        detected.append("2. 질문형")
    if any(w in title for w in ["지금", "오늘", "꼭", "놓치면", "늦기 전", "초기", "주의", "확인해야"]):
        detected.append("3. 긴급성/한정성 강조형")
    if any(w in title for w in ["이유", "비밀", "진짜", "따로", "놓친", "모르는", "알아야", "차이", "기준"]):
        detected.append("4. 궁금증 자극형")
    if any(w in title for w in ["오해", "진실", "예상과 달리", "의외", "반전", "사실은", "다를까요"]):
        detected.append("5. 반전/의외성형")
    if any(w in title for w in ["중이신가요", "계신가요", "때", "후", "앞두고", "반복", "고민", "걱정", "저림", "통증", "따갑", "붓기", "냄새", "못했을 때"]):
        detected.append("6. 독자 상황 콕집기형")
    return detected


def title_style_instruction(title_type):
    if not title_type or title_type == "선택 안함":
        return "특정 제목 유형을 강제하지 않는다. 다만 키워드 앞 배치, 30자 이내, 어그로 금지 등 제목 기본 기준은 유지한다."
    if title_type == "자동 추천":
        return "제목 유형은 자료와 주제에 맞춰 6가지 방식 중 하나를 자연스럽게 선택한다."
    mapping = {
        "1. 숫자/데이터 활용형": "제목에 3가지, 5가지, 6가지, 3분처럼 구체적인 숫자를 넣어 기준이 분명해 보이게 한다.",
        "2. 질문형": "독자가 실제로 궁금해할 질문 형태로 제목을 만든다. 단, 답과 다른 어그로성 질문은 피한다.",
        "3. 긴급성/한정성 강조형": "지금 확인해야 할 이유를 넣되, 병원·법률에서는 과장·공포 조장 없이 ‘확인할 기준’ 수준으로 표현한다.",
        "4. 궁금증 자극형": "답을 모두 드러내지 않고 이유, 기준, 차이, 놓치기 쉬운 점을 예고한다.",
        "5. 반전/의외성형": "독자가 당연하다고 생각한 부분의 오해나 의외성을 제목에 반영한다. 사실과 다른 반전은 만들지 않는다.",
        "6. 독자 상황 콕집기형": "특정 증상, 상황, 고민을 제목에 직접 넣어 ‘내 이야기’처럼 느끼게 한다.",
    }
    return mapping.get(title_type, "선택한 제목 유형을 유지한다.")


def recommend_title_style(field, topic, keyword, research_text):
    text = " ".join([field or "", topic or "", keyword or "", research_text or ""])
    if any(w in text for w in ["자가", "체크", "검사", "기준", "방법", "주의사항", "준비", "증거"]):
        return "1. 숫자/데이터 활용형"
    if any(w in text for w in ["차이", "비교", "vs", "VS", "울쎄라", "인모드", "슈링크", "써마지"]):
        return "2. 질문형"
    if any(w in text for w in ["경찰조사", "내용증명", "소멸시효", "초기", "방치", "오늘", "기한", "기간"]):
        return "3. 긴급성/한정성 강조형"
    if any(w in text for w in ["오해", "진실", "예상", "의외", "다를까요", "반전"]):
        return "5. 반전/의외성형"
    if any(w in text for w in ["통증", "저림", "붓기", "따갑", "냄새", "얼룩", "외도", "못했을 때", "걱정", "불안"]):
        return "6. 독자 상황 콕집기형"
    return "4. 궁금증 자극형"


def clean_title_candidate(title, keyword):
    title = re.sub(r"\s+", " ", title).strip()
    # 제목은 가능하면 키워드로 시작하게 보정
    if keyword and not title.startswith(keyword):
        title = f"{keyword} {title}"
    # 너무 긴 경우 불필요한 말 줄이기
    title = title.replace("확인해야 하는", "확인할").replace("알아야 하는", "알아둘")
    return title.strip()


def generate_title_candidates(keyword, topic, title_type, b_lines=None, field=""):
    kw = (keyword or topic or "키워드").strip()
    if not title_type or title_type == "선택 안함":
        title_type = "기본형"
    elif title_type == "자동 추천":
        title_type = "4. 궁금증 자극형"
    base_issue = ""
    if b_lines:
        base_issue = re.sub(r"^[-•·\d\.\)\s]+", "", str(b_lines[0])).strip()
    # 너무 구체적인 긴 문장은 제목에 직접 넣지 않고 흐름만 사용
    candidates_by_type = {
        "기본형": [
            f"{kw} 확인할 기준",
            f"{kw} 알아둘 점",
            f"{kw} 살펴볼 내용",
        ],
        "1. 숫자/데이터 활용형": [
            f"{kw} 확인할 기준 5가지",
            f"{kw} 증상 체크 3가지",
            f"{kw} 상담 전 볼 5가지",
        ],
        "2. 질문형": [
            f"{kw} 언제 확인해야 할까요",
            f"{kw} 왜 사람마다 다를까요",
            f"{kw} 내 상황에도 맞을까요",
        ],
        "3. 긴급성/한정성 강조형": [
            f"{kw} 지금 확인할 3가지",
            f"{kw} 늦기 전 볼 기준",
            f"{kw} 오늘 체크할 주의점",
        ],
        "4. 궁금증 자극형": [
            f"{kw} 놓치기 쉬운 기준",
            f"{kw} 결과가 다른 이유",
            f"{kw} 선택 전 알아둘 점",
        ],
        "5. 반전/의외성형": [
            f"{kw} 흔한 오해와 진실",
            f"{kw} 예상과 다른 이유",
            f"{kw} 당연하지 않은 기준",
        ],
        "6. 독자 상황 콕집기형": [
            f"{kw} 이런 증상이라면 확인",
            f"{kw} 고민 중이라면 기준부터",
            f"{kw} 반복된다면 살펴볼 점",
        ],
    }
    out = candidates_by_type.get(title_type, candidates_by_type["4. 궁금증 자극형"])
    if base_issue and len(base_issue) <= 20:
        out.append(f"{kw} {base_issue}부터 확인")
    # 키워드 앞, 30자 안팎을 우선하지만 무리하게 잘라 의미를 망치지 않음
    cleaned = []
    for c in out:
        c = clean_title_candidate(c, kw)
        if c not in cleaned:
            cleaned.append(c)
    return cleaned[:5]

def is_safe_risk_context(body, phrase):
    """위험 단어가 부정/주의 문맥에서 쓰인 경우는 오탐으로 보지 않는다."""
    common_safe_markers = [
        "아니", "않", "없", "피하", "주의", "권하지", "권하기보다", "단정", "어렵", "어려",
        "볼 수는 없습니다", "볼 수 없습니다", "말하기 어렵", "말하기는 어렵", "무조건 없애", "무조건 두껍"
    ]
    for match in re.finditer(re.escape(phrase), body):
        window = body[max(0, match.start() - 35): min(len(body), match.end() + 55)]
        if phrase == "무조건":
            safe_phrases = [
                "무조건 더 좋다고 말하기", "무조건 더 좋다고", "무조건 좋은", "무조건 권", "무조건 선택",
                "무조건 효과", "무조건 개선", "무조건 좋아"  # 아래에서 위험 문맥과 구분
            ]
            # 위험 문맥: 무조건 효과/개선/좋아짐 등은 그대로 위험 처리
            if any(x in window for x in ["무조건 효과", "무조건 개선", "무조건 좋아", "무조건 낫", "무조건 받을", "무조건 승소"]):
                return False
        if any(marker in window for marker in common_safe_markers):
            return True
    return False



def extract_first_content_sentence(body):
    """마크다운 제목/소제목을 건너뛰고 실제 본문 첫 문장을 추출한다."""
    body = body or ""
    lines = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        # 제목/소제목/라벨/표 구분선은 첫 문장 후보에서 제외
        if line.startswith("#"):
            continue
        if re.match(r"^[-*|:\s]+$", line):
            continue
        if re.match(r"^(제목 후보|최종 제목|본문)\s*[:：]?\s*$", line):
            continue
        # 너무 짧은 소제목성 문장은 건너뜀
        if len(line) <= 34 and not line.endswith(("다.", "요.", "죠.", "까?", "나요?", "세요?", "습니까?", "?", "!")):
            continue
        lines.append(line)
        if len(" ".join(lines)) > 250:
            break
    text = " ".join(lines).strip()
    text = re.sub(r"[*_`>#]", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    if not text:
        return ""
    m = re.search(r"(.{8,180}?(?:\?|!|다\.|요\.|죠\.|니다\.|까요\?|나요\?|세요\?|습니까\?))", text)
    if m:
        return m.group(1).strip()
    return text[:120].strip()

B_CONCERN_STOPWORDS = set("""
독자 사람들이 실제 반복 질문 불안 포인트 판단 어려운 지점 비용 효과 부작용 기간 선택 고민 요약 경우 자료 내용 원고 제목 도입 본문 마무리 설명 확인 필요 중요 과정 방식 방향 상담 의료진 병원 주제 핵심 관련 중심 가능 정도 여러 같은 먼저 이후 현재 이런 저런 하면 하기 대한 대해 있다 없다 있는 없는 된다 됩니다 합니다 합니다 궁금해한다 궁금해하는
""".split())
B_CONCERN_KEEP = {
    "효과", "효과없", "효과 없음", "반응", "반응 없음", "약", "복용", "부작용", "통증", "붓기", "열감", "비용", "가격", "차이", "비교", "기간", "실패", "불안", "걱정", "헷갈", "망설", "기저질환", "당뇨", "고혈압", "심장", "협심증", "저혈압", "복용약", "정상", "부담", "한번", "한 번", "유지", "아침발기", "성욕", "스트레스"
}

def extract_b_concern_terms(text, keyword=""):
    """B등급 고민 요약에서 첫문장에 들어가야 할 핵심 고민어를 뽑는다."""
    text = (text or "").strip()
    if not text:
        return []
    terms = []
    # 띄어쓰기 있는 핵심 구문 먼저 보존
    phrase_patterns = [
        r"효과\s*(?:가\s*)?(?:없|안\s*나|안\s*보|부족|약하|기대)",
        r"약\s*(?:을\s*)?(?:먹|복용).{0,12}(?:효과|반응|부작용|걱정|불안)",
        r"부작용.{0,8}(?:걱정|불안|우려)",
        r"비용.{0,8}(?:부담|불안|걱정|대비)",
        r"가격.{0,8}(?:차이|부담|불안)",
        r"기저질환|당뇨|고혈압|심장질환|협심증|저혈압|복용약",
        r"통증|붓기|열감|볼패임|흉터|색소|감각",
        r"차이|비교|무엇이\s*다른|뭐가\s*다른",
        r"한\s*번|1회|언제부터|기간|유지기간",
    ]
    for pat in phrase_patterns:
        for m in re.finditer(pat, text):
            t = re.sub(r"\s+", " ", m.group(0)).strip()
            if 2 <= len(t) <= 28 and t not in terms:
                terms.append(t)
    # 단어 단위 보강
    for tok in re.findall(r"[가-힣A-Za-z0-9]{2,}", text):
        if tok in B_CONCERN_STOPWORDS:
            continue
        if keyword and tok == keyword:
            continue
        keep = tok in B_CONCERN_KEEP or any(k in tok for k in ["효과", "부작용", "통증", "붓", "비용", "가격", "차이", "비교", "불안", "걱정", "헷갈", "망설", "당뇨", "고혈압", "심장", "복용", "반응", "실패", "유지"])
        if keep and tok not in terms:
            terms.append(tok)
        if len(terms) >= 18:
            break
    return terms[:18]

def evaluate_first_sentence_grounding(first_sentence, b_concern_text, keyword=""):
    """첫문장이 B등급 고민어를 실제로 담는지 간단 평가한다."""
    first_sentence = first_sentence or ""
    terms = extract_b_concern_terms(b_concern_text, keyword)
    if not terms:
        return {"status": "no_source", "terms": [], "hits": [], "message": "B등급 고민 요약이 없어 첫문장 근거 검수를 건너뜁니다."}
    compact_first = re.sub(r"\s+", "", first_sentence)
    hits = []
    for t in terms:
        tt = re.sub(r"\s+", "", t)
        if tt and (tt in compact_first or t in first_sentence):
            hits.append(t)
    strong_hits = [h for h in hits if len(re.sub(r"\s+", "", h)) >= 3 or h in {"효과", "부작용", "비용", "가격", "통증", "붓기", "불안", "걱정", "당뇨", "고혈압"}]
    # 단순히 '약' 하나만 들어간 수준은 약함으로 본다.
    only_weak = hits and all(h in {"약", "치료", "상담"} for h in hits)
    if len(strong_hits) >= 2 or (len(strong_hits) >= 1 and ("?" in first_sentence or "계신가요" in first_sentence or "걱정" in first_sentence)):
        status = "ok"
        msg = f"첫문장이 B등급 고민어를 반영했습니다: {', '.join(hits[:5])}"
    elif hits and not only_weak:
        status = "weak"
        msg = f"첫문장에 B등급 고민어가 일부만 보입니다: {', '.join(hits[:5])}. 핵심 고민을 1개 더 넣으면 좋습니다."
    else:
        status = "missing"
        msg = f"첫문장에 B등급 고민 핵심어가 약합니다. 후보 고민어: {', '.join(terms[:8])}"
    return {"status": status, "terms": terms, "hits": hits, "message": msg}

def check_all(title, body, keyword, field, purpose, writer_perspective, selected_intro_type, selected_title_type, ending_type, include_philosophy, philosophy_text, min_len, max_len, first_sentence_type="자동 추천", b_concern_text=""):
    issues = {"제목": [], "본문": [], "도입": [], "AI티": [], "복사찌꺼기": [], "위험표현": [], "작성자 관점": [], "마무리": []}
    scores = {}
    no_space_len = len(re.sub(r"\s+", "", body))
    body_kw = count_keyword(body, keyword)
    total_kw = body_kw + count_keyword(title, keyword)
    detected_intro = detect_intro_types(body)
    detected_title = detect_title_types(title)

    # 제목
    title_score = 15
    if not title:
        issues["제목"].append(("제목 없음", "제목 입력칸 또는 본문 첫 줄에서 제목을 찾지 못했습니다."))
        title_score = 0
    else:
        if keyword and keyword not in title:
            issues["제목"].append(("제목 키워드 누락", f"제목에 키워드 '{keyword}'가 정확히 들어가지 않았습니다."))
            title_score -= 6
        elif keyword and not title.startswith(keyword):
            issues["제목"].append(("키워드 위치", "제목 키워드는 가능하면 맨 앞에 두는 것이 좋습니다."))
            title_score -= 2
        if len(title) > 30:
            issues["제목"].append(("제목 길이", f"제목이 {len(title)}자로 30자를 넘습니다."))
            title_score -= 3
        if selected_title_type and selected_title_type not in ("자동 추천", "선택 안함") and selected_title_type not in detected_title:
            issues["제목"].append(("제목 유형 불일치", f"선택한 제목 유형은 '{selected_title_type}'인데, 현재 감지된 유형은 {', '.join(detected_title) if detected_title else '뚜렷한 유형 없음'}입니다."))
            title_score -= 2
    scores["제목"] = max(title_score, 0)

    # 본문
    body_score = 20
    if no_space_len < 1200:
        issues["본문"].append(("본문 길이 부족", f"공백 제외 {no_space_len}자입니다. 최소 1,300자 이상 권장합니다."))
        body_score -= 6
    elif no_space_len < min_len:
        issues["본문"].append(("본문이 약간 짧음", f"공백 제외 {no_space_len}자입니다. 100~200자 보강하면 더 안정적입니다."))
        body_score -= 2
    elif no_space_len > max_len:
        issues["본문"].append(("본문이 김", f"공백 제외 {no_space_len}자입니다. 권장 최대 {max_len}자를 넘습니다."))
        body_score -= 4
    target_for_kw = (min_len + max_len) // 2 if min_len and max_len else no_space_len
    kw_min, kw_max, body_kw_min, body_kw_max = keyword_count_range_by_length(target_for_kw)
    if keyword and total_kw < kw_min:
        issues["본문"].append(("키워드 부족", f"제목 포함 키워드가 {total_kw}회입니다. 이 분량에서는 {kw_min}~{kw_max}회 안팎을 권장합니다."))
        body_score -= 3
    elif keyword and total_kw > kw_max + 3:
        issues["본문"].append(("키워드 과다", f"제목 포함 키워드가 {total_kw}회입니다. 이 분량에서는 {kw_min}~{kw_max}회 안팎이 자연스럽습니다."))
        body_score -= 3
    elif keyword and total_kw > kw_max:
        issues["본문"].append(("키워드 많음", f"제목 포함 키워드가 {total_kw}회입니다. 권장 {kw_min}~{kw_max}회보다 많아 1~2회 줄이면 더 자연스럽습니다."))
        body_score -= 1
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    subheads = [l for l in lines if len(l) <= 38 and not l.endswith(("다.", "요.", "니다.", "죠.", "?")) and not l.startswith("☑")]
    if len(subheads) < 3:
        issues["본문"].append(("소제목 부족", f"소제목으로 보이는 줄이 {len(subheads)}개입니다."))
        body_score -= 3
    scores["본문"] = max(body_score, 0)

    # 도입
    intro_score = 15
    intro = body[:900]
    first_sentence = extract_first_content_sentence(body)
    first_ground = evaluate_first_sentence_grounding(first_sentence, b_concern_text, keyword)
    if b_concern_text.strip():
        if first_ground["status"] == "missing":
            issues["도입"].append(("첫문장 B등급 고민 약함", first_ground["message"]))
            intro_score -= 4
        elif first_ground["status"] == "weak":
            issues["도입"].append(("첫문장 고민 반영 약함", first_ground["message"]))
            intro_score -= 2
    if first_sentence_type == "의문문 강제" and first_sentence and "?" not in first_sentence:
        issues["도입"].append(("첫문장 의문문 아님", "첫문장 형태를 의문문 강제로 선택했지만 실제 첫 문장에 물음표(?)가 없습니다."))
        intro_score -= 3
    if not any(w in intro for w in ["당기", "번들", "헷갈", "속상", "고민", "푸석", "예민", "답답", "불안", "막막", "걱정", "망설", "효과", "부작용", "비용", "가격", "통증", "붓기", "약", "반응"]):
        issues["도입"].append(("공감 부족", "도입부에서 독자의 실제 고민이 약합니다."))
        intro_score -= 3
    if selected_intro_type not in detected_intro:
        issues["도입"].append(("도입 방식 불일치", f"선택한 달로썸 도입 방식은 '{selected_intro_type}'인데, 현재 감지된 방식은 {', '.join(detected_intro) if detected_intro else '뚜렷한 유형 없음'}입니다."))
        intro_score -= 6
    if any(intro.startswith(w) for w in ["오늘은", "이번 글에서는", "알아보겠습니다", "설명드리겠습니다"]):
        issues["도입"].append(("뻔한 시작", "도입 첫 문장이 흔한 AI식 시작입니다."))
        intro_score -= 3
    scores["도입"] = max(intro_score, 0)

    # AI티
    ai_score = 15
    repeated = [f"{p}({body.count(p)})" for p in AI_PATTERNS if body.count(p) >= 3]
    if repeated:
        issues["AI티"].append(("반복 표현", ", ".join(repeated)))
        ai_score -= min(7, len(repeated) * 2)
    if body.count(":") >= 5:
        issues["AI티"].append(("콜론 과다", f"콜론(:)이 {body.count(':')}회입니다."))
        ai_score -= 3
    scores["AI티"] = max(ai_score, 0)

    # 복사 찌꺼기 / 출처 흔적
    artifact_score = 10
    artifact_patterns = []
    if "�" in body or "�" in title:
        artifact_patterns.append("깨진 문자(�)")
    if re.search(r"(?:^|\s)(?:[A-Za-z가-힣][A-Za-z가-힣\s]{1,20})\s\+1(?:\s|$)", body):
        artifact_patterns.append("출처 +1 흔적")
    if re.search(r"\[[0-9]+\]", body):
        artifact_patterns.append("각주 번호 흔적")
    if any(w in body.lower() for w in ["cite", "source", "reference", "turn0", "utm_source"]):
        artifact_patterns.append("출처/검색 시스템 흔적")
    if artifact_patterns:
        issues["복사찌꺼기"].append(("복사 찌꺼기 감지", ", ".join(sorted(set(artifact_patterns)))))
        artifact_score -= min(8, len(set(artifact_patterns))*3)
    scores["복사찌꺼기"] = max(artifact_score, 0)

    # 위험표현
    comp_score = 15
    targets = RISK_COMMON + RISK_FIELD.get(field, [])
    found = sorted(set([p for p in targets if p in body and not is_safe_risk_context(body, p)]))
    if found:
        issues["위험표현"].append(("위험표현 감지", ", ".join(found)))
        comp_score -= min(10, len(found) * 2)
    if "테스트" in purpose:
        fake = [w for w in ["저희 병원", "본원", "대표원장", "전문의가 직접", "법무법인", "변호사 사무실"] if w in body]
        if fake:
            issues["위험표현"].append(("테스트 원고 주의", f"임의 기관 표현 주의: {', '.join(fake)}"))
            comp_score -= 4
    scores["위험표현"] = max(comp_score, 0)

    # 페르소나
    persona_score = 10
    if writer_perspective == "에스테틱 원장":
        medical = [w for w in ["진단", "처방", "치료", "완치", "병변", "진료", "의료진"] if w in body]
        if medical:
            issues["작성자 관점"].append(("에스테틱 톤 이탈", f"의료행위처럼 보일 수 있는 표현: {', '.join(medical)}"))
            persona_score -= min(5, len(medical))
        esthetic_words = ["원장", "에스테틱", "관리", "홈케어", "피부 상태", "유수분", "상담", "피부 컨디션"]
        if sum(1 for w in esthetic_words if w in body) < 3:
            issues["작성자 관점"].append(("원장 관점 약함", "에스테틱 원장이 상담하듯 말하는 표현이 조금 더 필요합니다."))
            persona_score -= 3
    scores["작성자 관점"] = max(persona_score, 0)

    # 마무리
    ending_score = 10
    ending = body[-700:]
    philosophy_words = ["중요하게 생각", "지향", "철학", "원칙", "무리", "편안", "균형", "정직", "섬세", "과정이라고 생각"]
    has_philosophy = any(w in ending for w in philosophy_words)
    if include_philosophy and ending_type != "철학 없이 정보 마무리" and not has_philosophy:
        issues["마무리"].append(("철학 반영 부족", "마지막 문단에 원장의 관리 철학이나 상담 기준이 약합니다."))
        ending_score -= 4
    if ending_type == "체크리스트 요약형" and not any(w in ending for w in ["첫째", "둘째", "정리하면", "기억해"]):
        issues["마무리"].append(("요약형 마무리 부족", "핵심 기준 2~3개를 정리하는 문장이 좋습니다."))
        ending_score -= 2
    scores["마무리"] = max(ending_score, 0)

    raw_total = scores["제목"] + scores["본문"] + scores["도입"] + scores["AI티"] + scores["위험표현"] + scores["작성자 관점"] + scores["마무리"] - (10 - scores["복사찌꺼기"])
    total = min(max(raw_total, 0), 100)
    cap_reasons = []
    if selected_intro_type not in detected_intro:
        total = min(total, 90)
        cap_reasons.append("선택한 달로썸 도입 방식과 실제 도입 방식이 달라 총점 상한 90점 적용")
    if selected_intro_type == "1. 독자의 상황을 찔러주는 체크리스트 활용" and selected_intro_type not in detected_intro:
        total = min(total, 88)
        cap_reasons.append("체크리스트형 선택했지만 실제 체크리스트가 없어 총점 상한 88점 적용")
    if include_philosophy and ending_type != "철학 없이 정보 마무리" and not has_philosophy:
        total = min(total, 92)
        cap_reasons.append("철학 반영을 선택했지만 마지막 문단의 철학 표현이 약해 총점 상한 92점 적용")
    if no_space_len < min_len:
        total = min(total, 94)
        cap_reasons.append(f"공백 제외 {min_len}자 미만이라 분량 조건 미달 상한 제한")
    if b_concern_text.strip() and first_ground.get("status") == "missing":
        total = min(total, 88)
        cap_reasons.append("첫문장이 B등급 고민 핵심어를 제대로 담지 못해 도입 화법 상한 88점 적용")

    return scores, issues, total, cap_reasons, {
        "no_space_len": no_space_len,
        "body_kw": body_kw,
        "total_kw": total_kw,
        "subheads": len(subheads),
        "detected_intro": detected_intro,
        "detected_title": detected_title,
        "first_sentence": first_sentence,
        "first_sentence_grounding": first_ground,
    }


def price_estimate(score):
    if score >= 95:
        return "5만 원 이상 포트폴리오급"
    if score >= 92:
        return "4~5만 원 테스트 합격권"
    if score >= 88:
        return "3~4만 원 실무 가능권"
    if score >= 82:
        return "부분 보완 필요"
    return "초안 재작성 권장"


def show_issues(title, items):
    st.write(f"### {title}")
    if not items:
        st.success("통과")
    else:
        for name, desc in items:
            st.warning(f"**{name}** — {desc}")


def glossary_check(body, field):
    terms = GLOSSARY_TERMS.get(field, [])
    suggestions = []
    for term in terms:
        if term in body:
            idx = body.find(term)
            window = body[max(0, idx - 50):idx + 120]
            if "란" not in window and "뜻" not in window and "말합니다" not in window and "부위" not in window:
                suggestions.append(term)
    return sorted(set(suggestions))


def generate_intro_rewrite(intro_type, keyword, title, field, writer_perspective):
    topic = keyword or title or "이 주제"
    if field == "에스테틱 / 피부관리" and "복합성" in topic:
        examples = {
            "1. 독자의 상황을 찔러주는 체크리스트 활용": f"""☑ 아침에는 볼이 당기는데 오후에는 T존이 번들거린다
☑ 수분크림을 바르면 답답하고, 안 바르면 금방 건조하다
☑ 내 피부가 지성인지 건성인지 헷갈린다

이런 고민이 반복된다면 단순히 지성이나 건성으로 나누기보다, 부위별 상태가 다른 복합성 피부인지 먼저 살펴볼 필요가 있습니다. {topic}은 피지를 무조건 줄이는 것이 아니라 T존과 U존의 차이를 보고 유수분 균형을 맞춰가는 데서 시작됩니다.""",
            "2. 비교 표 활용": f"""복합성 피부는 한 얼굴 안에서도 부위별 반응이 다르게 나타납니다.

| 구분 | 자주 느끼는 상태 | 관리 방향 |
|---|---|---|
| T존 | 번들거림, 피지 | 강한 제거보다 부드러운 정리 |
| U존 | 당김, 푸석함 | 수분감과 보호감 보충 |

그래서 {topic}은 한 제품을 얼굴 전체에 똑같이 바르는 방식보다, 부위별로 필요한 관리가 무엇인지 나누어 보는 것이 중요합니다.""",
            "3. 대화체 문구": f"""“원장님, 저는 지성인가요 건성인가요?”

에스테틱 현장에서 정말 자주 듣는 질문입니다. 아침에는 볼이 당기는데 오후만 되면 코와 이마가 번들거린다면 스스로도 피부 타입을 정하기 어렵게 느껴질 수 있습니다. 이럴 때 {topic}은 피부를 하나의 타입으로 단정하기보다, T존과 U존의 차이를 살피는 데서 시작해야 합니다.""",
            "4. 뉴스 기사 활용": f"""최근 자외선 차단과 피부 장벽 관리에 대한 관심이 높아지면서, 계절에 따라 피부 컨디션이 달라지는 분들의 상담도 늘고 있습니다. 특히 복합성 피부는 여름에는 T존 번들거림이, 겨울에는 볼과 입가의 당김이 더 크게 느껴질 수 있습니다. {topic}을 찾고 있다면 계절과 생활환경에 따라 달라지는 유수분 균형을 함께 봐야 합니다.""",
            "5. 독자에게 질문 던지기": f"""아침에는 볼이 당기는데, 오후에는 코와 이마가 번들거린다면 내 피부를 지성이라고 봐야 할까요? 아니면 건성이라고 봐야 할까요?

사실 이런 경우는 한 가지 피부 타입으로 단정하기보다 복합성 피부의 특징을 함께 살펴보는 것이 좋습니다. {topic}은 피지와 건조함 중 하나만 잡는 관리가 아니라, 부위별로 필요한 관리 방향을 다르게 잡는 데서 시작됩니다.""",
            "6. 많이 묻는 질문 인용": f"""“저는 피부가 지성인지 건성인지 모르겠어요.”

원장으로 상담하다 보면 복합성 피부 고객에게 가장 자주 듣는 질문 중 하나입니다. 코와 이마는 번들거리는데 볼과 입가는 당긴다면, 피부가 유난히 까다로운 것이 아니라 부위마다 필요한 관리가 다르다는 신호일 수 있습니다. {topic}은 바로 이 차이를 읽는 데서 시작됩니다.""",
            "7. 검색만으로는 모르는 알짜 정보 예고": f"""검색을 해보면 복합성 피부에 좋다는 제품 추천은 많습니다. 하지만 실제 관리에서 중요한 것은 어떤 제품을 쓰느냐보다, 어느 부위에 어떤 제형을 얼마나 쓰느냐입니다. {topic}을 제대로 이해하려면 T존과 U존을 같은 기준으로 보지 않는 것이 핵심입니다.""",
            "8. 간단한 웹툰 만들어 넣기": f"""[웹툰 도입 구성안]
1컷: 아침에 거울을 보며 볼이 당겨 고민하는 고객
2컷: 오후가 되자 코와 이마가 번들거려 당황하는 고객
3컷: “저 지성인가요, 건성인가요?”라고 묻는 장면
4컷: 원장이 “복합성 피부는 부위별 관리가 달라야 해요”라고 설명하는 장면

웹툰 아래 본문 도입:
아침에는 당기고 오후에는 번들거리는 피부라면 한 가지 타입으로 단정하기 어렵습니다. {topic}은 T존과 U존의 차이를 살피고, 부위별로 관리 강도를 조절하는 데서 시작됩니다."""
        }
        return fix_topic_josa(examples[intro_type], topic)

    common = {
        "1. 독자의 상황을 찔러주는 체크리스트 활용": f"""☑ {topic}을 검색해도 내 상황에 맞는 기준이 잘 보이지 않는다
☑ 정보는 많은데 무엇부터 확인해야 할지 헷갈린다
☑ 괜히 잘못 선택했다가 손해를 볼까 걱정된다

이런 상황이라면 단순한 정보 나열보다, 내 상황에 맞는 기준을 먼저 정리하는 것이 중요합니다.""",
        "2. 비교 표 활용": f"""| 구분 | 흔한 판단 | 실제 확인할 점 |
|---|---|---|
| 겉으로 보이는 문제 | 단순하게 판단 | 원인과 상황 확인 |
| 해결 방법 | 빠른 선택 | 기준에 맞는 선택 |

{topic}은 단순히 하나의 답을 고르는 문제가 아니라, 상황에 맞는 기준을 나누어 보는 것이 중요합니다.""",
        "3. 대화체 문구": f"""“이럴 때는 어떻게 해야 하나요?”

현장에서 자주 듣는 질문입니다. {topic}은 단순히 검색 결과만 보고 판단하기보다, 내 상황과 조건을 함께 살펴보는 것이 중요합니다.""",
        "4. 뉴스 기사 활용": f"""최근 관련 이슈가 늘면서 {topic}에 대한 관심도 함께 높아지고 있습니다. 다만 기사나 검색 결과만으로는 내 상황에 바로 적용하기 어려운 경우가 많아, 핵심 기준을 먼저 정리해보는 것이 좋습니다.""",
        "5. 독자에게 질문 던지기": f"""{topic}을 알아보고 있다면, 지금 가장 궁금한 점은 무엇인가요? 단순한 방법보다 내 상황에 맞는 기준을 먼저 확인하는 것이 중요합니다.""",
        "6. 많이 묻는 질문 인용": f"""“이 경우에는 어떻게 해야 하나요?”

{topic}과 관련해 가장 많이 나오는 질문 중 하나입니다. 같은 상황처럼 보여도 세부 조건에 따라 판단이 달라질 수 있기 때문에 기준을 나누어 살펴보는 것이 좋습니다.""",
        "7. 검색만으로는 모르는 알짜 정보 예고": f"""검색하면 기본 정보는 쉽게 찾을 수 있습니다. 하지만 실제로 중요한 것은 검색 결과에 잘 나오지 않는 판단 기준입니다. {topic}은 표면적인 정보보다 상황별 기준을 함께 봐야 합니다.""",
        "8. 간단한 웹툰 만들어 넣기": f"""[웹툰 도입 구성안]
1컷: 검색창에 {topic}을 입력하는 독자
2컷: 너무 많은 정보에 혼란스러워하는 장면
3컷: 전문가가 핵심 기준을 짚어주는 장면

웹툰 아래 본문 도입:
정보가 많을수록 오히려 판단은 어려워질 수 있습니다. {topic}은 내 상황에 맞는 기준을 먼저 잡는 것이 중요합니다."""
    }
    return fix_topic_josa(common[intro_type], topic)


def generate_final_paragraph(keyword, field, writer_perspective, homepage_mode, homepage_info, philosophy_text):
    topic = keyword or "이 주제"
    homepage_info = (homepage_info or "").strip()
    philosophy_text = (philosophy_text or "").strip()

    if homepage_mode == "홈페이지 정보 있음":
        if homepage_info:
            return f"""{topic}은 한 번에 완벽한 답을 찾기보다, 현재 상태와 생활 습관을 함께 살피며 관리 방향을 조절하는 과정입니다. 입력해주신 홈페이지 정보 기준으로 보면, {homepage_info} 이러한 방향을 원고 말미에 자연스럽게 연결할 수 있습니다.

다만 테스트 원고에서는 실제 업체명이나 원장명을 임의로 만들기보다, 홈페이지에 확인된 강점만 담백하게 반영하는 것이 안전합니다. 마지막 문단은 과장된 약속보다 독자가 자신의 상태를 점검하고 상담 필요성을 자연스럽게 느끼도록 마무리하는 편이 좋습니다."""
        return f"""홈페이지 정보 있음으로 선택되어 있지만 입력된 정보가 없습니다. 이 경우 실제 업체 철학이나 강점을 임의로 만들면 안 됩니다.

{topic}은 현재 상태를 먼저 확인하고, 필요한 관리 방향을 차분히 조절하는 것이 중요합니다. 홈페이지에서 확인한 실제 강점이나 상담 철학이 있다면 마지막 문단에 1~2문장으로만 자연스럽게 연결하세요."""

    if field == "에스테틱 / 피부관리":
        base = f"""{topic}은 한 번에 완벽한 제품을 찾는 데서 끝나는 관리가 아닙니다. 오늘 내 피부에서 어느 부위가 번들거리고, 어느 부위가 당기는지 살펴보며 세안과 보습, 자외선 차단 루틴을 조절하는 것이 먼저입니다."""
        if philosophy_text:
            base += f"\n\n{philosophy_text}"
        else:
            base += "\n\n에스테틱 관리는 피부를 억지로 바꾸는 일이 아니라, 지금 피부가 편안하게 받아들일 수 있는 균형을 찾는 과정이라고 생각합니다."
        return base

    return f"""{topic}은 검색으로 얻은 정보만으로 바로 결론을 내리기보다, 자신의 상황에 맞는 기준을 차분히 확인하는 것이 중요합니다. 홈페이지 정보가 없다면 업체의 철학이나 강점을 임의로 만들지 말고, 핵심 내용 요약과 다음 행동 기준을 중심으로 마무리하는 편이 안전합니다."""




# =========================
# v3.8: 자료조사 프롬프트 / 원고 설계 모드
# =========================
RESEARCH_FIELDS = [
    "병원 / 의료", "법률", "에스테틱 / 피부관리", "청소 / 홈케어", "생활용품", "학원 / 교육",
    "인테리어 / 리모델링", "보험 / 금융 / 부동산", "맛집 / 여행 / 숙박", "기타"
]
CONTENT_TYPES = ["정보성", "바이럴", "업체 홍보", "후기형", "전문가 설명형"]

USECASE_MODES = ["블로그 정보성", "카페 정보성", "커뮤니티/바이럴", "후기/리뷰"]

def usecase_style_block(usecase_mode, field=""):
    mode = usecase_mode or "블로그 정보성"
    field = field or ""
    base = """[원고 사용처 공통 구조]
- 문단 뼈대는 도입 → 핵심 설명 → 확인 기준 → 주의사항 → 마무리 흐름을 기본으로 한다.
- 사용처에 따라 문단 구조를 완전히 바꾸기보다 말투, 문장 길이, 홍보 허용도, 경험담 허용 여부, 마무리 방식을 조정한다.
- 키워드 배치, 도입 화법, 첫문장 형태, 도입 방식은 별도 선택값을 우선한다."""
    if mode == "카페 정보성":
        body = """
[카페 정보성 글투]
- 네이버 카페 회원이 정보를 정리해 공유하는 느낌으로 쓴다.
- 지나치게 전문가 블로그처럼 딱딱한 어미를 줄이고, 자연스러운 정보공유 말투를 쓴다.
- 문장 어미는 ‘~습니다’만 반복하지 말고 ‘~해요’, ‘~좋습니다’, ‘~확인해보는 게 좋습니다’를 자연스럽게 섞는다. 단, 과한 반말이나 친목 말투는 피한다.
- 단, 실제 경험이 없으면 ‘제가 해봤는데’, ‘직접 이용해보니’ 같은 후기인 척하는 문장은 금지한다.
- 특정 업체 추천, 신청 유도, 과한 장점 나열을 피한다.
- 마무리는 ‘어디를 고르라’가 아니라 확인 기준 정리로 끝낸다.
- 소제목은 [대괄호] 라벨보다 카페글에 어울리는 자연스러운 소제목을 기본으로 쓴다.
- 네이버 계정, 플랫폼 정책, 개인정보 관련 문장은 법률문처럼 단정하지 말고 ‘본인 사용을 전제로 보기 때문에’, ‘피하는 편이 안전합니다’처럼 완화해 쓴다.
- 예: ‘알아볼 때는 가격만 보기보다 추가요금 조건도 같이 확인하는 게 좋습니다.’"""
    elif mode == "커뮤니티/바이럴":
        body = """
[커뮤니티/바이럴 글투]
- 첫 문장과 도입에서 흥미를 만들되 낚시성, 허위 정보, 공포 조장은 금지한다.
- 문장은 블로그보다 짧고 리듬 있게 쓴다.
- 댓글을 유도하듯 자연스럽게 문제 상황을 던질 수 있으나, 근거 없는 단정은 피한다.
- 광고처럼 보이는 CTA와 업체 찬양은 피한다.
- 정보는 짧게 쪼개고, 확인 기준 중심으로 정리한다."""
    elif mode == "후기/리뷰":
        body = """
[후기/리뷰 글투]
- 실제 경험 자료가 제공된 경우에만 경험담을 쓴다.
- 경험 자료가 없으면 후기인 척하지 말고 ‘후기에서 자주 확인되는 기준’, ‘리뷰를 볼 때 확인할 점’처럼 정보형으로 쓴다.
- 특정 만족 경험, 방문 경험, 구매 경험, 상담 경험을 임의로 만들지 않는다.
- 짧고 구체적인 장점·불편 포인트 중심으로 정리한다.
- 과한 칭찬, 별점 조작 느낌, ‘무조건 추천’ 표현은 금지한다."""
    else:
        body = """
[블로그 정보성 글투]
- 검색 의도에 맞춰 차분하게 설명하는 정보성 블로그 톤으로 쓴다.
- 전문가가 기준을 정리해주는 느낌은 가능하지만, 과장된 홍보와 가짜 경험담은 피한다.
- 병원/법률/금융 분야는 단정·보장 표현을 더 강하게 제한한다.
- 홈페이지 정보가 있을 때만 업체·병원·법무법인 철학이나 장점을 마무리에 1~2문장 반영한다."""
    field_guard = ""
    if "병원" in field or "의료" in field:
        field_guard = "\n[분야별 추가 주의 - 병원/의료]\n- 치료 보장, 부작용 없음, 통증 없음, 100% 개선, 최고/유일 표현을 피한다."
    elif "법률" in field:
        field_guard = "\n[분야별 추가 주의 - 법률]\n- 무조건 승소, 반드시 회수, 100% 해결, 처벌 가능 단정 표현을 피한다."
    elif "금융" in field or "보험" in field or "부동산" in field:
        field_guard = "\n[분야별 추가 주의 - 금융/보험/부동산]\n- 수익 보장, 손실 없음, 무조건 유리함 같은 단정 표현을 피한다."
    return base + "\n" + body + field_guard

def usecase_summary_line(usecase_mode):
    mapping = {
        "블로그 정보성": "차분한 정보성 블로그 톤 / 검색 의도와 확인 기준 중심",
        "카페 정보성": "카페 회원 정보공유 톤 / 홍보성·가짜 후기 금지",
        "커뮤니티/바이럴": "짧고 흥미 있는 정보공유 톤 / 낚시성·허위정보 금지",
        "후기/리뷰": "실제 경험 자료가 있을 때만 후기형 / 경험 조작 금지",
    }
    return mapping.get(usecase_mode, mapping["블로그 정보성"])
VOICE_TYPES = [
    "일상 불편형",
    "판단 혼란형",
    "감정 직면형",
    "억울함 공감형",
    "비교 고민형",
    "비용 불안형",
    "선택 불안형",
    "후회 예방형",
    "전문가 안내형",
    "질문 응답형",
]
VOICE_TYPE_OPTIONS = ["자동 추천"] + VOICE_TYPES

FIRST_SENTENCE_TYPES = [
    "자동 추천",
    "의문문 강제",
    "체크리스트형",
    "많이 묻는 질문 인용형",
    "대화체형",
    "장면 묘사형",
    "전문가 안내형",
]

LENGTH_PRESETS = ["1000자", "1500자", "2000자", "3000자", "직접 입력"]
SPACING_TYPES = ["공백 제외", "공백 포함"]
PARAGRAPH_OPTIONS = ["분량 우선, 문단 수 자연 조절", "3문단", "4문단", "5문단", "6문단 이상"]

def resolve_target_length(preset, custom_value):
    if preset == "직접 입력":
        try:
            return int(custom_value)
        except Exception:
            return 1500
    return int(re.sub(r"[^0-9]", "", preset) or 1500)

def length_guidance(target_len, spacing_type, paragraph_option):
    try:
        target_len = int(target_len)
    except Exception:
        target_len = 1500
    if paragraph_option == "분량 우선, 문단 수 자연 조절":
        if target_len <= 1200:
            suggested = "3~4문단"
        elif target_len <= 1800:
            suggested = "5문단 짧게"
        elif target_len <= 2400:
            suggested = "5문단 안정형"
        else:
            suggested = "5~6문단"
    else:
        suggested = paragraph_option
    return f"""[분량 조건]
- 전체 분량: {spacing_type} {target_len}자 내외
- 테스트 조건에서는 기존 문장 수 설정보다 전체 분량 조건을 우선한다.
- 권장 문단 구성: {suggested}
- 기본 흐름은 도입 → 본문1 → 본문2 → 본문3 → 마무리를 유지하되, 분량이 짧으면 본문을 압축한다.
- 각 문단의 문장 수를 억지로 늘리지 말고, 중복 설명을 줄인다.
- 키워드는 자연스럽게 넣고, 분량을 맞추기 위해 키워드를 반복하지 않는다.
- 짧은 테스트 원고에서는 키워드를 많이 넣기보다 독자 고민과 설명의 자연스러움을 우선한다."""


def build_research_prompt(topic, keyword, field, content_goal, extra_focus, target_len=1500, spacing_type="공백 제외", paragraph_option="분량 우선, 문단 수 자연 조절", intro_type="자동 추천", title_type="자동 추천", voice_type="자동 추천", first_sentence_type="자동 추천", homepage_mode="홈페이지 정보 없음", homepage_info="", homepage_url="", keyword_delivery_text="", keyword_placement_text="", usecase_mode="블로그 정보성"):


    topic = topic.strip() or "써마지 시술"
    keyword = keyword.strip() or topic
    field = field.strip() or "병원 / 의료"
    content_goal = content_goal.strip() or "병원 블로그 원고 작성을 위한 사전 자료조사"
    usecase_mode = usecase_mode or "블로그 정보성"
    usecase_block = usecase_style_block(usecase_mode, field)
    extra_focus = extra_focus.strip()
    length_plan = length_guidance(target_len, spacing_type, paragraph_option)
    keyword_plan = keyword_delivery_text.strip() if keyword_delivery_text and keyword_delivery_text.strip() else keyword_count_instruction(keyword, target_len)
    keyword_placement_text = keyword_placement_text.strip() if keyword_placement_text else ""
    intro_type = intro_type or "자동 추천"
    title_type = title_type or "자동 추천"
    voice_type = voice_type or "자동 추천"
    first_sentence_type = first_sentence_type or "자동 추천"
    first_sentence_plan = first_sentence_instruction(first_sentence_type, intro_type)
    homepage_mode = homepage_mode or "홈페이지 정보 없음"
    homepage_info = homepage_info.strip() if homepage_info else ""
    homepage_url = homepage_url.strip() if homepage_url else ""
    homepage_block = homepage_info_force_block(homepage_mode, homepage_info)
    homepage_research_section = ""
    if homepage_mode == "홈페이지 정보 있음" and homepage_url:
        homepage_research_section = f"""
[공식 홈페이지 자료 조사]
아래 홈페이지 URL 또는 병원/업체명/법무법인명을 함께 확인해줘.
GPT가 직접 공식 홈페이지를 열람하거나 검색 가능한 경우에만 원장/대표 소개, 진료·상담 철학, 장비, 시스템, 사후관리, 접근성, 병원/업체 장점을 추출한다.

홈페이지/업체 단서:
{homepage_url}

조사 규칙:
- 반드시 공식 홈페이지 또는 공식 채널에서 확인되는 내용만 사용한다.
- 블로그 후기, 광고대행사 글, 플레이스 리뷰만 보고 원장 경력·철학·장점을 확정하지 않는다.
- 홈페이지를 확인할 수 없으면 “공식 홈페이지 확인 불가”라고 표시하고, 철학·장점을 임의로 만들지 않는다.
- 홈페이지 원문을 길게 베끼지 말고, 원장/대표 소개·철학·장점·장비/시스템·사후관리로 짧게 분류한다.
- 마무리 반영 후보는 이번 주제와 실제로 연결되는 내용만 1~2문장으로 만든다.
"""
    elif homepage_mode == "홈페이지 정보 있음" and homepage_info:
        homepage_research_section = f"""
[홈페이지/업체 정보 조사 반영]
아래 정보는 사용자가 홈페이지에서 확인해 입력한 내용이다. 조사 결과를 정리할 때 원장/대표 소개, 철학, 장점, 장비, 상담 방식, 사후관리 등으로 분류해줘.
단, 아래 입력 내용에 없는 경력·장점·철학은 임의로 만들지 말 것.

사용자 입력 홈페이지/업체 정보:
{homepage_info}
"""
    elif homepage_mode == "홈페이지 정보 있음":
        homepage_research_section = """
[공식 홈페이지 자료 조사]
홈페이지 정보 있음으로 선택되어 있지만 URL/업체명 또는 입력 내용이 없다. 이 경우 원장/대표 소개, 철학, 장점, 장비, 사후관리 문구를 임의로 만들지 말 것.
"""
    else:
        homepage_research_section = """
[홈페이지/업체 정보 조사 반영]
별도 홈페이지/업체 정보가 제공되지 않았다. 마무리에서 ‘본원은’, ‘저희 병원은’, ‘저희 법무법인은’, ‘환자 중심’, ‘정직한 진료’, ‘풍부한 경험’, ‘신뢰’ 같은 철학·장점 문구를 임의로 만들지 말 것.
"""
    voice_instruction = "도입 화법은 자료를 보고 가장 적합한 화법을 추천해줘." if voice_type == "자동 추천" else f"도입 화법은 반드시 '{voice_type}' 흐름을 우선 고려해줘."
    intro_instruction = "도입 8가지 방식은 자료를 보고 가장 적합한 유형을 추천해줘." if intro_type == "자동 추천" else f"도입 8가지 방식은 반드시 '{intro_type}' 방향을 우선 고려해줘."
    if title_type == "선택 안함":
        title_instruction = "제목 유형은 따로 선택하지 않는다. 6가지 유형을 강제하지 말고 키워드 앞 배치, 30자 이내, 어그로 금지 등 제목 기본 기준만 지켜줘."
    elif title_type == "자동 추천":
        title_instruction = "제목 유형은 자료와 주제에 맞는 방식을 추천해줘."
    else:
        title_instruction = f"제목 유형은 반드시 '{title_type}' 방향을 우선 고려해줘."

    return f"""주제: {topic}
핵심 키워드: {keyword}
분야: {field}
원고 목적: {content_goal}
원고 사용처: {usecase_mode}
{usecase_block}
{length_plan}
{keyword_plan}
{keyword_placement_text}
희망 도입 화법: {voice_type}
도입 화법 지시: {voice_instruction}
희망 도입 첫문장 형태: {first_sentence_type}
도입 첫문장 형태 지시: {first_sentence_plan}
희망 도입 방식: {intro_type}
도입 방식 지시: {intro_instruction}
희망 제목 유형: {title_type}
제목 유형 지시: {title_instruction}
{homepage_research_section}
{homepage_block}

제목 기본 기준:
- 제목에는 핵심 키워드 "{keyword}"를 맨 앞에 1회 넣는 것을 우선한다.
- 제목은 가능하면 30자 이내로 구성한다.
- 자극적인 어그로가 아니라, 독자의 호기심과 실제 고민을 건드리는 제목으로 만든다.
- 제목 내용과 본문 내용이 다르게 느껴지지 않게 한다.
- 제목 방식은 아래 6가지 중 자료와 주제에 맞게 추천한다.
  1) 숫자/데이터 활용형
  2) 질문형
  3) 긴급성/한정성 강조형
  4) 궁금증 자극형
  5) 반전/의외성형
  6) 독자 상황 콕집기형

표기 주의:
- 도입부에 많이 묻는 질문을 넣을 때는 질문을 2~3개(두세 개)만 사용한다고 명확히 써줘.
- 절대 “23개”라고 붙여 쓰지 말고, 범위 표시는 반드시 “2~3개”처럼 물결표를 포함해 써줘.

위 주제로 블로그 원고 작성을 위한 사전 자료조사를 해줘.
자료는 단순히 많이 모으는 것이 아니라, 아래처럼 등급을 나누고 원고에 어떻게 쓸지까지 정리해줘.

가장 중요한 목표:
1. A등급 자료에서는 여러 자료에서 공통으로 확인되는 핵심 사실을 뽑아줘.
2. B등급 자료에서는 실제 사람들이 반복해서 묻는 고민, 불안, 질문 패턴을 뽑아줘.
3. C등급 자료에서는 자연스러운 생활 표현, 후기 말투, 망설임 표현만 참고해줘.
4. 원문 문장을 그대로 베끼지 말고, 원고에 반영할 수 있는 패턴으로 재구성해줘.

자료 등급 기준:

A등급: 팩트 확인용
- 정부기관 자료
- 학회/협회 자료
- 병원 공식자료
- 제조사 공식자료
- 법령/판례/공식 안내자료
- 신뢰 가능한 전문자료

A등급에서 뽑을 내용:
- 여러 자료에서 공통으로 반복되는 핵심 사실
- 원리, 정의, 적용 대상, 주의사항
- 개인차가 있는 부분
- 단정하면 위험한 부분
- 본문에 안전하게 넣을 수 있는 기준

B등급: 잠재고객 고민 추출용
- 하이닥 Q&A
- 닥터나우 상담
- 로톡 상담 사례
- 법률메카 Q&A
- 네이버 지식iN
- 유튜브 댓글/질문
- 커뮤니티 질문글

B등급에서 뽑을 내용:
- 사람들이 실제로 걱정하는 질문
- 반복되는 고민
- 판단이 어려운 지점
- 비용, 부작용, 효과, 기간, 선택 불안
- 제목과 도입부에 넣을 만한 질문형 포인트

C등급: 말맛/후기 참고용
- 블로그 후기
- 카페 후기
- 쇼핑몰 리뷰
- 네이버 플레이스 리뷰
- 숨고 후기
- 댓글

C등급에서 뽑을 내용:
- 사람들이 불편함을 표현하는 방식
- 실제 독자 말투
- 후기형 글에 참고할 수 있는 분위기
- 단, 가짜 경험담은 만들지 말 것

D등급: 참고만 가능
- 출처 불명 블로그
- 광고성 글
- AI 느낌 강한 글
- 오래된 글
- 피상적인 정보글

제외 자료:
- 개인정보가 드러나는 글
- 특정 업체 비방글
- 과도한 공포 마케팅
- 근거 없는 루머
- 의료/법률/금융적으로 위험한 단정 표현

출력 형식:

[1] 자료 목록 및 등급 평가
각 자료마다 아래 형식으로 정리해줘.

자료 제목:
자료 링크:
자료 유형:
예상 등급: A/B/C/D/제외
관련성: 높음/보통/낮음
신뢰도: 높음/보통/낮음
고민 추출 가치: 높음/보통/낮음
최신성: 높음/보통/낮음
원고 활용 목적:
주의할 점:

[2] A등급 공통 핵심정보
여러 A등급 자료에서 공통으로 확인되는 내용만 5~8개로 정리해줘.
단, 한 자료에만 나오는 내용은 “단일 자료 확인 내용”으로 따로 분리해줘.
자료끼리 내용이 다르면 “추가 확인 필요”로 표시해줘.

[3] B등급 잠재고객 고민패턴
실제 질문/댓글/상담글에서 반복될 가능성이 높은 고민을 정리해줘.
아래 기준으로 나눠줘.
- 반복 질문
- 불안 포인트
- 판단이 어려운 지점
- 비용/효과/부작용/기간/선택 고민
- 제목으로 바꿀 수 있는 질문
- 도입부에 넣을 공감 포인트

[4] C등급 말맛 참고 포인트
후기나 댓글에서 참고할 수 있는 생활 표현을 정리해줘.
단, 특정 개인 경험을 그대로 쓰거나 가짜 후기로 만들지 말고 말투와 표현 방향만 정리해줘.

[5] 추천 제목 유형 + 제목 후보
아래 제목 방식 중 가장 어울리는 유형을 추천하고 이유를 설명해줘.
사용자가 희망 제목 유형을 지정했다면 그 방식이 이 주제에 맞는지 판단하고, 맞지 않으면 이유와 대체안을 함께 말해줘.

제목 6가지 방식:
1. 숫자/데이터 활용형
2. 질문형
3. 긴급성/한정성 강조형
4. 궁금증 자극형
5. 반전/의외성형
6. 독자 상황 콕집기형

제목 후보는 5개 제안해줘.
제목 후보는 가능하면 핵심 키워드를 맨 앞에 1회 넣고, 30자 이내로 작성해줘.

[6] 추천 도입 화법 + 달로썸 도입 8가지 방식
아래 중 가장 어울리는 도입 화법을 추천하고 이유를 설명해줘.
- 일상 불편형
- 판단 혼란형
- 감정 직면형
- 억울함 공감형
- 비교 고민형
- 비용 불안형
- 선택 불안형
- 후회 예방형
- 전문가 안내형
- 질문 응답형

그리고 아래 달로썸 도입 8가지 중 어떤 방식이 가장 적합한지도 추천해줘.
사용자가 희망 도입 방식을 지정했다면 그 방식이 이 주제에 맞는지 판단하고, 맞지 않으면 이유와 대체안을 함께 말해줘.

달로썸 도입 8가지:
1. 독자의 상황을 찔러주는 체크리스트 활용
2. 비교 표 활용
3. 대화체 문구
4. 뉴스 기사 활용
5. 독자에게 질문 던지기
6. 많이 묻는 질문 인용
7. 검색만으로는 모르는 알짜 정보 예고
8. 간단한 웹툰/장면 구성

[6-1] 선택 화법 실제 적용 설계
중요: “추천 도입 화법: 판단 혼란형 + 후회 예방형”처럼 이름만 쓰고 끝내지 말 것.
반드시 조사된 B등급 고민패턴을 바탕으로 아래까지 구체적으로 작성해줘.

선택 화법:
화법 선택 이유:
화법 설명:
- 이 화법으로 독자에게 어떤 감정/상황을 먼저 건드릴지 설명한다.

감정 도입 첫문장 후보 3개:
1. 문장:
   근거 B등급 고민:
2. 문장:
   근거 B등급 고민:
3. 문장:
   근거 B등급 고민:

본문 고민 브릿지 후보 3개:
1. 문장:
   근거 B등급 고민:
2. 문장:
   근거 B등급 고민:
3. 문장:
   근거 B등급 고민:

마무리 재연결 문장 후보 2개:
1. 문장:
   근거 B등급 고민:
2. 문장:
   근거 B등급 고민:

작성 규칙:
- 감정 도입 첫문장, 본문 고민 브릿지, 마무리 재연결 문장은 반드시 조사된 B등급 잠재고객 고민패턴에서 끌어와 만든다.
- 자료에 없는 감정, 증상, 비용 불안, 선택 상황을 임의로 만들지 않는다.
- 원문 문장을 그대로 베끼지 말고, 근거 고민을 상담형 문장으로 재구성한다.
- B등급 고민이 부족하면 “B등급 고민 부족”이라고 표시하고 구체 공감문을 억지로 만들지 않는다.
- 도입 첫문장은 정보 설명이 아니라 독자의 상황/판단 혼란/비용 불안/선택 불안을 먼저 짚는다.
- 본문 브릿지는 도입 문장을 그대로 반복하지 말고, 정보 설명 앞에 짧게 연결하는 문장으로 만든다.
- 마무리는 업체/병원/전문가 장점을 지어내지 말고, 독자가 무엇을 확인하고 선택해야 하는지 정리한다.
- 병원/법률/금융 분야는 단정·보장·확정 표현을 피한다.
- 생활/제품/홈케어 분야는 과장 표현과 가짜 후기 표현을 피한다.

[6-2] 도입 첫문장 형태 설계
중요: 화법 이름과 도입 방식만으로는 첫문장 형태가 보장되지 않는다.
선택된 첫문장 형태에 맞춰 실제 초안에서 보일 수 있게 아래까지 작성해줘.

도입 첫문장 형태:
첫문장 형태 선택 이유:
첫문장 필수 규칙:
- 의문문 강제라면 첫 문장은 반드시 물음표(?)로 끝나야 한다.
- 체크리스트형이라면 도입부 첫 5문장 안에 체크리스트 3~5개가 보여야 한다.
- 많이 묻는 질문 인용형이라면 도입부 초반에 질문 2~3개 또는 따옴표 질문이 보여야 한다.
- 대화체형이라면 실제 상담에서 나올 법한 짧은 말걸기 문장으로 시작한다.
- 장면 묘사형이라면 독자가 겪는 구체적인 생활 장면으로 시작한다.
- 전문가 안내형이라면 감정을 과하게 키우지 않고 확인 기준을 먼저 제시한다.
- 어떤 형태든 첫 문장을 정보 정의문으로 시작하지 않는다.
- 첫문장 예시는 반드시 B등급 고민 핵심어를 직접 포함한다.
- 단순히 물음표를 붙인 넓은 질문이 아니라, 효과 없음/부작용/비용/기저질환/비교 혼란/선택 불안 등 조사된 고민을 한 문장 안에 넣는다.

첫문장 예시 3개:
1.
2.
3.

[6-3] 홈페이지/업체 정보 반영 설계
중요: 공식 홈페이지에서 확인된 경우에만 마무리에서 병원/업체/법무법인 소개를 허용한다.

홈페이지 정보 제공 여부:
확인한 공식 홈페이지/공식 채널:
공식 홈페이지 확인 가능 여부:
홈페이지 정보 요약:
- 원장/대표 소개:
- 진료/상담/운영 철학:
- 장비/시스템/사후관리/접근성 등 장점:
- 이번 주제와 연결 가능한 내용:
마무리 반영 문장 후보 2개:
1.
2.
주의:
- 입력된 홈페이지 정보 안에서만 정리한다.
- 없는 경력, 전문성, 장점, 철학을 만들지 않는다.
- 마무리 반영은 1~2문장 정도로 제한한다.
- 홈페이지 정보가 주제와 관련이 약하면 억지 홍보하지 않는다.

[7] GPTs 초안 작성용 요약
내가 프로그램에 붙여넣을 수 있게 아래 형식으로 짧게 정리해줘.

핵심 팩트 자료 요약:
원고 사용처 적용 방향:
잠재고객 고민 요약:
추천 제목 유형:
제목 후보:
추천 도입 화법:
화법 선택 이유:
화법 설명:
도입 첫문장 형태:
첫문장 형태 선택 이유:
첫문장 필수 규칙:
감정 도입 첫문장 후보:
감정 도입 첫문장 근거 고민:
본문 고민 브릿지 후보:
본문 고민 브릿지 근거 고민:
마무리 재연결 문장 후보:
마무리 재연결 근거 고민:
홈페이지 정보 제공 여부:
확인한 공식 홈페이지/공식 채널:
공식 홈페이지 확인 가능 여부:
홈페이지 정보 요약:
마무리 반영 가능한 홈페이지 문장 후보:
추천 달로썸 도입 방식:
제목 방향:
도입부 방향:
소제목 방향:
반드시 포함할 내용:
피해야 할 표현:
분량/문단 반영 방향:

주의사항:
- 원문을 길게 복사하지 말 것.
- 실제 문장을 그대로 원고에 쓰지 말 것.
- 출처 링크는 반드시 함께 줄 것.
- {field} 분야에서 위험한 단정 표현은 피할 것.
- 사용자가 링크를 직접 확인할 수 있도록 자료별 링크를 빠뜨리지 말 것.
- 숫자 범위는 반드시 “2~3개”, “3~4개”, “4~6회”처럼 물결표를 넣어 표기하고, “23개”, “34개”, “46회”처럼 붙여 쓰지 말 것.
- 조사 결과 마지막에는 위 분량 조건에 맞춰 원고를 압축하거나 확장할 때 우선 반영할 내용도 정리할 것.
""" + (f"\n추가로 중점적으로 조사할 내용:\n{extra_focus}\n" if extra_focus else "")


def extract_lines_by_keywords(text, keywords, max_items=8):
    if not text.strip():
        return []
    lines = []
    for raw in re.split(r"[\n\r]+", text):
        line = raw.strip(" -•·\t")
        if len(line) < 8:
            continue
        if any(k in line for k in keywords):
            lines.append(line)
    # de-duplicate preserving order
    out = []
    seen = set()
    for l in lines:
        key = re.sub(r"\s+", "", l)[:60]
        if key not in seen:
            out.append(l)
            seen.add(key)
        if len(out) >= max_items:
            break
    return out


def section_after(text, names, stop_names=None, max_chars=2000):
    stop_names = stop_names or []
    for name in names:
        idx = text.find(name)
        if idx >= 0:
            part = text[idx: idx + max_chars]
            stop_idx = len(part)
            for stop in stop_names:
                j = part.find(stop, len(name))
                if j >= 0:
                    stop_idx = min(stop_idx, j)
            return part[:stop_idx].strip()
    return ""


def analyze_research_text(text):
    t = text or ""
    counts = {
        "A등급": len(re.findall(r"A등급|예상 등급:\s*A|예상등급:\s*A", t)),
        "B등급": len(re.findall(r"B등급|예상 등급:\s*B|예상등급:\s*B", t)),
        "C등급": len(re.findall(r"C등급|예상 등급:\s*C|예상등급:\s*C", t)),
        "D등급": len(re.findall(r"D등급|예상 등급:\s*D|예상등급:\s*D", t)),
        "제외": len(re.findall(r"제외|사용 금지|반영 비추천", t)),
    }
    a_section = section_after(t, ["[2] A등급 공통 핵심정보", "A등급 공통 핵심정보", "핵심 팩트 자료 요약"], ["[3]", "B등급", "잠재고객"], 2600)
    b_section = section_after(t, ["[3] B등급 잠재고객 고민패턴", "B등급 잠재고객 고민패턴", "잠재고객 고민 요약"], ["[4]", "C등급", "말맛"], 2600)
    c_section = section_after(t, ["[4] C등급 말맛 참고 포인트", "C등급 말맛 참고", "말맛 참고 포인트"], ["[5]", "추천 도입"], 1800)

    a_lines = extract_lines_by_keywords(a_section or t, ["공통", "원리", "정의", "개인차", "주의", "효과", "시술", "치료", "절차", "기준", "사용", "필요"], 8)
    b_lines = extract_lines_by_keywords(b_section or t, ["걱정", "불안", "궁금", "통증", "부작용", "비용", "효과", "기간", "차이", "비교", "헷갈", "고민", "질문", "막막", "억울"], 10)
    c_lines = extract_lines_by_keywords(c_section or t, ["말투", "표현", "후기", "불편", "느낌", "사용감", "망설", "생활"], 8)
    return counts, a_lines, b_lines, c_lines


def recommend_voice_type(field, topic, keyword, research_text):
    """조사자료를 바탕으로 전 분야 공통 화법을 추천한다."""
    text = " ".join([field or "", topic or "", keyword or "", research_text or ""])
    if any(w in text for w in ["외도", "상간", "배우자", "이혼", "배신", "폭행", "형사", "사망", "유산"]):
        return "감정 직면형"
    if any(w in text for w in ["억울", "책임", "누수", "대여금", "돈", "소송", "민원", "손해", "거짓말", "말을 바꾸"]):
        return "억울함 공감형"
    if any(w in text for w in ["비용", "가격", "견적", "수임료", "샷 수", "추가 비용", "환급", "보험료", "비싸"]):
        return "비용 불안형"
    if any(w in text for w in ["선택", "어디", "업체", "병원 선택", "학원 선택", "후기", "리뷰", "고르", "믿어도"]):
        return "선택 불안형"
    if any(w in text for w in ["차이", "비교", "추천", "vs", "VS", "울쎄라", "인모드", "슈링크", "전기면도기", "날면도기", "무엇이 더"]):
        return "비교 고민형"
    if any(w in text for w in ["전", "시작", "계약", "시술 전", "수술 전", "소송 전", "구매 전", "받기 전", "놓치", "후회"]):
        return "후회 예방형"
    if any(w in text for w in ["부작용", "정상", "염증", "회복", "헷갈", "괜찮", "문제", "신호", "구분", "판단"]):
        return "판단 혼란형"
    if any(w in text for w in ["통증", "아프", "냄새", "얼룩", "불편", "붓기", "따갑", "가려움", "일상", "옷", "잠"]):
        return "일상 불편형"
    if any(w in text for w in ["많이 묻", "자주 묻", "FAQ", "질문", "상담", "궁금"]):
        return "질문 응답형"
    if field in ["병원 / 의료", "법률", "보험 / 금융 / 부동산"]:
        return "전문가 안내형"
    return "일상 불편형"

def voice_style_instruction(voice_type):
    mapping = {
        "일상 불편형": "독자가 일상에서 겪는 불편한 장면을 먼저 짚고 정보로 연결한다.",
        "판단 혼란형": "정상인지 문제 신호인지, A인지 B인지 구분하기 어려운 지점을 먼저 짚는다.",
        "감정 직면형": "강한 충격, 배신감, 두려움처럼 감정 강도가 높은 상황을 먼저 인정하고 현실 기준으로 전환한다.",
        "억울함 공감형": "내 잘못이 아닌 것 같은데 책임이나 손해를 떠안는 상황의 억울함을 먼저 짚는다.",
        "비교 고민형": "둘 중 뭐가 더 좋은지보다 내 상황에 맞는 기준이 무엇인지로 전환한다.",
        "비용 불안형": "가격, 추가비용, 수임료, 샷 수, 견적 차이 때문에 망설이는 마음을 먼저 짚는다.",
        "선택 불안형": "후기와 정보는 많은데 어디를 골라야 할지 막막한 상황을 먼저 짚는다.",
        "후회 예방형": "시작 후 후회하지 않기 위해 사전에 확인해야 할 기준을 강조한다.",
        "전문가 안내형": "감정을 과하게 끌지 않고 전문가가 차분히 기준을 안내하는 흐름으로 간다.",
        "질문 응답형": "실제 상담에서 자주 나올 법한 질문을 먼저 던지고 하나씩 답하는 흐름으로 간다.",
    }
    return mapping.get(voice_type, "선택한 화법을 유지한다.")


def first_sentence_instruction(first_sentence_type, intro_type=""):
    """도입 첫문장 형태를 별도로 강제하는 지시문."""
    first_sentence_type = first_sentence_type or "자동 추천"
    intro_type = intro_type or "자동 추천"
    if first_sentence_type == "자동 추천":
        return "도입 방식과 화법에 맞춰 첫문장 형태를 선택한다. 질문형/FAQ/체크리스트 도입이면 첫 문장을 의문문 또는 질문형 항목으로 시작하고, 전문가 안내형/뉴스형이면 신중한 안내형 문장도 가능하다. 단, 첫 문장을 주제 정의나 장비/제도 설명으로 시작하지 않는다."
    mapping = {
        "의문문 강제": "도입부 첫 문장은 반드시 독자에게 직접 묻는 의문문으로 작성한다. 문장 끝은 반드시 물음표(?)로 끝낸다.",
        "체크리스트형": "도입부 첫 5문장 안에 체크리스트를 넣고, 각 항목은 독자의 실제 상황을 짚는 질문형 또는 짧은 상황형 문장으로 작성한다.",
        "많이 묻는 질문 인용형": "도입부 초반에 실제 사람들이 자주 묻는 질문을 따옴표 또는 질문문 형태로 재구성한다. 첫 블록에 물음표가 보이게 한다.",
        "대화체형": "도입부 첫 부분을 실제 상담에서 나올 법한 짧은 대화체 질문이나 독자에게 말 거는 문장으로 시작한다.",
        "장면 묘사형": "도입부 첫 문장은 독자가 겪는 구체적인 생활 장면이나 상황 묘사로 시작한다. 의문문이 아니어도 되지만 정보 정의문은 금지한다.",
        "전문가 안내형": "도입부 첫 문장은 차분한 안내형 평서문도 가능하다. 다만 주제 정의로 시작하지 말고 독자가 확인해야 할 기준이나 판단 상황을 먼저 짚는다.",
    }
    return mapping.get(first_sentence_type, "선택한 첫문장 형태를 유지한다.")


def first_sentence_force_block(first_sentence_type, keyword, intro_type=""):
    kw = keyword or "핵심 키워드"
    first_sentence_type = first_sentence_type or "자동 추천"
    common = f"""[도입 첫문장 형태 필수 규칙]
- 선택한 첫문장 형태: {first_sentence_type}
- 첫 문장을 “{kw}은/는 무엇입니다”, “{kw}은/는 ~입니다”, “최근 많은 분들이 ~” 같은 정보 설명형으로 시작하지 않는다.
- 첫 문장은 반드시 B등급 고민패턴에서 확인된 독자의 상황, 질문, 판단 혼란, 비용 불안, 선택 불안을 먼저 건드린다.
- 자료에 없는 증상, 감정, 비용 불안, 선택 상황을 GPT가 임의로 만들지 않는다.
- B등급 고민이 부족하면 구체적인 공감문을 억지로 만들지 말고, “내 상황에 맞는 기준을 확인한다” 수준으로만 쓴다.
- 도입 첫문장과 본문 브릿지는 같은 문장을 반복하지 않는다."""
    if first_sentence_type == "자동 추천":
        return common + """
- 도입 방식에 맞춰 의문문/체크리스트/FAQ/대화체/장면형/전문가 안내형 중 가장 자연스러운 첫문장을 선택한다."""
    if first_sentence_type == "의문문 강제":
        return common + """
- 도입부 첫 문장은 반드시 독자에게 직접 묻는 의문문으로 작성한다.
- 첫 문장 끝은 반드시 물음표(?)로 끝낸다.
- 예: ‘자다가 손이 저려 깨는 일이 반복되고 계신가요?’처럼 구체적인 상황을 묻는다."""
    if first_sentence_type == "체크리스트형":
        return common + """
- 도입부 첫 5문장 안에 체크리스트 3~5개를 반드시 넣는다.
- 체크리스트 항목은 ‘□’, ‘-’, ‘✓’ 중 하나로 표시한다.
- 각 항목은 독자가 자신의 상황을 바로 대입할 수 있어야 한다."""
    if first_sentence_type == "많이 묻는 질문 인용형":
        return common + """
- 도입부 초반에 따옴표가 있는 질문문 또는 질문 2~3개를 배치한다.
- 첫 블록 안에 반드시 물음표(?)가 보여야 한다.
- 실제 Q&A 문장을 그대로 복사하지 말고 반복 질문 패턴만 재구성한다."""
    if first_sentence_type == "대화체형":
        return common + """
- 도입부 첫 부분에 실제 상담에서 나올 법한 짧은 대화체 문장을 넣는다.
- ‘원장님, 이럴 때도 필요한가요?’처럼 자연스럽게 말 걸 수 있으나 가짜 후기나 실제 경험담처럼 쓰지 않는다."""
    if first_sentence_type == "장면 묘사형":
        return common + """
- 첫 문장은 독자가 겪는 구체적인 장면으로 시작한다.
- 의문문이 아니어도 되지만, 추상적인 정보 설명은 금지한다.
- 예: ‘아침마다 손끝이 저려 컵을 잡는 일도 조심스러워질 수 있습니다.’"""
    if first_sentence_type == "전문가 안내형":
        return common + """
- 첫 문장은 전문가가 차분히 기준을 안내하는 흐름으로 작성한다.
- 감정을 과하게 키우지 말고, ‘먼저 확인해야 할 기준’을 앞에 둔다.
- 단, 주제 정의문으로 시작하지 않는다."""
    return common

def _shorten_line(line, n=52):
    line = re.sub(r"^[-•·\d\.\)\s]+", "", str(line)).strip()
    line = re.sub(r"\s+", " ", line)
    return line[:n].rstrip() + ("..." if len(line) > n else "")


def build_emotion_flow_plan(topic, keyword, voice_type, b_lines, field=""):
    """조사자료에서 나온 B등급 고민을 전 분야 감정 흐름으로 변환한다.
    v5.3: 감정문장 후보마다 근거 고민을 함께 표시해 GPT가 임의 공감문을 만들지 않게 한다.
    """
    topic = (topic or keyword or "이 주제").strip()
    kw = (keyword or topic).strip()
    worries = []
    for x in b_lines or []:
        sx = _shorten_line(x, 90)
        if sx and sx not in worries:
            worries.append(sx)
        if len(worries) >= 5:
            break

    has_grounded_worries = len(worries) > 0
    if not has_grounded_worries:
        worries = [
            "B등급 고민자료가 부족해 구체적인 독자 상황을 확정하기 어려움",
            "자료에 확인된 반복 질문이 부족하므로 일반적인 선택 기준 중심으로 접근 필요",
            "효과·비용·기간·주의사항 등 실제 불안 포인트 추가 확인 필요",
            "자료에 없는 생활 장면을 임의로 만들지 말아야 하는 상황",
            "독자 상황을 단정하지 말고 현재 조건 확인으로 정리해야 하는 상황",
        ]
    while len(worries) < 5:
        worries.append(worries[-1])

    def qmark(text):
        return text if text.endswith("?") else text.rstrip(".다요") + "나요?"

    if voice_type == "일상 불편형":
        firsts = [
            f"{worries[0]} 때문에 일상에서 계속 신경 쓰이고 계신가요?",
            f"처음에는 대수롭지 않게 넘겼지만 {worries[0]}이/가 반복되면 고민이 깊어질 수 있습니다.",
            f"작은 불편처럼 보여도 {worries[0]}이/가 이어지면 어디서부터 확인해야 할지 막막할 수 있습니다.",
        ]
    elif voice_type == "판단 혼란형":
        firsts = [
            f"{worries[0]}이/가 정상적인 범위인지, 확인이 필요한 신호인지 헷갈리고 계신가요?",
            f"{worries[0]} 때문에 단순한 문제인지 다른 원인이 있는지 구분하기 어려울 수 있습니다.",
            f"검색해도 답이 다르게 느껴지는 이유는 {worries[0]}처럼 상황마다 판단 기준이 달라질 수 있기 때문입니다.",
        ]
    elif voice_type == "감정 직면형":
        firsts = [
            f"{worries[0]}을/를 마주한 순간, 마음이 쉽게 정리되지 않을 수 있습니다.",
            f"{worries[0]} 때문에 감정적으로 크게 흔들리는 것은 자연스러운 반응일 수 있습니다.",
            f"지금은 감정도 크지만, 동시에 어떤 기준으로 대응해야 할지 확인해야 하는 시점입니다.",
        ]
    elif voice_type == "억울함 공감형":
        firsts = [
            f"{worries[0]} 때문에 억울하고 답답한 상황이 이어지고 계신가요?",
            f"분명 내 입장에서는 납득하기 어려운데 {worries[0]}이/가 이어진다면 막막할 수밖에 없습니다.",
            f"감정적으로 대응하고 싶어지는 상황일수록, 먼저 확인해야 할 기준을 정리하는 것이 필요합니다.",
        ]
    elif voice_type == "비교 고민형":
        firsts = [
            f"{worries[0]} 때문에 무엇을 선택해야 할지 고민하고 계신가요?",
            f"비슷해 보이는 선택지라도 {worries[0]}처럼 내 상황에 맞는 기준은 다를 수 있습니다.",
            f"후기만 보면 더 헷갈릴 수 있어, 먼저 비교 기준을 차분히 나눠볼 필요가 있습니다.",
        ]
    elif voice_type == "비용 불안형":
        firsts = [
            f"{worries[0]} 때문에 비용을 들여도 괜찮을지 망설이고 계신가요?",
            f"가격 차이가 클수록 {worries[0]}처럼 무엇을 기준으로 선택해야 할지 더 불안해질 수 있습니다.",
            f"비용만 먼저 비교하면 정작 중요한 조건을 놓칠 수 있습니다.",
        ]
    elif voice_type == "선택 불안형":
        firsts = [
            f"후기와 정보는 많은데 {worries[0]} 때문에 선택이 더 어려워지고 계신가요?",
            f"정보가 많을수록 {worries[0]}처럼 오히려 어디를 믿어야 할지 막막해질 수 있습니다.",
            f"선택 전에는 장점보다 내 상황에 맞는 확인 기준을 먼저 보는 것이 좋습니다.",
        ]
    elif voice_type == "후회 예방형":
        firsts = [
            f"{topic}을/를 시작하기 전, {worries[0]} 때문에 망설여진다면 먼저 확인해야 할 기준이 있습니다.",
            f"결정하고 난 뒤 알게 되면 아쉬운 부분들이 있어, 시작 전에 {worries[0]}부터 기준을 잡는 것이 중요합니다.",
            f"후기만 보고 서두르기보다, 내 상황에 맞는지 먼저 확인해보는 것이 좋습니다.",
        ]
    elif voice_type == "질문 응답형":
        firsts = [
            f"“{worries[0]}”처럼 궁금해하는 분들이 많습니다.",
            f"상담이나 검색에서 자주 나오는 질문은 결국 ‘내 상황에도 맞을까?’라는 고민으로 이어집니다.",
            f"많이 묻는 질문부터 하나씩 정리하면 선택 기준을 더 쉽게 잡을 수 있습니다.",
        ]
    else:  # 전문가 안내형
        firsts = [
            f"{topic}은/는 단정하기보다 {worries[0]}을/를 기준에 따라 차분히 확인하는 것이 중요합니다.",
            f"정보를 많이 보는 것보다 내 상황에 어떤 기준을 적용해야 하는지 살피는 과정이 먼저입니다.",
            f"개인 상태와 조건에 따라 접근이 달라질 수 있어, 핵심 기준을 순서대로 확인해보는 것이 좋습니다.",
        ]

    bridges = [
        f"{worries[1]} — 이 고민을 먼저 짚고, 그 다음 A등급 팩트로 원리/정의/기준을 설명한다.",
        f"{worries[2]} — 독자가 망설이는 이유를 짚은 뒤 효과/절차/비교/주의사항으로 연결한다.",
        f"{worries[3]} — 선택 불안이나 후회 포인트를 짚고, 확인 기준 또는 상담 기준으로 정리한다.",
    ]
    endings = [
        f"결국 중요한 것은 {topic} 자체보다, {worries[4]}을/를 기준으로 내 상황에 맞는지 확인하는 과정입니다.",
        "자료에 나온 고민을 기준으로 현재 상태와 조건을 차분히 확인한 뒤 결정하는 흐름으로 마무리한다.",
    ]

    ground_notice = "B등급 고민자료 기반" if has_grounded_worries else "B등급 고민자료 부족: 구체 공감문 임의 생성 금지"
    return f"""[전 분야 감정 흐름 설계]
선택 화법: {voice_type}
화법 설명: {voice_style_instruction(voice_type)}
감정문장 생성 기준: {ground_notice}

감정 도입 첫문장 후보 3개:
1. 문장: {firsts[0]}
   근거 B등급 고민: {worries[0]}
2. 문장: {firsts[1]}
   근거 B등급 고민: {worries[0]}
3. 문장: {firsts[2]}
   근거 B등급 고민: {worries[0]}

본문 고민 브릿지 후보 3개:
1. 문장: {bridges[0]}
   근거 B등급 고민: {worries[1]}
2. 문장: {bridges[1]}
   근거 B등급 고민: {worries[2]}
3. 문장: {bridges[2]}
   근거 B등급 고민: {worries[3]}

마무리 재연결 문장 후보 2개:
1. 문장: {endings[0]}
   근거 B등급 고민: {worries[4]}
2. 문장: {endings[1]}
   근거 B등급 고민: B등급 고민 전체 요약

사용 규칙:
- 감정 도입, 본문 브릿지, 마무리 재연결은 반드시 B등급 잠재고객 고민패턴에서 확인된 내용으로 만든다.
- 원문 문장을 그대로 복사하지 말고 상담형 문장으로 재구성한다.
- 자료에 없는 증상, 불안, 가격 고민, 비교 대상을 임의로 추가하지 않는다.
- 도입부에 강한 감정/상황 질문을 넣고, 본문에서는 같은 말을 반복하지 않는다.
- 본문에는 브릿지를 2~3곳만 자연스럽게 배치한다. 1000~1500자 원고에서는 과하게 넣지 않는다.
- 마무리는 홈페이지 정보가 없으면 업체/병원 철학을 만들지 말고, 독자가 확인할 기준으로 정리한다."""



def recommend_intro_style(field, topic, keyword, research_text, voice_type=""):
    """주제/자료/화법을 보고 달로썸 도입 8가지 중 기본 추천안을 고른다. 사용자는 언제든 바꿀 수 있다.
    v6.1: '확인할 점/체크/주의/선택 전' 주제는 비교어가 섞여 있어도 체크리스트를 우선 추천한다.
    """
    topic_text = " ".join([topic or "", keyword or ""])
    text = " ".join([field or "", topic or "", keyword or "", research_text or "", voice_type or ""])

    # 1) 제목/주제가 '확인할 점, 체크할 것, 주의사항, 선택 전'이면 체크리스트가 우선.
    #    조사자료 안에 '가격 비교', 'A/B 비교' 같은 단어가 있어도 도입 방식은 체크리스트가 더 자연스럽다.
    checklist_priority_words = [
        "확인할 점", "확인할것", "확인할 것", "체크할", "체크리스트", "주의사항", "주의할", "알아둘", "선택 전", "시술 전", "수술 전", "소송 전", "계약 전", "구매 전", "받기 전", "하기 전", "전 확인", "기준", "놓치기 쉬운", "후회", "업체 선택", "병원 선택", "고르기 전"
    ]
    if any(w in topic_text for w in checklist_priority_words):
        return "1. 독자의 상황을 찔러주는 체크리스트 활용"

    # 2) 본문/조사자료에 명확한 체크 성격이 강하면 체크리스트 추천.
    if any(w in text for w in ["체크리스트", "확인 기준", "확인해야", "점검", "자가", "증상", "냄새", "얼룩", "따갑", "저림", "통증", "관리법", "A/S", "추가요금", "작업 범위", "계약 조건"]):
        return "1. 독자의 상황을 찔러주는 체크리스트 활용"

    # 3) 명확히 A vs B, 차이점, 비교 주제일 때만 비교표 우선.
    compare_topic_words = ["차이", "차이점", "비교", "vs", "VS", "장단점", "무엇이 더", "뭐가 더", "A와 B", "둘 중", "울쎄라", "인모드", "슈링크", "써마지와", "전기면도기", "날면도기"]
    if any(w in topic_text for w in compare_topic_words):
        return "2. 비교 표 활용"

    # 4) 조사자료에 비교어가 있어도 주제 자체가 비교글이 아니면 섣불리 비교표로 가지 않는다.
    if any(w in text for w in ["차이", "비교", "vs", "VS", "가격 비교"]):
        if any(w in text for w in ["무엇이 다른", "뭐가 다른", "장단점", "둘 중", "A와 B", "VS"]):
            return "2. 비교 표 활용"

    if any(w in text for w in ["자주 묻", "많이 묻", "FAQ", "질문", "하이닥", "닥터나우", "지식iN", "로톡", "상담 사례"]):
        return "6. 많이 묻는 질문 인용"
    if any(w in text for w in ["뉴스", "기사", "최근", "보도", "통계", "자료에 따르면"]):
        return "4. 뉴스 기사 활용"
    if any(w in text for w in ["검색만으로", "잘 알려지지", "놓치기 쉬운", "알짜", "모르는"]):
        return "7. 검색만으로는 모르는 알짜 정보 예고"
    if any(w in text for w in ["웹툰", "장면", "만화", "스토리"]):
        return "8. 간단한 웹툰 만들어 넣기"
    if any(w in text for w in ["원장님", "변호사님", "라고 묻", "상담", "대화"]):
        return "3. 대화체 문구"
    return "5. 독자에게 질문 던지기"


def intro_style_instruction(intro_type):
    if not intro_type or intro_type == "자동 추천":
        return "자료와 주제에 맞는 달로썸 도입 8가지 중 하나를 자연스럽게 선택해 사용한다."
    mapping = {
        "1. 독자의 상황을 찔러주는 체크리스트 활용": "도입부에 3~5개의 체크리스트를 넣어 독자가 자신의 상황을 바로 대입하게 만든다.",
        "2. 비교 표 활용": "도입부 또는 도입 직후에 간단한 비교표를 넣어 선택 고민을 정리한다.",
        "3. 대화체 문구": "실제 상담에서 나올 법한 짧은 질문이나 대화 문장으로 시작한다. 단, 가짜 후기는 만들지 않는다.",
        "4. 뉴스 기사 활용": "최근 이슈나 보도/자료 흐름을 언급하되, 확인되지 않은 통계나 뉴스는 지어내지 않는다.",
        "5. 독자에게 질문 던지기": "첫 문장을 독자 상황을 찌르는 질문으로 시작한다.",
        "6. 많이 묻는 질문 인용": "실제 Q&A 문장을 복사하지 말고, 반복 질문 패턴을 재구성해 ‘많이 묻는 질문’처럼 시작한다.",
        "7. 검색만으로는 모르는 알짜 정보 예고": "검색으로는 놓치기 쉬운 판단 기준을 예고하며 시작한다.",
        "8. 간단한 웹툰 만들어 넣기": "1~3컷 장면 구성 또는 장면 묘사로 시작하되, 실제 이미지를 요구하지 않고 텍스트 구성안으로 처리한다.",
    }
    return mapping.get(intro_type, "선택한 도입 방식을 유지한다.")




def intro_force_block(intro_type):
    """선택한 도입 8가지가 초안에서 실제 형식으로 보이도록 강제하는 블록."""
    if not intro_type or intro_type == "자동 추천":
        return """[도입 방식 필수 적용 규칙]
- 자료와 주제에 맞는 달로썸 도입 8가지 중 1개를 선택해 도입부에 실제 형식으로 반영한다.
- 도입 방식은 단순 참고가 아니라 도입부 구조에 보여야 한다.
- 도입부가 일반 설명문으로만 시작하면 지시 불이행으로 본다."""
    if intro_type == "1. 독자의 상황을 찔러주는 체크리스트 활용":
        return """[도입 방식 필수 적용 규칙 - 체크리스트]
- 도입부 첫 5문장 안에 체크리스트를 반드시 넣는다.
- 체크리스트는 3~5개로 작성한다.
- 각 항목은 실제 독자 고민이나 상황이어야 한다.
- 체크리스트 없이 일반 설명으로만 시작하면 지시 불이행이다."""
    if intro_type == "2. 비교 표 활용":
        return """[도입 방식 필수 적용 규칙 - 비교 표]
- 비교표는 본문 중간이 아니라 도입부에서 반드시 사용한다.
- 제목 다음 첫 소제목 또는 첫 문단 직후에 배치한다.
- 비교표는 반드시 마크다운 표 형식으로 작성한다.
- 표에는 반드시 `|---|---|---|` 구분선을 포함한다.
- 표 이후에 표 내용을 자연스럽게 풀어서 설명한다.
- 아래 형식을 따른다.

| 구분 | A | B |
|---|---|---|
| 방식 |  |  |
| 연결되는 고민 |  |  |
| 확인 기준 |  |  |

- 비교표를 도입부가 아닌 본문 중간에만 넣으면 지시 불이행이다."""
    if intro_type == "3. 대화체 문구":
        return """[도입 방식 필수 적용 규칙 - 대화체]
- 도입부 첫 부분에 실제 상담에서 나올 법한 짧은 대화형 문장을 넣는다.
- 예: “둘 중 뭐가 더 좋은가요?”처럼 반복 질문 패턴을 재구성한다.
- 가짜 후기나 실제 경험담처럼 쓰지 않는다."""
    if intro_type == "4. 뉴스 기사 활용":
        return """[도입 방식 필수 적용 규칙 - 뉴스/자료형]
- 도입부에서 최근 관심 증가, 자료 흐름, 업계 이슈 등을 언급한다.
- 확인되지 않은 통계, 기사명, 수치는 지어내지 않는다.
- 뉴스 느낌만 내고 근거 없는 단정으로 시작하지 않는다."""
    if intro_type == "5. 독자에게 질문 던지기":
        return """[도입 방식 필수 적용 규칙 - 질문형]
- 첫 문장은 독자의 실제 상황을 묻는 질문으로 시작한다.
- 질문은 막연한 질문이 아니라 자료에서 나온 고민을 반영한다.
- 예: “자다가 손이 저려 깨고, 손을 털면 잠깐 괜찮아지는 일이 반복되고 계신가요?”"""
    if intro_type == "6. 많이 묻는 질문 인용":
        return """[도입 방식 필수 적용 규칙 - FAQ 인용]
- 도입부 초반에 실제 사람들이 자주 묻는 질문을 재구성해 넣는다.
- 실제 Q&A 문장을 그대로 복사하지 않는다.
- “많은 분들이 ‘~’라고 묻습니다” 또는 “상담에서 자주 나오는 질문은 ~입니다” 형태를 사용할 수 있다."""
    if intro_type == "7. 검색만으로는 모르는 알짜 정보 예고":
        return """[도입 방식 필수 적용 규칙 - 알짜정보 예고]
- 도입부에서 검색만으로 놓치기 쉬운 판단 기준을 예고한다.
- ‘검색해도 정보는 많지만 정작 중요한 기준은 다를 수 있다’는 흐름을 만든다.
- 과한 비밀/충격식 표현은 쓰지 않는다."""
    if intro_type == "8. 간단한 웹툰 만들어 넣기":
        return """[도입 방식 필수 적용 규칙 - 웹툰/장면]
- 도입부에 1~3컷 장면 구성 또는 짧은 장면 묘사를 넣는다.
- 실제 이미지를 만들지 말고 텍스트 구성안으로 처리한다.
- 장면 이후 본문 도입으로 자연스럽게 연결한다."""
    return "[도입 방식 필수 적용 규칙]\n- 선택한 도입 방식을 도입부에서 눈에 보이게 반영한다."


def title_force_block(title_type, keyword):
    kw = keyword or "핵심 키워드"
    base = f"""[제목 필수 기준]
- 제목은 가능하면 핵심 키워드 “{kw}”로 시작한다.
- 핵심 키워드는 제목에 1회만 넣는다.
- 제목은 가능하면 30자 이내로 작성한다.
- 자극적인 어그로가 아니라 독자의 실제 고민과 호기심을 건드린다.
- 본문 내용과 다른 제목을 만들지 않는다.
- 제목 후보 3개를 먼저 제시한 뒤, 가장 적합한 제목 1개를 최종 제목으로 사용한다.
- 출력 형식은 반드시 아래처럼 제목을 분리한다.

제목 후보:
1. ...
2. ...
3. ...

최종 제목:
...

본문:
..."""
    if not title_type or title_type == "선택 안함":
        return base + "\n- 특정 제목 유형은 강제하지 않는다."
    if title_type == "자동 추천":
        return base + "\n- 자료와 주제에 맞는 제목 유형을 6가지 중에서 자동 선택한다."
    return base + f"\n- 선택한 제목 유형 “{title_type}”을 반드시 반영한다."


def output_hygiene_block():
    return """[출력 정리 규칙]
- 출처 찌꺼기나 검색 흔적을 본문에 남기지 않는다.
- `+1`, `[1]`, `[2]`, `cite`, `source`, `reference`, `�` 같은 표시는 출력하지 않는다.
- 출처명이나 링크를 본문 중간에 끼워 넣지 않는다.
- 자료는 참고만 하고 원고는 자연스러운 블로그 문장으로 작성한다.
- 현재 별도 홈페이지/업체 정보가 제공되지 않았다면 마무리에서 “저희 병원은”, “본원은”, “저희는”, “우리 병원은”, “대표원장은”, “환자 중심”, “정직한 진료”, “풍부한 경험”처럼 기관 철학·장점·운영방침을 절대 지어내지 않는다.
- 홈페이지 정보가 없을 때의 마무리는 병원 홍보가 아니라 정보형 정리로 끝낸다."""


def emotion_grounding_force_block():
    return """[B등급 고민 기반 감정문장 필수 규칙]
- 감정 도입 첫문장, 본문 고민 브릿지, 마무리 재연결 문장은 반드시 B등급 잠재고객 고민패턴에서 확인된 내용으로 만든다.
- A등급 팩트는 원리/효과/주의사항 설명에 사용하고, 독자 감정·상황 문장은 B등급 고민에서 가져온다.
- C등급은 말맛 참고만 가능하며, 가짜 후기나 개인 경험담으로 만들지 않는다.
- 자료에 없는 증상, 감정, 비용 고민, 비교 대상, 생활 장면을 임의로 추가하지 않는다.
- 원문 질문/후기 문장을 그대로 베끼지 말고, 같은 고민을 상담형 문장으로 재구성한다.
- B등급 고민이 부족하면 구체적인 공감문을 억지로 만들지 말고, ‘내 상황에 맞는 기준 확인’ 정도로만 표현한다.
- 첫 문장을 만들 때는 [전 분야 감정 흐름 설계]의 ‘근거 B등급 고민’을 확인하고 그 범위 안에서 작성한다.
- 첫 문장에는 B등급 고민의 핵심어를 최소 1~2개 이상 직접 반영한다. 예: 효과 없음, 부작용 걱정, 비용 부담, 기저질환, 비교 혼란, 선택 불안.
- 첫 문장이 물음표로 끝나더라도 B등급 고민 핵심어가 빠져 있으면 감정 도입으로 보지 않는다."""



def homepage_info_force_block(homepage_mode="홈페이지 정보 없음", homepage_info=""):
    """홈페이지/업체 정보가 있을 때만 마무리 홍보 문구를 허용하되, 입력 정보 밖으로 확장하지 않게 하는 규칙."""
    info = (homepage_info or "").strip()
    if homepage_mode == "홈페이지 정보 있음" and info:
        return f"""[홈페이지/업체 정보 반영 규칙]
- 아래 정보는 사용자가 직접 확인해 입력한 홈페이지/업체 정보다.
- 이 정보 안에서만 원장/대표 소개, 진료·운영 철학, 병원/업체 장점, 상담 기준을 정리한다.
- 정보에 없는 경력, 수상, 장비, 전문센터, 누적 건수, 원장명, 진료 철학, 장점을 새로 만들지 않는다.
- 홈페이지 원문을 길게 복사하지 말고, 원고 주제와 관련 있는 내용만 1~2문장으로 압축해 마무리에 자연스럽게 연결한다.
- 마무리에서 ‘저희 병원은/본원은/저희 법무법인은’ 문구를 사용할 수는 있지만, 반드시 아래 확인 정보에 근거해야 한다.
- 병원/법률/금융 분야에서는 ‘최고’, ‘유일’, ‘100%’, ‘보장’, ‘반드시 해결’ 같은 과장 표현을 쓰지 않는다.
- 홈페이지 정보가 원고 주제와 관련이 약하면 억지로 홍보하지 말고, 상담 기준 또는 확인 기준 수준으로만 연결한다.

[사용자가 입력한 홈페이지/업체 정보]
{info}

[마무리에 반영할 때 정리할 항목]
1. 원장/대표 소개: 입력 정보에 실제로 있는 경우에만 1문장 이내로 반영
2. 진료/운영 철학: 입력 정보에 실제로 있는 표현만 부드럽게 재구성
3. 병원/업체 장점: 장비, 검사, 상담, 관리, 접근성 등 입력 정보에 있는 장점만 반영
4. 주제와 연결: 이번 글의 핵심 고민 해결 흐름과 자연스럽게 연결
5. 분량: 마무리 전체에서 홈페이지 정보 반영은 1~2문장 정도로 제한"""
    return """[홈페이지/업체 정보 반영 규칙]
- 이번 프롬프트에는 별도 홈페이지 철학/병원 강점/업체 장점 정보가 제공되지 않았다.
- 따라서 마무리에서 “본원은”, “저희 병원은”, “저희는”, “대표원장은”, “저희 법무법인은”으로 시작하는 홍보성 문장을 만들지 않는다.
- 마지막 문단은 독자가 자기 상태를 확인하고 상담 전 체크할 기준을 정리하는 정보형 마무리로 작성한다.
- 사용자가 별도 홈페이지 정보를 제공하지 않았다면 병원 철학, 진료 철학, 장점, 경력, 전문성 문구를 임의로 만들지 않는다."""


def homepage_summary_guide(homepage_info):
    """입력된 홈페이지 정보를 사람이 확인하기 쉽게 후보 항목별로 간단히 분류한다."""
    info = (homepage_info or "").strip()
    if not info:
        return "홈페이지 정보가 비어 있습니다. 이 상태에서는 원장 소개, 철학, 병원 장점을 임의로 만들지 않습니다."
    lines = [re.sub(r"\s+", " ", x.strip(" -•·\t")) for x in re.split(r"[\n\r]+", info) if x.strip()]
    def pick(keys, max_n=5):
        out=[]
        for line in lines:
            if any(k in line for k in keys) and line not in out:
                out.append(line)
            if len(out)>=max_n:
                break
        return out
    director = pick(["원장", "대표", "전문의", "의사", "변호사", "대표변호사", "경력", "약력", "학회", "전담", "전문"])
    philosophy = pick(["철학", "원칙", "지향", "중심", "정직", "충분", "꼼꼼", "세심", "맞춤", "소통", "설명", "안전", "신뢰"])
    strengths = pick(["장비", "검사", "시스템", "센터", "야간", "주차", "예약", "관리", "사후", "정품", "개인별", "맞춤", "상담", "진료", "시술", "소송", "가압류", "강제집행"])
    def fmt(title, arr):
        if not arr:
            return f"{title}: 확인된 문구 없음"
        return title + ":\n" + "\n".join([f"- {x}" for x in arr])
    return "\n\n".join([
        fmt("원장/대표 소개 후보", director),
        fmt("철학/상담 기준 후보", philosophy),
        fmt("병원/업체 장점 후보", strengths),
        "마무리 반영 원칙:\n- 위 후보 중 주제와 직접 연결되는 것만 1~2문장으로 압축\n- 없는 장점·경력·철학은 추가 금지\n- 과장 대신 확인된 정보 기반의 담백한 상담 유도"
    ])

def build_emotion_bridge_plan(topic, keyword, voice_type, b_lines):
    """B등급 고민이 도입부에서만 사라지지 않도록 문단별 배치안을 만든다."""
    topic = (topic or keyword or "이 주제").strip()
    # 핵심 고민 후보를 4개까지 사용
    clean = []
    for x in b_lines or []:
        xx = re.sub(r"^[-•·\d\.\)\s]+", "", str(x)).strip()
        if xx and xx not in clean:
            clean.append(xx)
        if len(clean) >= 4:
            break
    while len(clean) < 4:
        defaults = [
            f"{topic}을 검색하는 독자가 가장 먼저 헷갈리는 지점",
            "증상이 정상 범위인지 문제 신호인지 판단하기 어려운 상황",
            "검사나 상담이 필요한지 몰라 망설이는 상황",
            "혼자 넘겨도 되는지, 지금 확인해야 하는지 고민하는 상황",
        ]
        clean.append(defaults[len(clean)])

    return f"""[문단별 고민 배치안]
도입부:
- 가장 강한 고민을 먼저 짚는다: {clean[0]}
- 단순 위로문이 아니라 실제 검색자가 겪는 장면과 판단 혼란을 문장으로 만든다.

본문 1 시작/전환부:
- 설명으로 바로 들어가지 말고 이 고민을 먼저 건드린다: {clean[1]}
- 그 다음 A등급 팩트로 원인/정의/구조를 설명한다.

본문 2 시작/전환부:
- 증상 반복, 일상 불편, 악화 상황에 대한 고민을 짚는다: {clean[2]}
- 그 다음 A등급 팩트로 기준/구분/주의사항을 설명한다.

본문 3 시작/전환부:
- 검사, 치료, 비용, 선택 불안처럼 독자가 망설이는 지점을 짚는다: {clean[3]}
- 그 다음 검사/치료/선택 기준을 신중하게 설명한다.

마무리:
- 독자의 현재 상황으로 다시 돌아온다.
- 과한 상담 유도보다 “혼자 단정하지 말고 현재 상태를 확인해보자”는 흐름으로 마무리한다.

금지:
- B등급 고민을 도입부에만 쓰고 본문은 A등급 팩트 나열로 끝내지 말 것.
- 모든 문단에 “힘드셨나요/불안하시죠”를 반복하지 말 것.
- 공감문장을 많이 넣는 것이 아니라, 고민을 설명의 입구로 사용할 것."""

def build_draft_prompt(topic, keyword, field, content_type, voice_type, intro_type, title_type, a_lines, b_lines, c_lines, extra_rules="", target_len=1500, spacing_type="공백 제외", paragraph_option="분량 우선, 문단 수 자연 조절", prompt_mode="달로썸 GPTs용", first_sentence_type="자동 추천", homepage_mode="홈페이지 정보 없음", homepage_info="", keyword_delivery_text="", keyword_placement_text="", usecase_mode="블로그 정보성"):

    usecase_mode = usecase_mode or "블로그 정보성"
    usecase_block = usecase_style_block(usecase_mode, field)
    a_text = "\n".join([f"- {x}" for x in a_lines]) if a_lines else "- 아직 정리된 A등급 공통정보가 부족합니다. 제공된 자료 안에서 공통 사실만 신중하게 사용하세요."
    b_text = "\n".join([f"- {x}" for x in b_lines]) if b_lines else "- 아직 정리된 고민패턴이 부족합니다. 독자가 검색하는 이유를 먼저 추정하되 단정하지 마세요."
    c_text = "\n".join([f"- {x}" for x in c_lines]) if c_lines else "- 말맛 참고자료가 부족하므로 가짜 후기나 경험담은 만들지 마세요."
    bridge_plan = build_emotion_bridge_plan(topic, keyword, voice_type, b_lines)
    emotion_flow_plan = build_emotion_flow_plan(topic, keyword, voice_type, b_lines, field)
    length_plan = length_guidance(target_len, spacing_type, paragraph_option)
    keyword_plan = keyword_delivery_text.strip() if keyword_delivery_text and keyword_delivery_text.strip() else keyword_count_instruction(keyword, target_len)
    keyword_placement_text = keyword_placement_text.strip() if keyword_placement_text else ""
    intro_type = intro_type or "자동 추천"
    title_type = title_type or "자동 추천"
    intro_plan = intro_style_instruction(intro_type)
    first_sentence_type = first_sentence_type or "자동 추천"
    first_sentence_plan = first_sentence_instruction(first_sentence_type, intro_type)
    title_plan = title_style_instruction(title_type)
    intro_force = intro_force_block(intro_type)
    first_sentence_force = first_sentence_force_block(first_sentence_type, keyword, intro_type)
    title_force = title_force_block(title_type, keyword)
    hygiene_force = output_hygiene_block()
    emotion_grounding_force = emotion_grounding_force_block()
    homepage_force = homepage_info_force_block(homepage_mode, homepage_info)
    if prompt_mode == "외부 GPTs용 강제 프롬프트":
        mode_notice = "외부 GPTs용입니다. 아래 조건은 추천이 아니라 필수 작성 조건입니다. 조건을 지키지 못하면 다시 작성해야 합니다."
    else:
        mode_notice = "달로썸 GPTs용입니다. 기존 GPTs 설정과 충돌하더라도 아래 선택 조건을 우선 적용합니다."
    if title_type == "선택 안함":
        title_rule = f"제목은 핵심 키워드 ‘{keyword}’를 맨 앞에 1회 넣고 가능하면 30자 이내로 작성해줘. 단, 6가지 제목 유형은 강제하지 말고 주제와 본문에 맞게 자연스럽게 구성해줘."
    elif title_type == "자동 추천":
        title_rule = f"제목은 핵심 키워드 ‘{keyword}’를 맨 앞에 1회 넣고 가능하면 30자 이내로 작성해줘. 자료와 주제에 맞는 제목 유형을 자연스럽게 선택하되 어그로성 제목은 쓰지 마."
    else:
        title_rule = f"제목은 핵심 키워드 ‘{keyword}’를 맨 앞에 1회 넣고 가능하면 30자 이내로 작성해줘. 선택한 제목 유형 ‘{title_type}’을 반영하되, 본문 내용과 다른 어그로성 제목은 쓰지 마."
    title_candidates = "\n".join([f"- {x}" for x in generate_title_candidates(keyword, topic, title_type, b_lines, field)])
    return f"""아래 자료 설계를 바탕으로 블로그 원고 초안을 작성해줘.

주제: {topic}
핵심 키워드: {keyword}
분야: {field}
원고 유형: {content_type}
원고 사용처: {usecase_mode}
프롬프트 출력 방식: {prompt_mode}

{usecase_block}

[중요]
{mode_notice}

선택한 제목 유형: {title_type}
제목 유형 세부 지시: {title_plan}
{title_force}
제목 후보 참고:
{title_candidates}

선택한 도입 화법: {voice_type}
선택한 도입 첫문장 형태: {first_sentence_type}
도입 첫문장 형태 세부 지시: {first_sentence_plan}
선택한 달로썸 도입 방식: {intro_type}
도입 방식 세부 지시: {intro_plan}
{first_sentence_force}
{intro_force}

{hygiene_force}

{emotion_grounding_force}

{homepage_force}

[A등급 공통 핵심정보 - 본문 팩트용]
{a_text}

[B등급 잠재고객 고민패턴 - 제목/도입/소제목/문단 전환부용]
{b_text}

[C등급 말맛 참고 포인트 - 표현 참고용]
{c_text}

{length_plan}
{keyword_plan}
{keyword_placement_text}

{emotion_flow_plan}

{bridge_plan}

작성 지시:
0. {title_rule}
0-1. 원고 사용처 “{usecase_mode}”에 맞는 말투와 금지조건을 반드시 지킨다. 문단 뼈대는 유지하되, 블로그/카페/커뮤니티/후기형에 맞게 문장 길이와 마무리 방식을 조정한다.
1. 도입부는 반드시 “{voice_type}” 화법, “{first_sentence_type}” 첫문장 형태, “{intro_type}” 방식을 함께 반영해 작성해줘.
1-1. 첫 문장은 반드시 위 [도입 첫문장 형태 필수 규칙]을 따른다.
1-1-1. [전 분야 감정 흐름 설계]의 감정 도입 첫문장 후보 중 1개를 첫 문장으로 사용하거나, 같은 근거 B등급 고민 범위 안에서 자연스럽게 재구성해줘.
1-1-2. 첫 문장에는 B등급 고민 핵심어를 최소 1~2개 직접 넣어줘. 물음표만 붙이고 고민어가 빠진 넓은 질문은 금지해줘.
1-2. 첫 문장을 “{keyword}은/는 무엇입니다” 같은 정보 설명으로 시작하지 마.
2. 선택한 달로썸 도입 방식은 추천이 아니라 필수 구조다. 도입부 첫 5문장 안에서 눈에 보이게 반영해줘.
2-1. 비교표 방식이면 마크다운 표와 `|---|---|---|` 구분선을 반드시 넣어줘.
2-2. 제목 후보 3개를 먼저 제시한 뒤 최종 제목 1개를 선택하고, 그 제목으로 원고를 작성해줘.
2-3. 출력은 반드시 “제목 후보:”, “최종 제목:”, “본문:” 라벨을 분리해서 보여줘. 제목을 본문 첫 줄에 붙여서 애매하게 출력하지 마.
3. B등급 고민패턴을 제목, 도입부, 소제목뿐 아니라 본문 주요 문단의 시작/전환부에도 자연스럽게 반영해줘. 단, 반드시 제공된 B등급 고민 안에서만 변환하고 자료에 없는 고민은 만들지 마.
3. A등급 공통 핵심정보는 본문 설명의 뼈대로 사용하되, 팩트만 나열하지 말고 B등급 고민에 답하는 방식으로 설명해줘.
4. C등급은 말투 참고만 하고, 가짜 후기처럼 쓰지 마.
5. 실제 Q&A나 후기 문장을 그대로 복사하지 마.
6. 키워드 “{keyword}”는 위 [기본 납품 설정 / 키워드 요구사항]과 [키워드 배치 지도]를 우선해서 배치해줘. 빠진 문단이 생기지 않게 분산하고, 한 문단에 몰아넣지 마.
7. 단정·과장 표현은 피하고, 개인 상태나 상황에 따라 달라질 수 있다는 신중한 표현을 사용해줘.
8. 소제목을 포함하되, 문단 수는 위 분량 조건을 우선해 자연스럽게 조절해줘.
9. 첫 문장은 “오늘은”, “이번 글에서는”, “알아보겠습니다”로 시작하지 마.
10. 마무리는 강한 구매/상담 유도보다 독자가 자기 상황을 확인하게 만드는 방향으로 작성해줘.
11. 각 주요 문단의 첫 문장 또는 전환부에는 가능한 범위에서 독자가 실제로 헷갈리는 지점/불편한 상황/망설이는 이유를 배치해줘. 단, 1000~1500자 원고에서는 억지로 많이 넣지 말고 2~3곳만 자연스럽게 넣어줘.
12. 공감은 “힘드셨나요?”, “불안하시죠?” 같은 빈 위로가 아니라 실제 B등급 고민 상황을 짚는 방식으로 작성해줘.

피해야 할 표현:
- 100%
- 무조건
- 반드시 좋아짐
- 완벽
- 부작용 없음
- 효과 보장
- 최고/유일
- 가짜 개인 경험담
- 힘드셨나요/불안하시죠/걱정되시죠의 반복

추가 조건:
{extra_rules.strip() if extra_rules.strip() else '- 없음'}
"""

def build_claude_prompt(voice_type, intro_type, title_type, keyword, field, body_text="", first_sentence_type="자동 추천", homepage_mode="홈페이지 정보 없음", homepage_info="", usecase_mode="블로그 정보성"):

    if title_type == "선택 안함":
        title_guard = "특정 제목 유형은 선택하지 않았다. 제목 유형을 억지로 맞추지 말고, 키워드 앞 배치와 30자 이내 권장, 어그로 금지 기준만 유지해줘."
        title_touch_rule = "0. 제목은 키워드 앞 배치와 기본 기준만 유지. 특정 제목 유형 강제 금지"
        title_change_rule = "- 제목 유형을 새로 만들거나 억지로 맞추기 금지"
        title_keep_sentence = "도입 화법과 달로썸 도입 방식은 절대 바꾸지 말고 유지해줘. 제목은 기본 기준만 유지하고 특정 유형을 강제하지 마."
    else:
        title_guard = f"이 원고의 제목 유형은 “{title_type}”이다."
        title_touch_rule = f"0. 제목의 핵심 키워드 앞 배치와 “{title_type}” 유형"
        title_change_rule = "- 제목 유형 변경 금지"
        title_keep_sentence = "제목 유형, 화법, 도입 방식은 절대 바꾸지 말고 유지해줘."
    homepage_guard = homepage_info_force_block(homepage_mode, homepage_info)
    usecase_guard = usecase_style_block(usecase_mode, field)
    usecase_claude_extra = ""
    if usecase_mode == "카페 정보성":
        usecase_claude_extra = """

[카페 정보성 윤문 추가 규칙]
- 대괄호 소제목([시작 전 체크할 상황] 등)은 가능하면 자연스러운 소제목으로 바꾼다. 단, 구조와 순서는 유지한다.
- 네이버 계정/플랫폼 정책 관련 문장은 법률문처럼 단정하지 말고, ‘본인 사용을 전제로 보기 때문에’, ‘피하는 편이 안전합니다’처럼 부드럽게 완화한다.
- ‘추천합니다’가 특정 업체나 행동을 강하게 유도하는 느낌이면 ‘좋습니다’, ‘확인해보는 게 좋습니다’ 정도로 낮춘다.
- 카페 회원이 정보 정리해 공유하는 느낌은 살리되, 실제 경험 없는 ‘제가 해봤는데’ 표현은 넣지 않는다.
"""
    elif usecase_mode == "커뮤니티/바이럴":
        usecase_claude_extra = """

[커뮤니티/바이럴 윤문 추가 규칙]
- 문장을 조금 더 짧고 리듬 있게 다듬되 낚시성, 과장, 허위정보는 넣지 않는다.
- 댓글 유도 느낌은 가능하지만 특정 업체 홍보처럼 보이게 만들지 않는다.
"""
    elif usecase_mode == "후기/리뷰":
        usecase_claude_extra = """

[후기/리뷰 윤문 추가 규칙]
- 실제 경험 자료가 없으면 후기처럼 보이는 1인칭 경험담을 만들지 않는다.
- 경험 자료가 있더라도 과한 칭찬, 별점 조작 느낌, 무조건 추천 표현은 줄인다.
"""
    return f"""아래 원고를 다듬어줘.

[이번 검수/설계 화면에서 새로 불러온 최신 조건]
- 원고 사용처: {usecase_mode}
- 도입 화법: {voice_type}
- 도입 첫문장 형태: {first_sentence_type}
- 달로썸 도입 방식: {intro_type}
- 제목 유형: {title_type}
- 핵심 키워드: {keyword}
- 분야: {field}

아래 최신 조건이 이전 대화나 이전 템플릿보다 우선이다. 바꾼 부분 요약에서도 화법명과 사용처명을 위 값 그대로 사용해줘.

{title_guard}
이 원고의 사용처는 “{usecase_mode}”이다.
{usecase_guard}
{usecase_claude_extra}

이 원고의 도입 화법은 “{voice_type}”이다.
이 원고의 도입 첫문장 형태는 “{first_sentence_type}”이다.
이 원고의 달로썸 도입 방식은 “{intro_type}”이다.
{title_keep_sentence}

건드리면 안 되는 것:
{title_touch_rule}
1. 도입부의 “{voice_type}” 흐름
1-1. 도입 첫문장 형태 “{first_sentence_type}”
2. 도입부의 “{intro_type}” 방식
3. 핵심 키워드 “{keyword}”
3. {field} 분야에 맞는 신중한 톤
4. 핵심 고민 포인트와 제목/소제목 방향
5. 본문 문단마다 들어간 ‘독자가 실제로 헷갈리는 지점’
6. 가짜 후기처럼 보이는 개인 경험 금지
7. 원고 전체 구조 대폭 변경 금지

수정 허용 범위:
- 문장 리듬 개선
- 어미 반복 줄이기
- 어색한 문장 자연스럽게 수정
- AI가 쓴 듯한 딱딱한 표현 완화
- 너무 반복되는 표현 정리

중요:
- 도입부 첫 2~3문장은 감정 도입 보호 문장으로 보고, 정보 설명형 문장으로 바꾸지 말 것.
- 첫문장 형태가 “의문문 강제”라면 첫 문장 끝의 물음표(?)를 없애지 말 것.
- 첫문장 형태가 체크리스트/FAQ/대화체/장면형이면 해당 형식을 일반 정보문으로 바꾸지 말 것.
- 정보 설명만 남기고 감정/고민 문장을 삭제하지 말 것.
- B등급 고민패턴에서 나온 공감 포인트를 살려둘 것.
- “힘드셨나요?”, “불안하시죠?” 같은 흔한 위로문장으로 단순화하지 말 것.
- 공감 문장은 실제 상황, 판단 혼란, 생활 불편을 짚는 방식으로 유지할 것.

{homepage_guard}

금지:
- 새로운 사례나 경험담 추가 금지
- 없는 병원/업체 장점 만들기 금지
- 과장 표현 추가 금지
{title_change_rule}
- 제목에서 키워드 위치 변경 금지
- 도입화법 변경 금지
- 도입 첫문장 형태 변경 금지
- 달로썸 도입 방식 변경 금지
- 원고 사용처 “{usecase_mode}”에 맞는 말투를 다른 채널 말투로 바꾸기 금지
- 본문을 팩트 설명문처럼 딱딱하게 바꾸기 금지
- `+1`, `[1]`, `[2]`, `cite`, `source`, `reference`, `�` 같은 복사 찌꺼기 남기기 금지
- 홈페이지 정보가 없는데 “저희 병원은”, “본원은”, “저희는”, “우리 병원은” 등 기관 철학·장점을 지어내기 금지

수정 후 아래 형식으로 답해줘.
1. 예상 점수
2. 바꾼 부분 요약
   - 바꾼 부분 요약에서 화법명을 언급해야 한다면 반드시 “{voice_type}”이라고 그대로 표기하고, 억울함 공감형/전문가형 등 다른 화법명으로 바꿔 부르지 마.
3. 최종 수정 원고

[원고]
{body_text.strip() if body_text.strip() else '여기에 원고를 붙여넣기'}
"""


st.title("📝 달로썸 원고 검수기 v6.4")
st.caption("GPT 조사 프롬프트 → 자료등급/고민패턴/화법 선택/감정흐름/제목유형/도입8가지 → GPTs용 프롬프트 → 초안 검수 → Claude 윤문 지시까지 한 흐름으로 사용합니다. v6.4에서는 Claude 복붙 지시문이 최신 검수값으로 강제 갱신되도록 수정했습니다.")

tab_research, tab_design, tab_check = st.tabs(["① 의뢰 조건 입력·GPT 조사 프롬프트", "② 조사 결과 붙여넣기·원고 설계", "③ 원고 검수 모드"])

with tab_research:
    st.header("① 의뢰 조건 입력 · GPT 조사 프롬프트")
    st.write("GPT가 먼저 조사하고, 너는 링크를 직접 확인한 뒤 확인된 자료를 ② 원고 설계 모드에 붙여넣는 흐름입니다.")
    col1, col2 = st.columns(2)
    with col1:
        r_topic = st.text_input("조사 주제", value="써마지 시술", key="r_topic")
        r_keyword = st.text_input("핵심 키워드", value="써마지", key="r_keyword")
        r_field = st.selectbox("분야", RESEARCH_FIELDS, index=0, key="r_field")
        r_usecase_mode = st.selectbox("원고 사용처", USECASE_MODES, index=0, key="r_usecase_mode")
        st.caption(usecase_summary_line(r_usecase_mode))
        r_title_type = st.selectbox("희망 제목 유형", TITLE_TYPE_OPTIONS, index=0, key="r_title_type")
        r_voice_choice = st.selectbox("희망 도입 화법", VOICE_TYPE_OPTIONS, index=0, key="r_voice_choice")
        st.caption("자동 추천을 두면 GPT가 조사자료 기준으로 화법을 추천합니다. 직접 선택하면 해당 화법을 우선 고려하게 합니다.")
        r_first_sentence_type = st.selectbox("희망 도입 첫문장 형태", FIRST_SENTENCE_TYPES, index=0, key="r_first_sentence_type")
        st.caption("의문문으로 시작해야 하면 '의문문 강제'를 선택하세요. 체크리스트/FAQ/대화체도 따로 고를 수 있습니다.")
        r_intro_type = st.selectbox("희망 도입 8가지 방식", INTRO_TYPE_OPTIONS, index=0, key="r_intro_type")
    with col2:
        r_goal = st.text_input("원고 목적", value="병원 블로그 원고 작성을 위한 사전 자료조사", key="r_goal")
        r_len_col1, r_len_col2 = st.columns(2)
        with r_len_col1:
            r_length_preset = st.selectbox("희망 분량", LENGTH_PRESETS, index=1, key="r_length_preset")
            r_spacing_type = st.selectbox("분량 기준", SPACING_TYPES, index=0, key="r_spacing_type")
        with r_len_col2:
            if r_length_preset == "직접 입력":
                r_custom_length = st.number_input("직접 입력 글자수", min_value=500, max_value=6000, value=1500, step=100, key="r_custom_length")
            else:
                r_custom_length = int(re.sub(r"[^0-9]", "", r_length_preset) or 1500)
                st.caption("직접 입력 글자수는 ‘희망 분량’을 ‘직접 입력’으로 선택할 때만 표시됩니다.")
            r_paragraph_option = st.selectbox("문단 설정", PARAGRAPH_OPTIONS, index=0, key="r_paragraph_option")
        r_target_len = resolve_target_length(r_length_preset, r_custom_length)
        st.caption(f"조사 프롬프트에 들어갈 분량 조건: {r_spacing_type} {r_target_len}자 내외 / {r_paragraph_option}")
        r_kw_settings = render_keyword_delivery_settings("research", r_keyword, r_target_len, expanded=False)
        r_extra = st.text_area("추가로 중점 조사할 내용", value="통증, 효과 시점, 유지기간, 울쎄라와 차이, 볼패임/얼굴살 빠짐 걱정, 부작용, 시술 후 관리", height=110, key="r_extra")
        st.divider()
        st.subheader("홈페이지 자료 조사")
        r_homepage_mode = st.radio("조사 단계 홈페이지/업체 자료", ["홈페이지 정보 없음", "홈페이지 정보 있음"], index=0, key="r_homepage_mode")
        r_homepage_url = st.text_input("공식 홈페이지 URL 또는 병원/업체명", placeholder="예: https://... 또는 ○○비뇨기과 / ○○법무법인", key="r_homepage_url")
        r_homepage_info = st.text_area("직접 확인한 홈페이지 내용이 있으면 추가 입력", placeholder="선택사항: 원장 약력, 진료 철학, 장비, 상담 방식 등. 비워두면 GPT가 위 URL/업체명으로 공식 홈페이지를 확인하도록 지시합니다.", height=100, key="r_homepage_info")
        st.caption("① 조사 프롬프트에서 GPT가 공식 홈페이지를 함께 확인해 원장 소개·철학·장점을 뽑도록 지시합니다. 확인 불가 시 임의 생성 금지.")

    r_keyword_delivery_text = keyword_delivery_setting_text(r_keyword, r_target_len, r_kw_settings)
    r_keyword_placement_text = keyword_placement_plan_text(r_keyword, r_target_len, r_kw_settings)
    research_prompt = build_research_prompt(r_topic, r_keyword, r_field, r_goal, r_extra, r_target_len, r_spacing_type, r_paragraph_option, r_intro_type, r_title_type, r_voice_choice, r_first_sentence_type, r_homepage_mode, r_homepage_info, r_homepage_url, r_keyword_delivery_text, r_keyword_placement_text, r_usecase_mode)
    st.text_area("GPT에 복붙할 조사 프롬프트", value=research_prompt, height=650)
    st.download_button("조사 프롬프트 txt 다운로드", research_prompt, file_name="dalrosom_research_prompt.txt")

    with st.expander("사용 순서"):
        st.write("""
1. 위 프롬프트를 GPT에 붙여넣고 조사시킵니다.
2. GPT가 준 링크를 직접 열어봅니다.
3. 광고글, 오래된 글, 관련 없는 글은 버립니다.
4. 확인한 자료 요약만 ② 원고 설계 모드에 붙여넣습니다.
5. 프로그램이 A등급 공통정보, B등급 고민패턴, 도입화법, GPTs 초안 프롬프트를 만들어줍니다.
""")

with tab_design:
    st.header("② 조사 결과 붙여넣기 · 원고 설계")
    st.write("①에서 만든 조사 프롬프트로 받은 결과만 붙여넣으면, 원고 설계와 GPTs용 초안 프롬프트를 정리합니다.")
    d_use_research_inputs = st.checkbox("① 의뢰 조건 입력값 그대로 사용", value=True, key="d_use_research_inputs")
    st.caption("켜두면 ①에서 입력한 주제·키워드·분야·분량·키워드 납품 설정을 ②에서 다시 쓰지 않아도 됩니다.")

    d_col1, d_col2 = st.columns(2)
    if d_use_research_inputs:
        d_topic = st.session_state.get("r_topic", "써마지 시술")
        d_keyword = st.session_state.get("r_keyword", "써마지")
        d_field = st.session_state.get("r_field", "병원 / 의료")
        d_usecase_mode = st.session_state.get("r_usecase_mode", "블로그 정보성")
        d_length_preset = st.session_state.get("r_length_preset", "1500자")
        d_spacing_type = st.session_state.get("r_spacing_type", "공백 제외")
        d_custom_length = st.session_state.get("r_custom_length", 1500)
        d_paragraph_option = st.session_state.get("r_paragraph_option", "분량 우선, 문단 수 자연 조절")
        d_target_len = resolve_target_length(d_length_preset, d_custom_length)
        d_kw_settings = r_kw_settings
        st.info(f"① 입력값 적용: 주제={d_topic} / 키워드={d_keyword} / 분야={d_field} / 사용처={d_usecase_mode} / 분량={d_spacing_type} {d_target_len}자 내외")
        with d_col1:
            d_content_type = st.selectbox("원고 유형", CONTENT_TYPES, index=4, key="d_content_type")
            st.caption(f"원고 사용처: {d_usecase_mode} / {usecase_summary_line(d_usecase_mode)}")
            d_prompt_mode = st.selectbox("프롬프트 출력 방식", ["달로썸 GPTs용", "외부 GPTs용 강제 프롬프트"], index=0, key="d_prompt_mode")
            st.caption("네가 만든/달로썸 GPTs에는 기본값, 남의 GPTs에는 외부 GPTs용 강제 프롬프트를 사용하세요.")
        with d_col2:
            d_extra_rules = st.text_area("초안 작성 추가 조건", placeholder="예: 추가 금지어, 클라이언트 요청사항, 특정 문체", height=100, key="d_extra_rules")
    else:
        with d_col1:
            d_topic = st.text_input("주제", value="써마지 시술", key="d_topic")
            d_keyword = st.text_input("핵심 키워드", value="써마지", key="d_keyword")
            d_field = st.selectbox("분야", RESEARCH_FIELDS, index=0, key="d_field")
            d_usecase_mode = st.selectbox("원고 사용처", USECASE_MODES, index=0, key="d_usecase_mode")
            st.caption(usecase_summary_line(d_usecase_mode))
        with d_col2:
            d_content_type = st.selectbox("원고 유형", CONTENT_TYPES, index=4, key="d_content_type")
            st.caption(f"원고 사용처: {d_usecase_mode} / {usecase_summary_line(d_usecase_mode)}")
            d_prompt_mode = st.selectbox("프롬프트 출력 방식", ["달로썸 GPTs용", "외부 GPTs용 강제 프롬프트"], index=0, key="d_prompt_mode")
            st.caption("네가 만든/달로썸 GPTs에는 기본값, 남의 GPTs에는 외부 GPTs용 강제 프롬프트를 사용하세요.")
            length_col1, length_col2 = st.columns(2)
            with length_col1:
                d_length_preset = st.selectbox("희망 분량", LENGTH_PRESETS, index=1, key="d_length_preset")
                d_spacing_type = st.selectbox("분량 기준", SPACING_TYPES, index=0, key="d_spacing_type")
            with length_col2:
                if d_length_preset == "직접 입력":
                    d_custom_length = st.number_input("직접 입력 글자수", min_value=500, max_value=6000, value=1500, step=100, key="d_custom_length")
                else:
                    d_custom_length = int(re.sub(r"[^0-9]", "", d_length_preset) or 1500)
                    st.caption("직접 입력 글자수는 ‘희망 분량’을 ‘직접 입력’으로 선택할 때만 표시됩니다.")
                d_paragraph_option = st.selectbox("문단 설정", PARAGRAPH_OPTIONS, index=0, key="d_paragraph_option")
            d_target_len = resolve_target_length(d_length_preset, d_custom_length)
            st.caption(f"적용될 분량 조건: {d_spacing_type} {d_target_len}자 내외 / {d_paragraph_option}")
            d_kw_settings = render_keyword_delivery_settings("design", d_keyword, d_target_len, expanded=False)
            d_extra_rules = st.text_area("초안 작성 추가 조건", placeholder="예: 제목에 키워드 1회, 본문 키워드 5회, 의료광고 위험표현 금지", height=100, key="d_extra_rules")

    st.divider()
    st.subheader("홈페이지 정보 반영")
    d_homepage_mode = st.radio("홈페이지/업체 정보", ["홈페이지 정보 없음", "홈페이지 정보 있음"], index=0, key="d_homepage_mode")
    d_homepage_info = st.text_area("홈페이지에서 확인한 원장/대표 소개·철학·장점", placeholder="예: 원장 약력, 진료 철학, 정품 장비, 상담 방식, 사후관리, 접근성 등 실제 홈페이지에서 확인한 내용만 붙여넣기", height=100, key="d_homepage_info")
    st.caption("입력한 정보 안에서만 마무리에 반영합니다. 없는 경력·장점·철학은 만들지 않게 합니다.")

    research_text = st.text_area("GPT 조사 결과 붙여넣기", height=360, placeholder="①에서 만든 조사 프롬프트를 GPT에 붙여넣고, GPT가 정리해준 조사 결과를 여기에 붙여넣으세요. 주제·키워드·분량은 다시 안 써도 됩니다.", key="research_text")

    counts, a_lines, b_lines, c_lines = analyze_research_text(research_text)
    st.write("### 화법 선택")
    recommended_voice = recommend_voice_type(d_field, d_topic, d_keyword, research_text)
    d_voice_choice = st.selectbox("메인 화법 선택", VOICE_TYPE_OPTIONS, index=0, key="d_voice")
    d_voice = recommended_voice if d_voice_choice == "자동 추천" else d_voice_choice
    st.caption(f"자동 추천 화법: {recommended_voice} / 최종 적용 화법: {d_voice}")
    st.session_state["applied_voice_type"] = d_voice

    recommended_title = recommend_title_style(d_field, d_topic, d_keyword, research_text)
    d_title_choice = st.selectbox("제목 유형 선택", TITLE_TYPE_OPTIONS, index=TITLE_TYPE_OPTIONS.index("자동 추천"), key="d_title_type_choice")
    d_title_type = recommended_title if d_title_choice == "자동 추천" else d_title_choice
    st.caption(f"자동 추천 제목 유형: {recommended_title} / 최종 적용 제목 유형: {d_title_type}")
    st.session_state["applied_title_type"] = d_title_type

    recommended_intro = recommend_intro_style(d_field, d_topic, d_keyword, research_text, d_voice)
    d_intro_choice = st.selectbox("달로썸 도입 8가지 방식 선택", INTRO_TYPE_OPTIONS, index=0, key="d_intro_type_choice")
    d_intro_type = recommended_intro if d_intro_choice == "자동 추천" else d_intro_choice
    st.caption(f"자동 추천 도입 방식: {recommended_intro} / 최종 적용 도입 방식: {d_intro_type}")
    st.session_state["applied_intro_type"] = d_intro_type

    d_first_sentence_type = st.selectbox("도입 첫문장 형태 선택", FIRST_SENTENCE_TYPES, index=0, key="d_first_sentence_type")
    st.caption("초안을 의문문으로 시작시키고 싶으면 여기서 '의문문 강제'를 선택하세요. 화법과 별도로 적용됩니다.")
    st.session_state["applied_first_sentence_type"] = d_first_sentence_type
    st.session_state["applied_topic"] = d_topic
    st.session_state["applied_keyword"] = d_keyword
    st.session_state["applied_field"] = d_field
    st.session_state["applied_content_type"] = d_content_type
    st.session_state["applied_usecase_mode"] = d_usecase_mode
    st.session_state["applied_target_len"] = d_target_len
    st.session_state["applied_spacing_type"] = d_spacing_type
    st.session_state["applied_homepage_mode"] = d_homepage_mode
    st.session_state["applied_homepage_info"] = d_homepage_info
    st.session_state["applied_keyword_settings"] = d_kw_settings

    d_keyword_delivery_text = keyword_delivery_setting_text(d_keyword, d_target_len, d_kw_settings)
    d_keyword_placement_text = keyword_placement_plan_text(d_keyword, d_target_len, d_kw_settings)
    st.write("### 키워드 배치 지도")
    st.text_area("초안 작성에 적용할 키워드 위치/횟수 기준", value=d_keyword_delivery_text + "\n\n" + d_keyword_placement_text, height=300)

    st.write("### 제목 후보")
    title_candidates = generate_title_candidates(d_keyword, d_topic, d_title_type, b_lines, d_field)
    for cand in title_candidates:
        length_note = "✅ 30자 이내" if len(cand) <= 30 else f"⚠️ {len(cand)}자"
        st.info(f"{cand}  ·  {length_note}")

    st.write("### 자료 등급 카운트")
    st.table(pd.DataFrame([{"구분": k, "감지 수": v} for k, v in counts.items()]))

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.write("### A등급 공통 핵심정보 후보")
        if a_lines:
            for x in a_lines:
                st.info(x)
        else:
            st.warning("A등급 공통정보 후보가 약합니다. GPT 조사 결과의 [2] A등급 공통 핵심정보 섹션을 붙여넣어 주세요.")
    with cc2:
        st.write("### B등급 고민패턴 후보")
        if b_lines:
            for x in b_lines:
                st.warning(x)
        else:
            st.warning("B등급 고민패턴 후보가 약합니다. 실제 질문/댓글/상담글 요약을 더 넣어주세요.")
    with cc3:
        st.write("### C등급 말맛 참고 후보")
        if c_lines:
            for x in c_lines:
                st.success(x)
        else:
            st.info("C등급 말맛 참고는 없어도 됩니다. 단, 후기형 원고라면 있으면 좋습니다.")

    st.write("## 전 분야 감정 흐름 설계")
    emotion_flow_plan = build_emotion_flow_plan(d_topic, d_keyword, d_voice, b_lines, d_field)
    st.text_area("도입 첫문장 후보 / 본문 브릿지 / 마무리 재연결", value=emotion_flow_plan, height=420)

    st.write("## 문단별 고민 배치안")
    bridge_plan = build_emotion_bridge_plan(d_topic, d_keyword, d_voice, b_lines)
    st.text_area("감정이 죽지 않도록 본문 전환부에 넣을 고민 배치", value=bridge_plan, height=360)

    st.write("## 홈페이지 정보 정리 / 마무리 반영")
    if d_homepage_mode == "홈페이지 정보 있음" and d_homepage_info.strip():
        homepage_guide = homepage_summary_guide(d_homepage_info)
        st.text_area("원장/대표 소개·철학·장점 정리 후보", value=homepage_guide, height=300)
    elif d_homepage_mode == "홈페이지 정보 있음":
        st.warning("홈페이지 정보 있음으로 선택했지만 입력 내용이 없습니다. 이 상태에서는 마무리 홍보 문구를 만들지 않습니다.")
    else:
        st.info("홈페이지 정보 없음: 마무리에서 본원/저희/철학/장점 문구를 임의 생성하지 않습니다.")

    draft_prompt = build_draft_prompt(d_topic, d_keyword, d_field, d_content_type, d_voice, d_intro_type, d_title_type, a_lines, b_lines, c_lines, d_extra_rules, d_target_len, d_spacing_type, d_paragraph_option, d_prompt_mode, d_first_sentence_type, d_homepage_mode, d_homepage_info, d_keyword_delivery_text, d_keyword_placement_text, d_usecase_mode)
    claude_prompt_empty = build_claude_prompt(d_voice, d_intro_type, d_title_type, d_keyword, d_field, first_sentence_type=d_first_sentence_type, homepage_mode=d_homepage_mode, homepage_info=d_homepage_info, usecase_mode=d_usecase_mode)

    st.write("## GPTs용 초안 프롬프트")
    st.text_area(
        "GPTs에 복붙",
        value=draft_prompt,
        height=520,
        key=dynamic_widget_key("draft_prompt_live", d_topic, d_keyword, d_field, d_usecase_mode, d_voice, d_intro_type, d_first_sentence_type, d_title_type, d_target_len, research_text)
    )
    st.download_button("GPTs용 초안 프롬프트 txt 다운로드", draft_prompt, file_name="dalrosom_draft_prompt.txt", key=dynamic_widget_key("draft_download", draft_prompt))

    st.write("## Claude용 윤문 지시문 기본형")
    st.caption("설계값이 바뀌면 이 칸도 자동으로 새 키로 갱신됩니다. 예전 화법명이나 사용처가 남으면 새로고침하지 말고 ②값을 한 번 다시 선택하세요.")
    st.text_area(
        "Claude에 보낼 때 원고와 함께 복붙",
        value=claude_prompt_empty,
        height=420,
        key=dynamic_widget_key("claude_design_live", d_voice, d_intro_type, d_title_type, d_keyword, d_field, d_first_sentence_type, d_homepage_mode, d_homepage_info, d_usecase_mode)
    )
    st.download_button("Claude용 지시문 txt 다운로드", claude_prompt_empty, file_name="dalrosom_claude_prompt.txt", key=dynamic_widget_key("claude_design_download", claude_prompt_empty))

with tab_check:
    st.title("📝 원고 검수 모드")
    st.caption("초안 작성 후 점수, 위험표현, 도입/마무리를 확인합니다. 필요할 때만 리라이트를 생성합니다.")

    with st.sidebar:
        st.header("원고 조건")
        use_flow_check = st.checkbox("①/② 입력값으로 검수 조건 자동 적용", value=True, key="check_use_flow")
        st.caption("켜두면 주제·분야·키워드·화법·도입방식·분량·키워드 기준을 다시 입력하지 않습니다.")

        if use_flow_check:
            purpose = "마케팅 회사 테스트 원고"
            field = st.session_state.get("applied_field", st.session_state.get("r_field", "병원 / 의료"))
            if field not in FIELDS:
                field = "기타 전문업종"
            writer_perspective = st.selectbox("작성자 관점", WRITER_PERSPECTIVES, index=0)
            keyword = st.session_state.get("applied_keyword", "") or st.session_state.get("r_keyword", "") or st.session_state.get("d_keyword", "") or "핵심 키워드"
            title_input = st.text_input("제목", placeholder="제목을 따로 넣거나, 본문 첫 줄에 넣어도 됩니다.")

            selected_title_type = st.session_state.get("applied_title_type", st.session_state.get("r_title_type", "선택 안함"))
            if selected_title_type == "자동 추천":
                selected_title_type = st.session_state.get("applied_title_type", "선택 안함")
            selected_intro_type = st.session_state.get("applied_intro_type", None)
            if not selected_intro_type or selected_intro_type == "자동 추천":
                selected_intro_type = st.session_state.get("r_intro_type", "5. 독자에게 질문 던지기")
                if selected_intro_type == "자동 추천":
                    selected_intro_type = "5. 독자에게 질문 던지기"
            selected_voice_type = st.session_state.get("applied_voice_type", st.session_state.get("r_voice_choice", "자동 추천"))
            selected_first_sentence_type = st.session_state.get("applied_first_sentence_type", st.session_state.get("r_first_sentence_type", "자동 추천"))
            selected_usecase_mode = st.session_state.get("applied_usecase_mode", st.session_state.get("r_usecase_mode", "블로그 정보성"))

            auto_b_source = "\n".join(b_lines) if 'b_lines' in globals() and b_lines else section_after(st.session_state.get("research_text", ""), ["B등급 잠재고객 고민패턴", "잠재고객 고민 요약", "감정 도입 첫문장 근거 고민"], ["C등급", "추천 제목", "[4]"], 1600)
            check_b_concern_text = st.text_area("B등급 고민 요약 / 첫문장 근거", value=auto_b_source, placeholder="조사 결과의 잠재고객 고민 요약이 자동으로 들어옵니다. 부족하면 보충하세요.", height=120)
            st.caption("첫문장이 실제 B등급 고민을 담았는지 검수합니다.")

            st.info(f"자동 적용: 분야={field} / 사용처={selected_usecase_mode} / 키워드={keyword} / 제목유형={selected_title_type} / 화법={selected_voice_type} / 도입방식={selected_intro_type} / 첫문장={selected_first_sentence_type}")

            ending_type = st.selectbox("현재 원고 마무리 방식", ENDING_TYPES, index=0)
            include_philosophy = st.checkbox("마지막 문단에 철학/강점 반영", value=False)
            philosophy_text = st.text_area("철학/강점 문구", value="", height=80, placeholder="홈페이지 정보가 있을 때만 입력")

            st.divider()
            st.subheader("검수 후 생성 옵션")
            generate_intro = st.checkbox("도입 리라이트 생성", value=False)
            rewrite_intro_type = st.selectbox("도입 리라이트 방식", INTRO_TYPES, index=INTRO_TYPES.index(selected_intro_type) if selected_intro_type in INTRO_TYPES else 5)
            generate_ending = st.checkbox("마무리 문단 생성", value=False)
            auto_homepage_mode = st.session_state.get("applied_homepage_mode", "홈페이지 정보 없음")
            homepage_mode = st.radio("마지막 문단 정보", ["홈페이지 정보 없음", "홈페이지 정보 있음"], index=0 if auto_homepage_mode == "홈페이지 정보 없음" else 1)
            homepage_info = st.text_area("홈페이지에서 가져온 철학/강점/특징", value=st.session_state.get("applied_homepage_info", "") if auto_homepage_mode == "홈페이지 정보 있음" else "", placeholder="실제 확인된 정보만 입력", height=90)

            st.divider()
            st.subheader("분량 검수")
            check_target_len = st.session_state.get("applied_target_len", d_target_len if 'd_target_len' in globals() else resolve_target_length(st.session_state.get("r_length_preset", "1500자"), st.session_state.get("r_custom_length", 1500)))
            st.caption(f"①/② 분량 기준 자동 적용: 공백 제외 기준 {check_target_len}자 내외")
            default_min = max(500, int(check_target_len * 0.85))
            default_max = int(check_target_len * 1.15)
            min_len = st.number_input("권장 최소 글자수(공백 제외)", min_value=500, max_value=6000, value=default_min, step=50)
            max_len = st.number_input("권장 최대 글자수(공백 제외)", min_value=600, max_value=7000, value=default_max, step=50)
            check_kw_settings = st.session_state.get("applied_keyword_settings", d_kw_settings if 'd_kw_settings' in globals() else auto_keyword_defaults(check_target_len))
            st.caption("키워드 납품 기준도 ①/② 설정값을 자동 적용합니다. 수정이 필요하면 위 체크를 끄고 수동 검수하세요.")
        else:
            purpose = st.selectbox("원고 목적", PURPOSES, index=0)
            field = st.selectbox("분야", FIELDS, index=0)
            writer_perspective = st.selectbox("작성자 관점", WRITER_PERSPECTIVES, index=0)
            keyword = st.text_input("키워드", value="복합성 피부 좋아지는 방법")
            title_input = st.text_input("제목", placeholder="제목을 따로 넣거나, 본문 첫 줄에 넣어도 됩니다.")
            selected_title_type = st.selectbox("현재 제목 유형", TITLE_TYPE_OPTIONS, index=0)
            selected_intro_type = st.selectbox("현재 원고 도입 방식", INTRO_TYPES, index=5)
            selected_voice_type = st.selectbox("현재 원고 화법", VOICE_TYPE_OPTIONS, index=0, key="check_voice_type_manual")
            selected_first_sentence_type = st.selectbox("현재 원고 첫문장 형태", FIRST_SENTENCE_TYPES, index=0, key="check_first_sentence_type_manual")
            selected_usecase_mode = st.selectbox("현재 원고 사용처", USECASE_MODES, index=0, key="check_usecase_mode_manual")
            st.caption(usecase_summary_line(selected_usecase_mode))
            check_b_concern_text = st.text_area("B등급 고민 요약 / 첫문장 근거", placeholder="조사 결과의 잠재고객 고민 요약, 감정 도입 근거 고민, B등급 고민패턴을 붙여넣으세요.", height=120)
            st.caption("첫문장이 실제 B등급 고민을 담았는지 검수합니다.")
            ending_type = st.selectbox("현재 원고 마무리 방식", ENDING_TYPES, index=0)
            include_philosophy = st.checkbox("마지막 문단에 철학/강점 반영", value=True)
            philosophy_text = st.text_area("철학/강점 문구", value=default_philosophy_by_field(field, writer_perspective), height=90)
            st.divider()
            st.subheader("검수 후 생성 옵션")
            generate_intro = st.checkbox("도입 리라이트 생성", value=False)
            rewrite_intro_type = st.selectbox("도입 리라이트 방식", INTRO_TYPES, index=5)
            generate_ending = st.checkbox("마무리 문단 생성", value=False)
            homepage_mode = st.radio("마지막 문단 정보", ["홈페이지 정보 없음", "홈페이지 정보 있음"], index=0)
            homepage_info = st.text_area("홈페이지에서 가져온 철학/강점/특징", placeholder="실제 확인된 정보만 입력", height=90)
            st.divider()
            st.subheader("분량 검수")
            check_length_preset = st.selectbox("검수 분량 기준", LENGTH_PRESETS, index=1, key="check_length_preset")
            if check_length_preset == "직접 입력":
                check_custom_length = st.number_input("직접 입력 검수 글자수", min_value=500, max_value=6000, value=1500, step=100, key="check_custom_length")
            else:
                check_custom_length = int(re.sub(r"[^0-9]", "", check_length_preset) or 1500)
                st.caption("직접 입력 글자수는 ‘검수 분량 기준’을 ‘직접 입력’으로 선택할 때만 표시됩니다.")
            check_target_len = resolve_target_length(check_length_preset, check_custom_length)
            default_min = max(500, int(check_target_len * 0.85))
            default_max = int(check_target_len * 1.15)
            min_len = st.number_input("권장 최소 글자수(공백 제외)", min_value=500, max_value=6000, value=default_min, step=50)
            max_len = st.number_input("권장 최대 글자수(공백 제외)", min_value=600, max_value=7000, value=default_max, step=50)
            check_kw_settings = render_keyword_delivery_settings("check", keyword, check_target_len, expanded=False)
    draft = st.text_area("검수할 원고를 붙여넣으세요", height=520, placeholder="제목 포함 원고를 그대로 붙여넣어도 됩니다.")

    if st.button("검수 시작", type="primary"):
        title, body, title_source = extract_title(title_input, draft)
        if not body:
            st.error("본문이 비어 있습니다.")
            st.stop()

        scores, issues, total, cap_reasons, meta = check_all(
            title, body, keyword, field, purpose, writer_perspective,
            selected_intro_type, selected_title_type, ending_type, include_philosophy, philosophy_text,
            min_len, max_len, selected_first_sentence_type, check_b_concern_text
        )

        st.write("## 추출 결과")
        c1, c2, c3 = st.columns(3)
        c1.metric("제목 인식", "성공" if title else "실패")
        c2.metric("제목 출처", title_source)
        c3.metric("제목 글자수", len(title) if title else 0)
        st.info(f"인식된 제목: {title if title else '없음'}")
        first_sentence_preview = extract_first_content_sentence(body)
        if first_sentence_preview:
            st.caption(f"감지된 실제 첫문장: {first_sentence_preview}")
            if check_b_concern_text.strip():
                fg = evaluate_first_sentence_grounding(first_sentence_preview, check_b_concern_text, keyword)
                if fg["status"] == "ok":
                    st.success(fg["message"])
                elif fg["status"] == "weak":
                    st.warning(fg["message"])
                elif fg["status"] == "missing":
                    st.error(fg["message"])

        kw_report, kw_insert_prompt = keyword_placement_report(title, body, keyword, check_kw_settings)
        st.write("## 키워드 배치 검수")
        st.markdown(kw_report)
        if kw_insert_prompt:
            st.text_area("누락 문단 키워드 삽입 요청문", value=kw_insert_prompt, height=360)
            st.download_button("키워드 삽입 요청문 txt 다운로드", kw_insert_prompt, file_name="dalrosom_keyword_insert_prompt.txt")

        if homepage_mode == "홈페이지 정보 있음" and homepage_info.strip():
            philosophy_source_label = "홈페이지 확인 정보 반영"
        elif include_philosophy and philosophy_text.strip() and ending_type != "철학 없이 정보 마무리":
            philosophy_source_label = "사용자 입력 철학 반영"
        elif include_philosophy and philosophy_text.strip() and ending_type == "철학 없이 정보 마무리":
            philosophy_source_label = "철학 문구 입력됨 / 현재 마무리 방식은 정보형"
        else:
            philosophy_source_label = "철학 미반영"
        st.caption(f"선택한 현재 제목 유형: {selected_title_type} / 화법: {selected_voice_type} / 첫문장 형태: {selected_first_sentence_type} / 도입 방식: {selected_intro_type} / 마무리 방식: {ending_type} / 철학 상태: {philosophy_source_label}")

        st.write("## 점수")
        st.metric("총점", f"{total}점", price_estimate(total))
        if cap_reasons:
            with st.expander("점수 상한 적용 이유"):
                for r in cap_reasons:
                    st.warning(r)

        st.table(pd.DataFrame([
            {"항목": "제목", "점수": f"{scores['제목']}/15"},
            {"항목": "본문 SEO/길이/키워드", "점수": f"{scores['본문']}/20"},
            {"항목": "도입부", "점수": f"{scores['도입']}/15"},
            {"항목": "AI티", "점수": f"{scores['AI티']}/15"},
            {"항목": "복사찌꺼기", "점수": f"{scores['복사찌꺼기']}/10"},
            {"항목": "위험표현", "점수": f"{scores['위험표현']}/15"},
            {"항목": "작성자 관점", "점수": f"{scores['작성자 관점']}/10"},
            {"항목": "마무리", "점수": f"{scores['마무리']}/10"},
        ]))

        st.write("## 핵심 수치")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("공백 제외 글자수", meta["no_space_len"])
        m2.metric("키워드 횟수", f"본문 {meta['body_kw']} / 제목포함 {meta['total_kw']}")
        m3.metric("소제목 수", meta["subheads"])
        m4.metric("감지 제목", ", ".join(meta["detected_title"]) if meta["detected_title"] else "없음")
        m5.metric("감지 도입", ", ".join(meta["detected_intro"]) if meta["detected_intro"] else "없음")

        for section in ["제목", "본문", "도입", "AI티", "복사찌꺼기", "위험표현", "작성자 관점", "마무리"]:
            show_issues(f"{section} 검수", issues[section])

        st.write("### 용어 설명 제안")
        glossary_terms = glossary_check(body, field)
        if glossary_terms:
            st.info("본문에 나오지만 초보 독자에게 설명이 있으면 좋은 용어: " + ", ".join(glossary_terms))
        else:
            st.success("용어 설명 제안 없음")

        st.write("## 검수 후 리라이트 생성")

        if not generate_intro and not generate_ending:
            st.success("현재는 리라이트 생성이 꺼져 있습니다. 점수와 검수 결과만 확인하면 됩니다.")
            if total >= 92 and not issues["도입"] and not issues["마무리"]:
                st.info("현재 도입과 마무리는 유지해도 괜찮습니다. 굳이 새 문단으로 바꿀 필요는 없습니다.")

        if generate_intro:
            st.write("### 선택한 방식으로 도입 다시 쓰기")
            rewritten_intro = generate_intro_rewrite(rewrite_intro_type, keyword, title, field, writer_perspective)
            st.text_area("생성된 도입 문단", value=rewritten_intro, height=260)
        else:
            st.caption("도입 리라이트가 필요하면 왼쪽에서 '도입 리라이트 생성'을 켜세요.")

        if generate_ending:
            st.write("### 마지막 문단 생성")
            final_paragraph = generate_final_paragraph(keyword, field, writer_perspective, homepage_mode, homepage_info, philosophy_text if include_philosophy else "")
            st.text_area("생성된 마무리 문단", value=final_paragraph, height=240)
        else:
            st.caption("마무리 문단 생성이 필요하면 왼쪽에서 '마무리 문단 생성'을 켜세요.")

        if generate_intro and rewrite_intro_type == "8. 간단한 웹툰 만들어 넣기":
            st.caption("웹툰형은 실제 이미지를 만들지 않고 컷 구성안만 제공합니다. 실제 웹툰 이미지는 별도 이미지 제작 도구에서 만드는 방식이 안전합니다.")

        st.write("## Claude용 윤문 지시문 · 현재 검수값 자동 갱신")
        current_body_for_claude = f"최종 제목: {title}\n\n본문:\n{body}".strip()
        claude_prompt_current = build_claude_prompt(
            selected_voice_type,
            selected_intro_type,
            selected_title_type,
            keyword,
            field,
            body_text=current_body_for_claude,
            first_sentence_type=selected_first_sentence_type,
            homepage_mode=homepage_mode,
            homepage_info=homepage_info,
            usecase_mode=selected_usecase_mode
        )
        st.caption("검수 화면의 최신 사용처·화법·도입방식·키워드 기준으로 매번 새로 생성됩니다. Claude에는 이 칸을 복붙하세요.")
        st.text_area(
            "Claude에 바로 복붙",
            value=claude_prompt_current,
            height=520,
            key=dynamic_widget_key("claude_check_live", selected_usecase_mode, selected_voice_type, selected_intro_type, selected_first_sentence_type, selected_title_type, keyword, field, homepage_mode, homepage_info, title, body[:500])
        )
        st.download_button("현재 검수값 Claude 지시문 txt 다운로드", claude_prompt_current, file_name="dalrosom_claude_prompt_current.txt", key=dynamic_widget_key("claude_check_download", claude_prompt_current))

        st.write("## 제출 판단")
        if total >= 92:
            st.success("제출 가능권입니다. 오탈자와 줄바꿈만 확인하세요.")
        elif total >= 88:
            st.info("실무 가능권입니다. 제출은 가능하지만 도입 방식/마무리 철학 중 하나는 보완하는 편이 좋습니다.")
        elif total >= 82:
            st.warning("부분 보완 필요입니다. 재작성까지는 아니고 길이/키워드/도입만 손보세요.")
        else:
            st.error("재작성 권장입니다. 구조부터 다시 잡는 편이 빠릅니다.")
    else:
        st.info("왼쪽 조건을 입력하고 원고를 붙여넣은 뒤 검수 시작을 누르세요.")
