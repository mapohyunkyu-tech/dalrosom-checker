from pathlib import Path
import re
p = Path('/mnt/data/v1014_work/app.py')
s = p.read_text(encoding='utf-8')

s = s.replace('st.set_page_config(page_title="달로썸 원고 검수기 v10.0.13", layout="wide")',
              'st.set_page_config(page_title="달로썸 원고 검수기 v10.0.14", layout="wide")')

insert_after = 'BRAND_INTENSITY_OPTIONS = ["업체명 없음", "본문 1회만", "본문 2~3회 자연 반영", "제목 포함"]\n'
insert = r'''

# =========================
# v10.0.14: 원고 글결 조종판
# =========================
WRITING_GYEOL_OPTIONS = [
    "자동 추천",
    "기본 정보성",
    "증상 공감형",
    "선택 기준형",
    "문제 해결형",
    "오해 반박형",
    "대표자 주장형",
    "병원/업체 선택 기준형",
    "수술·시술·상담 전 체크형",
    "장비보다 해석/판단 강조형",
    "치료·해결 방법 설명형",
    "병원/업체 시스템 연결형",
    "책임 진료/책임 작업 강조형",
    "브랜드 철학형",
    "과정 설명형",
    "비용·가격 기준형",
    "사례·케이스 해설형",
    "비교형",
    "후기/기자단형",
    "카페 자연 정보형",
    "홈피드 이슈형",
]
WRITING_GYEOL_SECONDARY_OPTIONS = ["선택 안함"] + [x for x in WRITING_GYEOL_OPTIONS if x != "자동 추천"]

WRITING_GYEOL_ALIASES = {
    "": "자동 추천",
    "없음": "자동 추천",
    "달로썸형": "증상 공감형",
    "달로썸 기존형": "증상 공감형",
    "원장 칼럼형": "대표자 주장형",
    "대표원장 주장형": "대표자 주장형",
    "대표원장 신뢰형": "대표자 주장형",
    "대표변호사 칼럼형": "대표자 주장형",
    "병원 선택 기준형": "병원/업체 선택 기준형",
    "업체 선택 기준형": "병원/업체 선택 기준형",
    "수술 전 체크리스트형": "수술·시술·상담 전 체크형",
    "시술 전 체크리스트형": "수술·시술·상담 전 체크형",
    "상담 전 체크형": "수술·시술·상담 전 체크형",
    "장비/시스템 전문성형": "장비보다 해석/판단 강조형",
    "책임 진료 강조형": "책임 진료/책임 작업 강조형",
}

def normalize_writing_gyeol(gyeol=""):
    gyeol = (gyeol or "").strip()
    gyeol = WRITING_GYEOL_ALIASES.get(gyeol, gyeol)
    return gyeol if gyeol in WRITING_GYEOL_OPTIONS or gyeol in WRITING_GYEOL_SECONDARY_OPTIONS else "자동 추천"

def auto_recommend_writing_gyeol(field="", article_style="", topic="", keyword=""):
    field = field or ""
    style = normalize_article_style(article_style or "정보성") if 'normalize_article_style' in globals() else (article_style or "정보성")
    text = f"{topic} {keyword} {field} {style}"
    if style == "홈피드 이슈형" or "홈피드" in field:
        return "홈피드 이슈형"
    if style == "후기/기자단형":
        return "후기/기자단형"
    if style == "카페 자연글형":
        return "카페 자연 정보형"
    if any(w in text for w in ["비용", "가격", "견적", "단가"]):
        return "비용·가격 기준형"
    if any(w in text for w in ["차이", "비교", "라식 라섹", "라식·라섹", "수술 비수술"]):
        return "비교형"
    if any(w in text for w in ["전 확인", "전 체크", "시술 전", "수술 전", "상담 전", "검사 전", "방문 전"]):
        return "수술·시술·상담 전 체크형"
    if any(w in text for w in ["장비", "검사", "정밀", "시스템", "해석", "판단"]):
        return "장비보다 해석/판단 강조형" if "병원" in field or "의료" in field else "과정 설명형"
    if any(w in text for w in ["왜", "무조건", "같을까요", "좋을까요", "오해", "아닌 이유"]):
        return "오해 반박형"
    if any(w in text for w in ["고르는", "선택", "기준", "확인할 점", "찾을 때"]):
        return "병원/업체 선택 기준형" if any(x in field for x in ["병원", "의료", "법률"]) else "선택 기준형"
    if any(w in text for w in ["통증", "증상", "아픈", "불편", "냄새", "얼룩", "누수", "문제"]):
        return "증상 공감형" if any(x in field for x in ["병원", "의료"]) else "문제 해결형"
    if style == "매출 전환형":
        return "선택 기준형"
    return "기본 정보성"

def resolve_primary_gyeol(primary_gyeol="", field="", article_style="", topic="", keyword=""):
    g = normalize_writing_gyeol(primary_gyeol)
    if g in ["", "자동 추천", "선택 안함"]:
        return auto_recommend_writing_gyeol(field, article_style, topic, keyword)
    return g

def clean_secondary_gyeols(g1="", g2=""):
    arr = []
    for g in [g1, g2]:
        ng = normalize_writing_gyeol(g)
        if ng and ng not in ["자동 추천", "선택 안함"] and ng not in arr:
            arr.append(ng)
    return arr[:2]

def writing_gyeol_goal_clause(primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style="", topic="", keyword=""):
    primary = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)
    seconds = clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)
    if primary == "기본 정보성" and not seconds:
        return ""
    names = " + ".join([primary] + seconds)
    clauses = {
        "증상 공감형": "독자의 증상·불편·망설임을 먼저 짚고 원인과 확인 기준으로 연결하는 흐름",
        "선택 기준형": "독자가 비교·선택 전에 확인할 기준을 3~5개로 정리하는 흐름",
        "문제 해결형": "문제 원인과 해결 방향을 단계적으로 설명하는 흐름",
        "오해 반박형": "흔한 오해를 먼저 제시한 뒤 왜 다르게 봐야 하는지 반박하는 흐름",
        "대표자 주장형": "대표원장·변호사·대표의 관점과 판단 기준이 드러나는 칼럼형 흐름",
        "병원/업체 선택 기준형": "광고성 장점 나열보다 독자가 병원·업체를 고를 때 봐야 할 기준을 알려주는 흐름",
        "수술·시술·상담 전 체크형": "상담·검사·수술·시술 전 확인해야 할 항목을 중심으로 정리하는 흐름",
        "장비보다 해석/판단 강조형": "장비나 방법 자체보다 결과를 해석하고 판단하는 기준의 중요성을 설명하는 흐름",
        "치료·해결 방법 설명형": "초기 관리부터 치료·해결 방법까지 선택지를 차분히 설명하는 흐름",
        "병원/업체 시스템 연결형": "정보 설명 뒤 확인된 병원·업체의 시스템과 상담 기준을 주제와 연결하는 흐름",
        "책임 진료/책임 작업 강조형": "누가 상담·진료·작업을 책임지고 판단하는지 신뢰 기준을 강조하는 흐름",
        "브랜드 철학형": "대표 철학과 운영 기준을 주제 해결과 연결하는 흐름",
        "과정 설명형": "상담·검사·시술·작업·수업 과정을 순서대로 설명하는 흐름",
        "비용·가격 기준형": "비용 차이와 견적 기준, 추가 비용 발생 요인을 설명하는 흐름",
        "사례·케이스 해설형": "사례·판례·케이스를 통해 쟁점과 판단 기준을 설명하는 흐름",
        "비교형": "두 가지 이상 선택지를 비교하고 내 상황에 맞는 판단 기준으로 연결하는 흐름",
        "후기/기자단형": "사진자료나 제공 정보를 바탕으로 자연스럽게 소개하되 가짜 경험담을 피하는 흐름",
        "카페 자연 정보형": "카페 회원이 정보를 공유하듯 부담 없는 말투로 정리하는 흐름",
        "홈피드 이슈형": "검색 설명보다 공감·반응·이슈 포인트를 중심으로 풀어내는 흐름",
    }
    desc = clauses.get(primary, "선택한 글결에 맞춰 문단 흐름을 조절하는 방식")
    if seconds:
        desc += "에 보조 글결 " + ", ".join(seconds) + "을 자연스럽게 섞는다"
    return f" 글결은 ‘{names}’으로 잡고, {desc}."

def writing_gyeol_prompt_block(primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style="", topic="", keyword=""):
    primary = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)
    seconds = clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)
    names = " / ".join([primary] + seconds) if seconds else primary
    flow_map = {
        "기본 정보성": ["독자 검색 의도 제시", "핵심 개념 설명", "확인 기준", "주의사항", "정리"],
        "증상 공감형": ["증상·불편 공감", "단순히 넘기기 어려운 이유", "원인·진행 설명", "검사·치료·해결 기준", "병원/업체 시스템 또는 상담 유도"],
        "선택 기준형": ["선택이 어려운 상황", "잘못 보기 쉬운 기준", "확인 기준 3~5가지", "기준별 이유", "문의/상담 전 정리"],
        "문제 해결형": ["독자의 문제 상황", "원인 후보", "해결 방향", "전문가 확인이 필요한 지점", "상담/문의 유도"],
        "오해 반박형": ["흔한 오해 또는 질문", "왜 그대로 믿으면 안 되는지", "전문가 기준", "선택·상담 기준", "확인된 장점 연결"],
        "대표자 주장형": ["대표/전문가 관점 제시", "현장에서 자주 보는 문제", "판단 기준", "운영 철학·상담 기준", "문의 유도"],
        "병원/업체 선택 기준형": ["병원/업체 선택이 어려운 이유", "광고만 보고 고르기 어려운 기준", "진짜 확인할 기준 3~5가지", "확인된 장점을 기준과 연결", "상담/예약/문의 유도"],
        "수술·시술·상담 전 체크형": ["상담 전 불안·궁금증", "먼저 확인할 체크포인트", "검사·준비·주의사항", "결과에 따라 달라지는 선택", "상담 유도"],
        "장비보다 해석/판단 강조형": ["장비·방법만 보고 판단하기 쉬운 상황", "장비만으로 부족한 이유", "해석·세팅·판단 기준", "의료진/전문가 상담 기준", "확인된 시스템 연결"],
        "치료·해결 방법 설명형": ["문제/증상 공감", "초기 관리", "비수술/비작업 또는 기본 해결", "전문 치료·작업 선택지", "상담 유도"],
        "병원/업체 시스템 연결형": ["정보 설명", "왜 시스템이 필요한지", "검사·상담·작업 흐름", "확인된 장점 연결", "문의 유도"],
        "책임 진료/책임 작업 강조형": ["누가 판단하는지 중요한 이유", "책임 구조 확인 기준", "상담·진료·작업 과정", "신뢰 기준", "문의 유도"],
        "브랜드 철학형": ["독자 고민", "대표 철학", "그 철학이 주제 해결에 필요한 이유", "운영/상담 기준", "문의 유도"],
        "과정 설명형": ["진행 전 고민", "1단계", "2단계", "3단계", "마무리/주의사항"],
        "비용·가격 기준형": ["가격 차이가 나는 상황", "비용이 달라지는 기준", "추가비 확인", "싼 가격만 보면 안 되는 이유", "견적 문의"],
        "사례·케이스 해설형": ["사례 상황", "쟁점", "판단 기준", "비슷한 상황에서 확인할 점", "상담 유도"],
        "비교형": ["두 선택지 제시", "차이점", "장단점", "내 상황 기준", "상담/문의 유도"],
        "후기/기자단형": ["사진/자료 기준 소개", "분위기/특징", "이용 전 확인점", "가짜 경험 없이 정리", "방문/문의 유도"],
        "카페 자연 정보형": ["가벼운 문제 제기", "알아본 내용", "장단점", "주의사항", "부담 없는 정리"],
        "홈피드 이슈형": ["멈추게 하는 첫문장", "이슈 상황", "반응/공감", "왜 화제인지", "댓글/저장 포인트"],
    }
    flow = flow_map.get(primary, flow_map["기본 정보성"])
    extra = ""
    if seconds:
        extra = "\n- 보조 글결은 대표 글결을 흐리지 않는 선에서 문단 전환부와 마무리에만 자연스럽게 섞는다."
    return "\n".join([
        "[원고 글결 적용 지시]",
        f"- 대표 글결: {primary}",
        f"- 보조 글결: {', '.join(seconds) if seconds else '없음'}",
        f"- 최종 글결 조합: {names}",
        "- 글 성격은 큰 분류이고, 글결은 실제 본문 흐름이다. 단순 정보 나열로 쓰지 말고 아래 흐름을 우선한다.",
        "- 권장 흐름: " + " → ".join(flow),
        "- 병원·법률·금융 등 민감 업종은 글결이 강해도 결과 보장, 과장, 공포 조장은 피한다.",
        "- 매출 전환형이라도 장점 나열문으로 끝내지 말고, 선택 기준·판단 기준과 연결해 자연스럽게 마무리한다." + extra,
    ])

def inspect_writing_gyeol_alignment(body="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style="", topic="", keyword=""):
    primary = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)
    text = body or ""
    issues = []
    def has(words):
        return any(w in text for w in words)
    if primary == "오해 반박형":
        if not has(["무조건", "같을까요", "좋을까요", "오해", "착각", "그럴까요", "아닙니다", "다릅니다", "보다 먼저"]):
            issues.append("오해 반박형인데 흔한 오해를 제시하고 반박하는 문장이 약합니다.")
    elif primary == "병원/업체 선택 기준형":
        count = sum(text.count(w) for w in ["기준", "확인", "살펴", "피하", "고를", "선택", "봐야"])
        if count < 5:
            issues.append("병원/업체 선택 기준형인데 독자가 확인할 기준이 충분히 보이지 않습니다.")
    elif primary == "대표자 주장형":
        if not has(["중요하게", "생각합니다", "봅니다", "기준", "원칙", "철학", "상담에서", "현장에서"]):
            issues.append("대표자 주장형인데 대표/전문가의 판단 기준이나 철학 문장이 약합니다.")
    elif primary == "장비보다 해석/판단 강조형":
        if not has(["해석", "판단", "분석", "결과를", "상태를", "검사 결과", "세팅", "기준"]):
            issues.append("장비보다 해석/판단 강조형인데 장비 이후의 해석·판단 기준 설명이 약합니다.")
    elif primary == "증상 공감형":
        if not has(["아프", "통증", "불편", "반복", "답답", "걱정", "헷갈", "망설", "냄새", "얼룩", "문제"]):
            issues.append("증상 공감형인데 독자의 증상·불편·문제 상황을 짚는 문장이 약합니다.")
    elif primary == "수술·시술·상담 전 체크형":
        if not has(["전 확인", "먼저", "체크", "주의", "준비", "검사", "상담 전", "예약 전"]):
            issues.append("체크형인데 상담·검사·시술 전 확인해야 할 항목이 약합니다.")
    return {"primary": primary, "secondary": clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2), "issues": issues}
'''
if insert_after not in s:
    raise SystemExit('insert point not found')
