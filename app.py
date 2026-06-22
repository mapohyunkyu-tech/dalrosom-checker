import streamlit as st

from modules.constants import PURPOSES, FIELDS
from modules.utils import clean_text, count_keyword, highlight_text
from modules.checkers import (
    check_title,
    check_intro,
    check_body_seo,
    check_ai_smell,
    check_compliance,
    check_glossary,
    check_ending,
)
from modules.scoring import estimate_price, final_judgement, recommend_intro_type


st.set_page_config(
    page_title="달로썸 테스트 원고 검수기",
    page_icon="📝",
    layout="wide",
)

st.title("📝 달로썸 테스트 원고 검수기 v1")
st.caption("GPTs 초안을 붙여넣으면 제목, 도입, SEO, AI티, 위험표현, 마무리, 점수와 예상 단가를 검수합니다.")

with st.sidebar:
    st.header("기본 설정")
    purpose = st.radio("원고 목적", PURPOSES, index=1)
    field = st.radio("분야", FIELDS, index=0)

    keyword = st.text_input("키워드", placeholder="예: 복합성 피부 좋아지는 방법")
    title = st.text_input("제목", placeholder="예: 복합성 피부 좋아지는 방법 5가지 관리 기준")
    target = st.text_input("타깃 독자", placeholder="예: 유분과 속건조가 동시에 고민인 20~40대 여성")
    tone = st.text_input("원고 톤", placeholder="예: 에스테틱 원장이 설명하는 친절한 전문 톤")

st.subheader("1. GPTs 초안 붙여넣기")
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
    st.subheader("2. 최종 점수")

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
    st.subheader("3. 하이라이트 원고")

    highlight_phrases = ai_phrases + risk_phrases
    highlighted = highlight_text(draft, highlight_phrases)
    st.markdown(
        f"<div style='line-height:1.9; font-size:16px; white-space:pre-wrap;'>{highlighted}</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("4. 검수 결과")

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
    st.subheader("5. 도입부 추천")

    for name, effect in recommend_intro_type(field):
        st.info(f"**{name}**\n\n효과: {effect}")

    st.divider()
    st.subheader("6. 어려운 용어 코너 추천")

    if glossary_suggestions:
        for term in glossary_suggestions:
            st.write(f"✅ **여기서 잠깐! {term}란?** 코너 추가 추천")
            st.caption("효과: 독자가 낯선 용어를 이해하기 쉬워지고, 원고가 더 친절하고 정성스러워 보입니다.")
    else:
        st.success("현재 감지된 어려운 용어 코너 추천은 없습니다.")

    st.divider()
    st.subheader("7. 최종 납품 전 체크리스트")

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
    st.subheader("8. 판정")

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
        st.write(f"타깃: {target}")
        st.write(f"톤: {tone}")
else:
    st.info("왼쪽에서 목적, 분야, 키워드, 제목을 입력하고 GPTs 초안을 붙여넣은 뒤 검수 시작을 누르세요.")