s = s.replace(insert_after, insert_after + insert)

# Update function signatures and calls for content goal
s = s.replace('def auto_generate_content_goal(field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords=""):',
              'def auto_generate_content_goal(field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2=""):')
s = s.replace('    field = (field or "기타 전문업종").strip()\n    style = normalize_article_style(article_style or "정보성")',
              '    field = (field or "기타 전문업종").strip()\n    style = normalize_article_style(article_style or "정보성")')
# Add gyeol clause after brand_part line
s = s.replace('    brand_part = "병원/업체의 확인된 장점과 상담 기준" if brand_name else "확인된 서비스 기준과 선택 포인트"\n\n    field_templates = {',
              '    brand_part = "병원/업체의 확인된 장점과 상담 기준" if brand_name else "확인된 서비스 기준과 선택 포인트"\n    gyeol_clause = writing_gyeol_goal_clause(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, style, topic, keyword)\n\n    field_templates = {')
# Append gyeol_clause to returns in auto_generate_content_goal block roughly until effective_content_goal
old_returns = [
('return f"{topic_phrase}를 최근 이슈와 독자 반응 중심으로 풀어내고, 클릭·공감·저장 포인트가 살아나도록 구성하는 홈피드형 원고"', 'return f"{topic_phrase}를 최근 이슈와 독자 반응 중심으로 풀어내고, 클릭·공감·저장 포인트가 살아나도록 구성하는 홈피드형 원고{gyeol_clause}"'),
('return f"{topic_phrase}에 대해 {kw_phrase}를 가진 독자가 핵심 기준과 주의사항을 이해하도록 돕는 정보성 원고"', 'return f"{topic_phrase}에 대해 {kw_phrase}를 가진 독자가 핵심 기준과 주의사항을 이해하도록 돕는 정보성 원고{gyeol_clause}"'),
('return f"{topic_phrase}에서 독자가 비교·선택 전 확인해야 할 기준을 정리하고, 본인 상황에 맞는 판단을 돕는 선택 기준형 원고"', 'return f"{topic_phrase}에서 독자가 비교·선택 전 확인해야 할 기준을 정리하고, 본인 상황에 맞는 판단을 돕는 선택 기준형 원고{gyeol_clause}"'),
('return f"{topic_phrase}와 관련해 독자가 겪는 불편이나 고민을 먼저 짚고, 원인 확인과 해결 방향을 단계적으로 안내하는 문제 해결형 원고"', 'return f"{topic_phrase}와 관련해 독자가 겪는 불편이나 고민을 먼저 짚고, 원인 확인과 해결 방향을 단계적으로 안내하는 문제 해결형 원고{gyeol_clause}"'),
('return f"{topic_phrase}를 바탕으로 독자가 필요한 기준을 이해한 뒤, {brand_part}을 자료 범위 안에서 자연스럽게 소개하는 업체/서비스 소개형 원고"', 'return f"{topic_phrase}를 바탕으로 독자가 필요한 기준을 이해한 뒤, {brand_part}을 자료 범위 안에서 자연스럽게 소개하는 업체/서비스 소개형 원고{gyeol_clause}"'),
('return f"{topic_phrase}를 사진자료나 제공 정보 기준으로 자연스럽게 소개하되, 직접 경험한 척하지 않고 방문·이용 전 확인할 포인트를 정리하는 후기/기자단형 원고"', 'return f"{topic_phrase}를 사진자료나 제공 정보 기준으로 자연스럽게 소개하되, 직접 경험한 척하지 않고 방문·이용 전 확인할 포인트를 정리하는 후기/기자단형 원고{gyeol_clause}"'),
('return f"{topic_phrase}를 카페 회원이 정보 공유하듯 자연스럽게 정리하고, 장단점과 주의사항을 부담 없는 말투로 알려주는 원고"', 'return f"{topic_phrase}를 카페 회원이 정보 공유하듯 자연스럽게 정리하고, 장단점과 주의사항을 부담 없는 말투로 알려주는 원고{gyeol_clause}"'),
('return f"{topic_phrase}에 관심 있는 독자에게 핵심 기준과 주의사항을 설명하고, {brand_part}을 주제와 자연스럽게 연결해 {action}로 이어지게 하는 매출 전환형 원고. 단순 설명에서 끝내지 않고 독자의 고민 → 확인 기준 → 상담/문의 필요성 흐름으로 작성한다."', 'return f"{topic_phrase}에 관심 있는 독자에게 핵심 기준과 주의사항을 설명하고, {brand_part}을 주제와 자연스럽게 연결해 {action}로 이어지게 하는 매출 전환형 원고. 단순 설명에서 끝내지 않고 독자의 고민 → 확인 기준 → 상담/문의 필요성 흐름으로 작성한다{gyeol_clause}."')
]
for a,b in old_returns:
    s = s.replace(a,b)

s = s.replace('def effective_content_goal(content_goal="", field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords=""):',
              'def effective_content_goal(content_goal="", field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2=""):')
s = s.replace('return auto_generate_content_goal(field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)',
              'return auto_generate_content_goal(field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2)',1)
s = s.replace('def content_goal_force_block(content_goal="", field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords=""):',
              'def content_goal_force_block(content_goal="", field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2=""):')
s = s.replace('goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)',
              'goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2)',1)
s = s.replace('    lines = ["[원고 목적 자동 적용]", f"- 최종 적용 원고 목적: {goal}"]',
              '    resolved_gyeol = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)\n    lines = ["[원고 목적 자동 적용]", f"- 최종 적용 원고 목적: {goal}", f"- 적용 대표 글결: {resolved_gyeol}"]')

# build_research_prompt signature and internals
s = s.replace('homefeed_overseas_usage=""):', 'homefeed_overseas_usage="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2=""):',1)
s = s.replace('content_goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)',
              'content_goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2)',1)
s = s.replace('purpose_block = content_goal_force_block(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)',
              'purpose_block = content_goal_force_block(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2)',1)
s = s.replace('brand_block = brand_voice_block(article_style, sub_keywords, brand_name, conversion_goal, brand_intensity, tone_detail, writer_perspective, field, topic, keyword)',
              'brand_block = brand_voice_block(article_style, sub_keywords, brand_name, conversion_goal, brand_intensity, tone_detail, writer_perspective, field, topic, keyword)\n    gyeol_block = writing_gyeol_prompt_block(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword)',1)
s = s.replace('전환 목표: {conversion_goal if conversion_goal else "없음"}\n업체명 반영 강도: {brand_intensity}',
              '전환 목표: {conversion_goal if conversion_goal else "없음"}\n대표 글결: {resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)}\n보조 글결: {", ".join(clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)) if clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2) else "없음"}\n업체명 반영 강도: {brand_intensity}',1)
s = s.replace('{purpose_block}\n{brand_block}', '{purpose_block}\n{gyeol_block}\n{brand_block}',1)

# build_draft_prompt signature and internals
s = s.replace('homefeed_overseas_usage="", content_goal=""):', 'homefeed_overseas_usage="", content_goal="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2=""):',1)
s = s.replace('content_goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)',
              'content_goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2)',1)
s = s.replace('purpose_block = content_goal_force_block(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)',
              'purpose_block = content_goal_force_block(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2)',1)
s = s.replace('brand_block = brand_voice_block(article_style, sub_keywords, brand_name, conversion_goal, brand_intensity, tone_detail, writer_perspective, field, topic, keyword)',
              'brand_block = brand_voice_block(article_style, sub_keywords, brand_name, conversion_goal, brand_intensity, tone_detail, writer_perspective, field, topic, keyword)\n    gyeol_block = writing_gyeol_prompt_block(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword)',1)
# In draft prompt metadata replace first occurrence after def? It appears lower. Add if unique no issue maybe both research/draft? We did one. Need second occurrence of field header in draft. Use replace with count 1 after previous? Already one exact gone? We need inspect later maybe use generic replace next occurrence.
s = s.replace('전환 목표: {conversion_goal if conversion_goal else "없음"}\n업체명 반영 강도: {brand_intensity}',
              '전환 목표: {conversion_goal if conversion_goal else "없음"}\n대표 글결: {resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)}\n보조 글결: {", ".join(clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)) if clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2) else "없음"}\n업체명 반영 강도: {brand_intensity}',1)
s = s.replace('{purpose_block}\n{brand_block}', '{purpose_block}\n{gyeol_block}\n{brand_block}',1)
# Add writing gyeol explicit rule in instructions
s = s.replace('0-4. 위 [글 성격 / 브랜드 반영 / 말투 세부 조건]을 반드시 지킨다. 선택한 글 성격에 맞게 업체명·전환 목표·말맛을 조절한다. 선택한 글 성격에 따라 마무리 강도와 업체 정보 반영 범위를 조절한다.',
              '0-4. 위 [글 성격 / 브랜드 반영 / 말투 세부 조건]을 반드시 지킨다. 선택한 글 성격에 맞게 업체명·전환 목표·말맛을 조절한다. 선택한 글 성격에 따라 마무리 강도와 업체 정보 반영 범위를 조절한다.\n0-5. 위 [원고 글결 적용 지시]를 반드시 지킨다. 대표 글결이 선택 기준형이면 기준을, 오해 반박형이면 오해와 반박을, 대표자 주장형이면 판단 기준과 철학을, 증상 공감형이면 불편 공감과 치료/해결 흐름을 분명히 만든다.',1)

# Claude function signature and internals
s = s.replace('homepage_info="",\n):', 'homepage_info="",\n    primary_gyeol="",\n    secondary_gyeol_1="",\n    secondary_gyeol_2="",\n):',1)
s = s.replace('homepage_info = clean_text(homepage_info) if \'clean_text\' in globals() else (homepage_info or "").strip()\n\n    if not draft_text.strip():',
              'homepage_info = clean_text(homepage_info) if \'clean_text\' in globals() else (homepage_info or "").strip()\n    primary_gyeol = clean_text(primary_gyeol) if \'clean_text\' in globals() else (primary_gyeol or "").strip()\n    secondary_gyeol_1 = clean_text(secondary_gyeol_1) if \'clean_text\' in globals() else (secondary_gyeol_1 or "").strip()\n    secondary_gyeol_2 = clean_text(secondary_gyeol_2) if \'clean_text\' in globals() else (secondary_gyeol_2 or "").strip()\n    resolved_gyeol = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)\n    resolved_secondary_gyeols = clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)\n\n    if not draft_text.strip():')
s = s.replace('boost_rules.append("- 소제목은 본문 문장과 분리해 한 줄 단독으로 유지할 것.")',
              'boost_rules.append("- 소제목은 본문 문장과 분리해 한 줄 단독으로 유지할 것.")\n    boost_rules.append(f"- 원고 글결은 ‘{resolved_gyeol}’입니다. 문장을 다듬더라도 이 글결 흐름을 유지하고, 단순 정보 나열이나 장점 나열문으로 바꾸지 말 것.")')
s = s.replace('- 글 성격: {article_style or \'미입력\'}\n- 목표 분량:', '- 글 성격: {article_style or \'미입력\'}\n- 대표 글결: {resolved_gyeol}\n- 보조 글결: {", ".join(resolved_secondary_gyeols) if resolved_secondary_gyeols else "없음"}\n- 목표 분량:',1)

# Preset keys/options
s = s.replace('"r_article_style", "r_tone_detail", "r_title_type",', '"r_article_style", "r_primary_gyeol", "r_secondary_gyeol_1", "r_secondary_gyeol_2", "r_tone_detail", "r_title_type",')
s = s.replace('"r_article_style": lambda: ARTICLE_STYLES,', '"r_article_style": lambda: ARTICLE_STYLES,\n    "r_primary_gyeol": lambda: WRITING_GYEOL_OPTIONS,\n    "r_secondary_gyeol_1": lambda: WRITING_GYEOL_SECONDARY_OPTIONS,\n    "r_secondary_gyeol_2": lambda: WRITING_GYEOL_SECONDARY_OPTIONS,')

# UI ② insert after article_style selection
s = s.replace('r_article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="r_article_style")\n            r_tone_detail = tone_detail_text_area',
              'r_article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="r_article_style")\n            r_auto_gyeol = auto_recommend_writing_gyeol(r_field, r_article_style, r_topic, r_keyword)\n            r_primary_gyeol = st.selectbox("대표 글결", WRITING_GYEOL_OPTIONS, index=0, key="r_primary_gyeol")\n            st.caption(f"자동 추천 글결: {r_auto_gyeol} · 자동 추천을 두면 주제/분야/글성격으로 원고 흐름을 잡습니다.")\n            r_gcol1, r_gcol2 = st.columns(2)\n            with r_gcol1:\n                r_secondary_gyeol_1 = st.selectbox("보조 글결 1", WRITING_GYEOL_SECONDARY_OPTIONS, index=0, key="r_secondary_gyeol_1")\n            with r_gcol2:\n                r_secondary_gyeol_2 = st.selectbox("보조 글결 2", WRITING_GYEOL_SECONDARY_OPTIONS, index=0, key="r_secondary_gyeol_2")\n            r_tone_detail = tone_detail_text_area')
# UI ② effective goal call
s = s.replace('r_effective_goal = effective_content_goal(r_goal, r_field, r_article_style, r_topic, r_keyword, r_conversion_goal, r_brand_name, r_usecase_mode, r_sub_keywords)',
              'r_effective_goal = effective_content_goal(r_goal, r_field, r_article_style, r_topic, r_keyword, r_conversion_goal, r_brand_name, r_usecase_mode, r_sub_keywords, r_primary_gyeol, r_secondary_gyeol_1, r_secondary_gyeol_2)')
s = s.replace('st.info("적용 원고 목적: " + r_effective_goal)', 'st.info("적용 원고 목적: " + r_effective_goal)\n            st.session_state["r_resolved_primary_gyeol"] = resolve_primary_gyeol(r_primary_gyeol, r_field, r_article_style, r_topic, r_keyword)')

# Research prompt call add gyeol params
s = s.replace('r_homefeed_overseas_usage)', 'r_homefeed_overseas_usage, r_primary_gyeol, r_secondary_gyeol_1, r_secondary_gyeol_2)',1)

# ③ use ② state
s = s.replace('d_article_style = st.session_state.get("r_article_style", "일반 정보성")\n        d_sub_keywords',
              'd_article_style = st.session_state.get("r_article_style", "일반 정보성")\n        d_primary_gyeol = st.session_state.get("r_primary_gyeol", "자동 추천")\n        d_secondary_gyeol_1 = st.session_state.get("r_secondary_gyeol_1", "선택 안함")\n        d_secondary_gyeol_2 = st.session_state.get("r_secondary_gyeol_2", "선택 안함")\n        d_sub_keywords')
s = s.replace('effective_content_goal(st.session_state.get("r_goal", ""), d_field, d_article_style, d_topic, d_keyword, d_conversion_goal, d_brand_name, d_usecase_mode, d_sub_keywords))',
              'effective_content_goal(st.session_state.get("r_goal", ""), d_field, d_article_style, d_topic, d_keyword, d_conversion_goal, d_brand_name, d_usecase_mode, d_sub_keywords, d_primary_gyeol, d_secondary_gyeol_1, d_secondary_gyeol_2))')
s = s.replace('/ 글 성격={d_article_style} / 전환목표=', '/ 글 성격={d_article_style} / 대표글결={resolve_primary_gyeol(d_primary_gyeol, d_field, d_article_style, d_topic, d_keyword)} / 전환목표=')
s = s.replace('st.write(f"글 성격: {d_article_style}")\n                st.write(f"보조 키워드:',
              'st.write(f"글 성격: {d_article_style}")\n                st.write(f"대표 글결: {resolve_primary_gyeol(d_primary_gyeol, d_field, d_article_style, d_topic, d_keyword)}")\n                st.write(f"보조 글결: {", ".join(clean_secondary_gyeols(d_secondary_gyeol_1, d_secondary_gyeol_2)) if clean_secondary_gyeols(d_secondary_gyeol_1, d_secondary_gyeol_2) else "없음"}")\n                st.write(f"보조 키워드:')
# ③ manual insert after d_article_style selectbox
s = s.replace('d_article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="d_article_style")\n            d_tone_detail',
              'd_article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="d_article_style")\n            d_primary_gyeol = st.selectbox("대표 글결", WRITING_GYEOL_OPTIONS, index=0, key="d_primary_gyeol")\n            d_gcol1, d_gcol2 = st.columns(2)\n            with d_gcol1:\n                d_secondary_gyeol_1 = st.selectbox("보조 글결 1", WRITING_GYEOL_SECONDARY_OPTIONS, index=0, key="d_secondary_gyeol_1")\n            with d_gcol2:\n                d_secondary_gyeol_2 = st.selectbox("보조 글결 2", WRITING_GYEOL_SECONDARY_OPTIONS, index=0, key="d_secondary_gyeol_2")\n            d_tone_detail')
s = s.replace('d_content_goal = auto_generate_content_goal(d_field, d_article_style, d_topic, d_keyword, d_conversion_goal, d_brand_name, d_usecase_mode, d_sub_keywords)',
              'd_content_goal = auto_generate_content_goal(d_field, d_article_style, d_topic, d_keyword, d_conversion_goal, d_brand_name, d_usecase_mode, d_sub_keywords, d_primary_gyeol, d_secondary_gyeol_1, d_secondary_gyeol_2)')
# draft_prompt call add params at end
s = s.replace('d_homefeed_overseas_usage, d_content_goal)', 'd_homefeed_overseas_usage, d_content_goal, d_primary_gyeol, d_secondary_gyeol_1, d_secondary_gyeol_2)')
s = s.replace('dynamic_widget_key("draft_prompt_live", d_topic, d_keyword, d_sub_keywords, d_brand_name, d_article_style,', 'dynamic_widget_key("draft_prompt_live", d_topic, d_keyword, d_sub_keywords, d_brand_name, d_article_style, resolve_primary_gyeol(d_primary_gyeol, d_field, d_article_style, d_topic, d_keyword),')
# applied session state after draft generation storage, insert around applied_article_style
s = s.replace('st.session_state["applied_article_style"] = d_article_style\n', 'st.session_state["applied_article_style"] = d_article_style\n        st.session_state["applied_primary_gyeol"] = d_primary_gyeol\n        st.session_state["applied_secondary_gyeol_1"] = d_secondary_gyeol_1\n        st.session_state["applied_secondary_gyeol_2"] = d_secondary_gyeol_2\n')

# ⑧ auto apply variables
s = s.replace('article_style = st.session_state.get("applied_article_style", st.session_state.get("r_article_style", "일반 정보성"))\n            sub_keywords',
              'article_style = st.session_state.get("applied_article_style", st.session_state.get("r_article_style", "일반 정보성"))\n            primary_gyeol = st.session_state.get("applied_primary_gyeol", st.session_state.get("r_primary_gyeol", "자동 추천"))\n            secondary_gyeol_1 = st.session_state.get("applied_secondary_gyeol_1", st.session_state.get("r_secondary_gyeol_1", "선택 안함"))\n            secondary_gyeol_2 = st.session_state.get("applied_secondary_gyeol_2", st.session_state.get("r_secondary_gyeol_2", "선택 안함"))\n            sub_keywords')
s = s.replace('자동 적용: 분야={field} / 사용처={selected_usecase_mode} / 작성자 관점={writer_perspective} / 글 성격={article_style} / 업체명=',
              '자동 적용: 분야={field} / 사용처={selected_usecase_mode} / 작성자 관점={writer_perspective} / 글 성격={article_style} / 대표글결={resolve_primary_gyeol(primary_gyeol, field, article_style, check_topic_for_claude if \'check_topic_for_claude\' in globals() else st.session_state.get("r_topic", ""), keyword)} / 업체명=')
# ⑧ manual add variables
s = s.replace('article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="check_article_style_manual")\n            sub_keywords',
              'article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="check_article_style_manual")\n            primary_gyeol = st.selectbox("대표 글결", WRITING_GYEOL_OPTIONS, index=0, key="check_primary_gyeol_manual")\n            mg1, mg2 = st.columns(2)\n            with mg1:\n                secondary_gyeol_1 = st.selectbox("보조 글결 1", WRITING_GYEOL_SECONDARY_OPTIONS, index=0, key="check_secondary_gyeol_1_manual")\n            with mg2:\n                secondary_gyeol_2 = st.selectbox("보조 글결 2", WRITING_GYEOL_SECONDARY_OPTIONS, index=0, key="check_secondary_gyeol_2_manual")\n            sub_keywords')
s = s.replace('content_goal = effective_content_goal("", field, article_style, st.session_state.get("r_topic", ""), keyword, conversion_goal, brand_name, selected_usecase_mode, sub_keywords)',
              'content_goal = effective_content_goal("", field, article_style, st.session_state.get("r_topic", ""), keyword, conversion_goal, brand_name, selected_usecase_mode, sub_keywords, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2)')
# Claude call add params
s = s.replace('homepage_info=homepage_info,\n    )', 'homepage_info=homepage_info,\n        primary_gyeol=primary_gyeol,\n        secondary_gyeol_1=secondary_gyeol_1,\n        secondary_gyeol_2=secondary_gyeol_2,\n    )',1)
# dynamic widget key add
s = s.replace('dynamic_widget_key("claude_naturalize_check", selected_usecase_mode, writer_perspective, article_style, keyword,', 'dynamic_widget_key("claude_naturalize_check", selected_usecase_mode, writer_perspective, article_style, resolve_primary_gyeol(primary_gyeol, field, article_style, check_topic_for_claude if \'check_topic_for_claude\' in globals() else "", keyword), keyword,')

# check_all signature and body
s = s.replace('conversion_goal=""):', 'conversion_goal="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2=""):',1)
s = s.replace('style_ending_alignment = inspect_article_style_ending_alignment(\n        body=body,', 'style_ending_alignment = inspect_article_style_ending_alignment(\n        body=body,',1)
# insert gyeol alignment after style_ending block end marker
marker = '    )\n\n    # 제목\n'
s = s.replace(marker, '    )\n    gyeol_alignment = inspect_writing_gyeol_alignment(body, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, title, keyword)\n\n    # 제목\n',1)
# insert body issues after subhead joined block perhaps before specialty_profile
s = s.replace('    if specialty_profile and len(specialty_missing) >= 4:', '    if gyeol_alignment.get("issues"):\n        for gi in gyeol_alignment.get("issues", [])[:3]:\n            issues["본문"].append(("글결 반영 약함", gi))\n        body_score -= min(5, 2 + len(gyeol_alignment.get("issues", [])))\n    if specialty_profile and len(specialty_missing) >= 4:',1)
# cap reason before delivery_risks
s = s.replace('    if specialty_profile and len(specialty_missing) >= 4:', '    if gyeol_alignment.get("issues"):\n        total = min(total, 91)\n        cap_reasons.append("선택한 대표 글결이 본문 흐름에 충분히 반영되지 않아 글결 상한 91점 적용")\n    if specialty_profile and len(specialty_missing) >= 4:',1)
# return dict add fields
s = s.replace('"detected_title": detected_title,\n        "first_sentence": first_sentence,', '"detected_title": detected_title,\n        "writing_gyeol": gyeol_alignment,\n        "first_sentence": first_sentence,')
# check_all call add params
s = s.replace('selected_voice_type, selected_usecase_mode, article_style, homepage_mode, homepage_info, brand_name, conversion_goal\n        )', 'selected_voice_type, selected_usecase_mode, article_style, homepage_mode, homepage_info, brand_name, conversion_goal, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2\n        )')

# Some r_effective_goal apply in old exact might have failed; Ensure research prompt call not syntax broken later.
p.write_text(s, encoding='utf-8')
print('patched v1014')
