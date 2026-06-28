from pathlib import Path
import re
p=Path('/mnt/data/v1013_work/app.py')
s=p.read_text(encoding='utf-8')
# version labels
s=s.replace('달로썸 원고 검수기 v10.0.12','달로썸 원고 검수기 v10.0.13')
s=s.replace('page_title="달로썸 원고 검수기 v10.0.12"','page_title="달로썸 원고 검수기 v10.0.13"')
s=s.replace('## v10.0.12 Claude 자연화용 복붙 패키지','## v10.0.13 Claude 보강·자연화 복붙 패키지')

# Insert auto goal helpers after BRAND_INTENSITY_OPTIONS
marker='BRAND_INTENSITY_OPTIONS = ["업체명 없음", "본문 1회만", "본문 2~3회 자연 반영", "제목 포함"]\n'
insert=r'''

# =========================
# v10.0.13: 원고 목적 자동 생성 / 전환형 마무리 보정
# =========================
def auto_generate_content_goal(field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords=""):
    """마케팅 회사가 목적을 짧게 주거나 비워도 분야·글성격·전환목표에 맞는 원고 목적을 자동 생성한다."""
    field = (field or "기타 전문업종").strip()
    style = normalize_article_style(article_style or "정보성")
    topic = (topic or keyword or "해당 주제").strip()
    keyword = (keyword or topic).strip()
    conversion_goal = (conversion_goal or "").strip()
    brand_name = (brand_name or "").strip()
    usecase_mode = (usecase_mode or "블로그 정보성").strip()

    topic_phrase = f"'{topic}' 주제"
    kw_phrase = f"핵심 키워드 '{keyword}' 검색 의도"
    action = conversion_goal or "상담·예약·문의 같은 다음 행동"
    brand_part = "병원/업체의 확인된 장점과 상담 기준" if brand_name else "확인된 서비스 기준과 선택 포인트"

    field_templates = {
        "병원 / 의료": "증상·검사·치료 기준을 차분히 설명하고, 의료진 상담 기준·검사 장비·진료 시스템처럼 확인된 병원 정보를 주제와 연결해 예약 또는 상담 문의로 유도하는 원고",
        "법률": "독자가 처한 법적 상황과 핵심 쟁점을 이해하도록 돕고, 증거·절차·기한·상대방 반박 가능성을 정리해 변호사 상담 문의로 유도하는 원고",
        "청소 / 홈케어": "오염 원인, 작업 범위, 업체 선택 기준을 설명하고, 전문 장비·작업 과정·사후관리 장점을 자연스럽게 연결해 견적 문의로 유도하는 원고",
        "학원 / 교육": "학부모 또는 수강생의 고민을 짚고, 선택 기준·수업 방식·관리 시스템을 설명해 상담 또는 체험수업 문의로 유도하는 원고",
        "맛집 / 카페 / 외식": "방문 상황과 메뉴 선택 기준을 자연스럽게 소개하고, 매장의 특징·위치·이용 장점을 연결해 방문을 유도하는 원고",
        "부동산 / 분양": "입지, 상품 조건, 생활 편의성, 거주·투자 관점의 확인 기준을 설명하고 상담 또는 방문 문의로 유도하는 원고",
        "뷰티 / 미용실 / 네일": "시술 또는 관리 전 고민과 선택 기준을 설명하고, 상담 방식·관리 과정·차별점을 연결해 예약 문의로 유도하는 원고",
        "에스테틱 / 피부관리": "피부 고민과 관리 전 확인 기준을 설명하고, 관리 과정·상담 방식·매장 장점을 자연스럽게 연결해 예약 문의로 유도하는 원고",
        "보험 / 금융": "독자가 조건과 위험을 이해하도록 돕고, 상품 선택 전 확인할 기준을 정리해 상담 문의로 연결하는 원고",
        "세무 / 회계": "세금·신고·자료 준비 기준을 설명하고, 개인 상황별 검토 필요성을 연결해 상담 문의로 유도하는 원고",
        "노무 / 인사": "근로자 또는 사업주의 상황을 기준으로 절차·증빙·쟁점을 설명하고, 노무 상담 문의로 연결하는 원고",
        "요양 / 돌봄 / 복지": "보호자와 이용자의 고민을 짚고, 이용 기준·돌봄 과정·시설 선택 기준을 설명해 상담 문의로 유도하는 원고",
        "IT / 소프트웨어 / 디지털": "기능·도입 기준·비용과 운영 효율을 설명하고, 서비스 상담 또는 도입 문의로 연결하는 원고",
    }
    base = field_templates.get(field, "독자의 고민과 선택 기준을 설명하고, 확인된 업체·서비스 장점을 주제와 연결해 문의 또는 상담으로 유도하는 원고")

    if usecase_mode == "홈피드형" or style == "홈피드 이슈형":
        return f"{topic_phrase}를 최근 이슈와 독자 반응 중심으로 풀어내고, 클릭·공감·저장 포인트가 살아나도록 구성하는 홈피드형 원고"
    if style == "정보성":
        return f"{topic_phrase}에 대해 {kw_phrase}를 가진 독자가 핵심 기준과 주의사항을 이해하도록 돕는 정보성 원고"
    if style == "선택 기준형":
        return f"{topic_phrase}에서 독자가 비교·선택 전 확인해야 할 기준을 정리하고, 본인 상황에 맞는 판단을 돕는 선택 기준형 원고"
    if style == "문제 해결형":
        return f"{topic_phrase}와 관련해 독자가 겪는 불편이나 고민을 먼저 짚고, 원인 확인과 해결 방향을 단계적으로 안내하는 문제 해결형 원고"
    if style == "업체/서비스 소개형":
        return f"{topic_phrase}를 바탕으로 독자가 필요한 기준을 이해한 뒤, {brand_part}을 자료 범위 안에서 자연스럽게 소개하는 업체/서비스 소개형 원고"
    if style == "후기/기자단형":
        return f"{topic_phrase}를 사진자료나 제공 정보 기준으로 자연스럽게 소개하되, 직접 경험한 척하지 않고 방문·이용 전 확인할 포인트를 정리하는 후기/기자단형 원고"
    if style == "카페 자연글형":
        return f"{topic_phrase}를 카페 회원이 정보 공유하듯 자연스럽게 정리하고, 장단점과 주의사항을 부담 없는 말투로 알려주는 원고"
    # 매출 전환형 기본
    return f"{topic_phrase}에 관심 있는 독자에게 핵심 기준과 주의사항을 설명하고, {brand_part}을 주제와 자연스럽게 연결해 {action}로 이어지게 하는 매출 전환형 원고. 단순 설명에서 끝내지 않고 독자의 고민 → 확인 기준 → 상담/문의 필요성 흐름으로 작성한다."


def effective_content_goal(content_goal="", field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords=""):
    """직접 입력한 원고 목적을 최우선으로 사용하고, 비어 있으면 자동 생성한다."""
    typed = (content_goal or "").strip()
    if typed:
        return typed
    return auto_generate_content_goal(field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)


def content_goal_force_block(content_goal="", field="", article_style="", topic="", keyword="", conversion_goal="", brand_name="", usecase_mode="블로그 정보성", sub_keywords=""):
    goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)
    style = normalize_article_style(article_style or "정보성")
    lines = ["[원고 목적 자동 적용]", f"- 최종 적용 원고 목적: {goal}"]
    lines.append("- 원고 목적은 주제보다 넓은 글의 방향이다. 단순 설명으로 끝내지 말고 이 목적에 맞춰 도입, 본문 깊이, 마무리 강도를 조절한다.")
    if article_style_group(style) == "conversion":
        lines.append("- 매출 전환형은 정보성 설명 뒤에 확인된 병원/업체/법무법인 장점을 주제와 연결해 마무리한다.")
        lines.append("- 마무리 장점은 단순 나열이 아니라 ‘왜 이 장점이 이번 주제 해결에 필요한지’로 풀어쓴다.")
        lines.append("- 공식 홈페이지·조사자료·사용자 제공자료에 있는 장비, 시스템, 상담 기준, 원장/대표 철학, 사후관리 중 이번 주제와 연결되는 항목을 2문장 이상 반영한다. 자료에 없는 장점은 만들지 않는다.")
    return "\n".join(lines)


def conversion_ending_weak(body="", article_style="", brand_name="", conversion_goal="", field=""):
    """매출 전환형인데 마지막 문단이 업체명만 넣고 끝나는지 감지한다."""
    style = normalize_article_style(article_style or "정보성")
    if article_style_group(style) != "conversion":
        return False
    if not (brand_name or conversion_goal):
        return False
    ending = (body or "")[-900:]
    if not ending.strip():
        return False
    # 단순 CTA/예약어만 있고 시스템·장비·상담 기준·철학 연결어가 부족하면 약하다고 본다.
    strong_terms = [
        "장비", "시스템", "철학", "원장", "대표", "의료진", "전문의", "전담", "협진", "재활", "사후관리",
        "상담 기준", "검사 시스템", "정밀검사 장비", "진료 체계", "치료 과정", "작업 과정", "관리 과정", "선택 기준",
        "공식 안내", "확인된", "자료 기준", "맞춤", "개인별", "사례", "절차", "증거", "기한"
    ]
    hits = [w for w in strong_terms if w in ending]
    # 병원/법률/서비스 분야는 마지막에 확인된 장점·시스템이 최소 1~2개는 보여야 한다.
    return len(hits) < 2
'''
if marker in s and 'def auto_generate_content_goal' not in s:
    s=s.replace(marker, marker+insert)

# brand_voice_block conversion closure rules
s=s.replace("- 대표 작성형 의료글은 본문 중 2~3곳에 ‘진료실에서 자주 묻는 질문입니다’, ‘환자분들이 가장 헷갈려하는 부분입니다’, ‘상담 때는 이 기준을 먼저 확인합니다’처럼 원장이 설명하는 듯한 문장을 자연스럽게 넣는다.\n            lines.append(\"- 단, ‘저희 병원은’, ‘풍부한 경험’, ‘정직한 진료’, ‘최신 장비’ 같은 병원 장점·철학은 공식 홈페이지나 사용자가 제공한 자료에 있을 때만 쓴다. 공식 홈페이지 정보가 제공되면 확인된 장점·철학 중 이번 주제와 연결되는 내용을 마무리에 반드시 1~2문장 반영한다.\")",
"- 대표 작성형 의료글은 본문 중 2~3곳에 ‘진료실에서 자주 묻는 질문입니다’, ‘환자분들이 가장 헷갈려하는 부분입니다’, ‘상담 때는 이 기준을 먼저 확인합니다’처럼 원장이 설명하는 듯한 문장을 자연스럽게 넣는다.\n            if article_style_group(article_style) == \"conversion\":\n                lines.append(\"- 단, ‘저희 병원은’, ‘풍부한 경험’, ‘정직한 진료’, ‘최신 장비’ 같은 병원 장점·철학은 공식 홈페이지나 사용자가 제공한 자료에 있을 때만 쓴다. 매출 전환형에서 공식/조사자료가 제공되면 확인된 장점·철학·장비·상담 기준 중 이번 주제와 연결되는 내용을 마무리에 2~4문장 반영한다.\")\n            else:\n                lines.append(\"- 단, ‘저희 병원은’, ‘풍부한 경험’, ‘정직한 진료’, ‘최신 장비’ 같은 병원 장점·철학은 공식 홈페이지나 사용자가 제공한 자료에 있을 때만 쓴다. 공식 홈페이지 정보가 제공되면 확인된 장점·철학 중 이번 주제와 연결되는 내용을 마무리에 1~2문장 반영한다.\")")
s=s.replace('- 공식 홈페이지/업체 정보가 제공된 경우에는 확인된 장점·철학·상담 기준 중 이번 주제와 직접 연결되는 내용을 마무리 문단에 반드시 1~2문장 반영한다. 단, 자료에 없는 장점은 만들지 않는다.',
'''- 공식 홈페이지/업체 정보가 제공된 경우에는 확인된 장점·철학·상담 기준 중 이번 주제와 직접 연결되는 내용을 마무리 문단에 반영한다. 정보성은 1~2문장, 매출 전환형은 2~4문장을 권장한다. 단, 자료에 없는 장점은 만들지 않는다.''')

# Title detection expand
old='if any(w in title for w in ["중이신가요", "계신가요", "때", "후", "앞두고", "반복", "고민", "걱정", "저림", "통증", "따갑", "붓기", "냄새", "못했을 때"]):\n        detected.append("6. 독자 상황 콕집기형")'
new='if any(w in title for w in ["중이신가요", "계신가요", "때", "후", "앞두고", "반복", "고민", "고민된다면", "고민이라면", "걱정", "걱정된다면", "헷갈", "헷갈린다면", "망설", "망설인다면", "어렵다면", "불안", "차이", "저림", "통증", "따갑", "붓기", "냄새", "못했을 때"]):\n        detected.append("6. 독자 상황 콕집기형")'
s=s.replace(old,new)

# B concerns expand
s=s.replace('"효과", "효과없", "효과 없음", "반응", "반응 없음", "약", "복용", "부작용", "통증", "붓기", "열감", "비용", "가격", "차이", "비교", "기간", "실패", "불안", "걱정", "헷갈", "망설", "기저질환",',
'''"효과", "효과없", "효과 없음", "반응", "반응 없음", "약", "복용", "부작용", "통증", "붓기", "열감", "비용", "가격", "차이", "비교", "기간", "검사", "검사전", "검사 전", "렌즈", "렌즈중단", "렌즈 중단", "빛번짐", "건조감", "안구건조증", "정밀검사", "각막", "각막두께", "실패", "불안", "걱정", "헷갈", "망설", "기저질환",''')
s=s.replace('r"통증|붓기|열감|볼패임|흉터|색소|감각",\n        r"차이|비교|무엇이\\s*다른|뭐가\\s*다른",\n        r"한\\s*번|1회|언제부터|기간|유지기간",',
'''r"통증|붓기|열감|볼패임|흉터|색소|감각",\n        r"검사\\s*전|정밀검사|각막두께|각막|렌즈\\s*중단|렌즈|빛번짐|건조감|안구건조증",\n        r"헷갈|망설|고민|걱정|불안",\n        r"차이|비교|무엇이\\s*다른|뭐가\\s*다른",\n        r"한\\s*번|1회|언제부터|기간|유지기간",''')
s=s.replace('"효과", "부작용", "통증", "붓", "비용", "가격", "차이", "비교", "불안", "걱정", "헷갈", "망설", "당뇨", "고혈압", "심장", "복용", "반응", "실패", "유지"',
'''"효과", "부작용", "통증", "붓", "비용", "가격", "차이", "비교", "불안", "걱정", "헷갈", "망설", "검사", "렌즈", "빛번짐", "건조", "안구건조", "각막", "정밀검사", "기간", "당뇨", "고혈압", "심장", "복용", "반응", "실패", "유지"''')
s=s.replace('h in {"효과", "부작용", "비용", "가격", "통증", "붓기", "불안", "걱정", "당뇨", "고혈압"}',
'''h in {"효과", "부작용", "비용", "가격", "통증", "붓기", "불안", "걱정", "차이", "비교", "기간", "검사", "검사 전", "렌즈", "빛번짐", "건조감", "안구건조증", "정밀검사", "각막", "당뇨", "고혈압"}''')
s=s.replace('if len(strong_hits) >= 2 or (len(strong_hits) >= 1 and ("?" in first_sentence or "계신가요" in first_sentence or "걱정" in first_sentence)):',
'''if len(strong_hits) >= 2 or (len(strong_hits) >= 1 and ("?" in first_sentence or "계신가요" in first_sentence or "걱정" in first_sentence or "헷갈" in first_sentence or "망설" in first_sentence)):''')
s=s.replace('"당기", "번들", "헷갈", "속상", "고민", "푸석", "예민", "답답", "불안", "막막", "걱정", "망설", "효과", "부작용", "비용", "가격", "통증", "붓기", "약", "반응"',
'''"당기", "번들", "헷갈", "속상", "고민", "푸석", "예민", "답답", "불안", "막막", "걱정", "망설", "검사 전", "렌즈", "빛번짐", "건조감", "안구건조증", "각막", "정밀검사", "효과", "부작용", "비용", "가격", "통증", "붓기", "약", "반응"''')

# refine subtitle false positive detection
old='joined_like_heading = [l for l in lines if 45 <= len(l) <= 120 and re.match(r"^[가-힣A-Za-z0-9·/ ]{6,28}\\s+(검사|수술|상담|결과|비용|회복|주의|라식|라섹|환자|독자|본문|정밀)", l)]\n    if joined_like_heading:'
new='''joined_like_heading = [
        l for l in lines
        if 45 <= len(l) <= 150 and re.match(r"^[가-힣A-Za-z0-9·/ ,]{6,38}(?:입니다|합니다|됩니다|하세요|봅니다)\\s+(?:진료실|환자|독자|검사|수술|상담|라식|라섹|정밀|먼저|그래서)", l)
    ]
    if joined_like_heading:'''
s=s.replace(old,new)

# Add content goal in research prompt: compute effective and force block
old='''    content_goal = (content_goal or "").strip()
    usecase_mode = usecase_mode or "블로그 정보성"
    usecase_block = usecase_style_block(usecase_mode, field)
    brand_block = brand_voice_block(article_style, sub_keywords, brand_name, conversion_goal, brand_intensity, tone_detail, writer_perspective, field, topic, keyword)'''
new='''    content_goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)
    usecase_mode = usecase_mode or "블로그 정보성"
    usecase_block = usecase_style_block(usecase_mode, field)
    purpose_block = content_goal_force_block(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)
    brand_block = brand_voice_block(article_style, sub_keywords, brand_name, conversion_goal, brand_intensity, tone_detail, writer_perspective, field, topic, keyword)'''
s=s.replace(old,new)
s=s.replace('{usecase_block}\n{homefeed_block}\n{brand_block}\n{length_plan}', '{usecase_block}\n{homefeed_block}\n{purpose_block}\n{brand_block}\n{length_plan}', 1)

# Extend build_draft_prompt signature and insert purpose block
s=s.replace('def build_draft_prompt(topic, keyword, field, content_type, voice_type, intro_type, title_type, a_lines, b_lines, c_lines, extra_rules="", target_len=1500, spacing_type="공백 제외", paragraph_option="분량 우선, 문단 수 자연 조절", prompt_mode="달로썸 GPTs용", first_sentence_type="자동 추천", homepage_mode="홈페이지 정보 없음", homepage_info="", keyword_delivery_text="", keyword_placement_text="", usecase_mode="블로그 정보성", writer_perspective="정보성 블로그 작성자", article_style="일반 정보성", sub_keywords="", brand_name="", conversion_goal="", brand_intensity="업체명 없음", tone_detail="", homefeed_category="", homefeed_tone="", homefeed_hook="", homefeed_experience="", homefeed_revenue="", homefeed_issue="", homefeed_overseas_policy="", homefeed_overseas_usage=""):',
'def build_draft_prompt(topic, keyword, field, content_type, voice_type, intro_type, title_type, a_lines, b_lines, c_lines, extra_rules="", target_len=1500, spacing_type="공백 제외", paragraph_option="분량 우선, 문단 수 자연 조절", prompt_mode="달로썸 GPTs용", first_sentence_type="자동 추천", homepage_mode="홈페이지 정보 없음", homepage_info="", keyword_delivery_text="", keyword_placement_text="", usecase_mode="블로그 정보성", writer_perspective="정보성 블로그 작성자", article_style="일반 정보성", sub_keywords="", brand_name="", conversion_goal="", brand_intensity="업체명 없음", tone_detail="", homefeed_category="", homefeed_tone="", homefeed_hook="", homefeed_experience="", homefeed_revenue="", homefeed_issue="", homefeed_overseas_policy="", homefeed_overseas_usage="", content_goal=""):' )
old='''    usecase_block = usecase_style_block(usecase_mode, field)
    brand_block = brand_voice_block(article_style, sub_keywords, brand_name, conversion_goal, brand_intensity, tone_detail, writer_perspective, field, topic, keyword)'''
new='''    usecase_block = usecase_style_block(usecase_mode, field)
    content_goal = effective_content_goal(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)
    purpose_block = content_goal_force_block(content_goal, field, article_style, topic, keyword, conversion_goal, brand_name, usecase_mode, sub_keywords)
    brand_block = brand_voice_block(article_style, sub_keywords, brand_name, conversion_goal, brand_intensity, tone_detail, writer_perspective, field, topic, keyword)'''
s=s.replace(old,new,1)  # this will hit build_draft if build_research already replaced; but check maybe first remaining.
# Ensure draft prompt header includes 원고 목적 and purpose block
s=s.replace('''분야: {field}\n원고 유형: {content_type}\n원고 사용처: {usecase_mode}''', '''분야: {field}\n원고 목적: {content_goal}\n원고 유형: {content_type}\n원고 사용처: {usecase_mode}''')
s=s.replace('''{usecase_block}\n\n{homefeed_block}\n\n{brand_block}''','''{usecase_block}\n\n{homefeed_block}\n\n{purpose_block}\n\n{brand_block}''')
# update writing instruction closing 1-2 to style based
s=s.replace('''11. 마무리는 강한 구매/상담 유도보다 독자가 자기 상황을 확인하게 만드는 방향으로 작성해줘. 단, 홈페이지/업체 정보가 제공된 경우에는 확인된 장점·철학·상담 기준 중 이번 주제와 직접 연결되는 내용을 마무리에 반드시 1~2문장 포함해줘.''',
'''11. 마무리는 글 성격에 맞춰 작성해줘. 정보성은 독자가 자기 상황을 확인하게 만드는 방향으로 낮추고, 매출 전환형은 확인된 병원/업체/법무법인 장점·철학·상담 기준·장비/시스템 중 이번 주제와 직접 연결되는 내용을 2~4문장 반영해 상담/예약/문의로 자연스럽게 이어줘. 단, 자료 없는 장점은 만들지 말고 장점만 줄줄이 나열하지 마.''')

# Add conversion ending weak in check_all score
old='''    if missing_homepage_reflection:
        issues["마무리"].append(("홈페이지 정보 미반영", "홈페이지 정보 있음으로 선택했지만 마지막 문단에 입력된 장점·철학·상담 기준이 거의 반영되지 않았습니다."))
        ending_score -= 5
    if style_ending_alignment.get("level") == "주의":'''
new='''    if missing_homepage_reflection:
        issues["마무리"].append(("홈페이지 정보 미반영", "홈페이지 정보 있음으로 선택했지만 마지막 문단에 입력된 장점·철학·상담 기준이 거의 반영되지 않았습니다."))
        ending_score -= 5
    if conversion_ending_weak(body, article_style, brand_name, conversion_goal, field):
        issues["마무리"].append(("매출전환 마무리 약함", "글 성격이 매출 전환형인데 마지막 문단이 병원/업체 장점, 상담 기준, 장비·시스템, 철학과 충분히 연결되지 않았습니다. 확인된 자료 범위 안에서 2~4문장 보강하세요."))
        ending_score -= 3
    if style_ending_alignment.get("level") == "주의":'''
s=s.replace(old,new)
old='''    if include_philosophy and ending_type != "철학 없이 정보 마무리" and not has_philosophy:
        total = min(total, 92)
        cap_reasons.append("철학 반영을 선택했지만 마지막 문단의 철학 표현이 약해 총점 상한 92점 적용")'''
new='''    if include_philosophy and ending_type != "철학 없이 정보 마무리" and not has_philosophy:
        total = min(total, 92)
        cap_reasons.append("철학 반영을 선택했지만 마지막 문단의 철학 표현이 약해 총점 상한 92점 적용")
    if conversion_ending_weak(body, article_style, brand_name, conversion_goal, field):
        total = min(total, 90)
        cap_reasons.append("매출 전환형인데 마무리 병원/업체 장점 연결이 약해 총점 상한 90점 적용")'''
s=s.replace(old,new)

# Build Claude package signature add homepage params, and rewrite package core
s=s.replace('''    review_notes="",\n    draft_text="",\n    target_len=0,''','''    review_notes="",\n    draft_text="",\n    target_len=0,''')
# Add homepage args after spacing_type via safer signature replacement
s=s.replace('''    target_len=0,
    spacing_type="공백 제외",
    output_rule="최종 원고만 출력",
):''','''    target_len=0,
    spacing_type="공백 제외",
    output_rule="최종 원고만 출력",
    homepage_mode="홈페이지 정보 없음",
    homepage_info="",
):''')
# Insert clean for homepage and mode logic before return
old='''    if not draft_text.strip():
        draft_text = "여기에 GPTs에서 만든 원고를 붙여넣기"

    sensitive_extra = ""'''
new='''    homepage_mode = clean_text(homepage_mode) if 'clean_text' in globals() else (homepage_mode or "홈페이지 정보 없음").strip()
    homepage_info = clean_text(homepage_info) if 'clean_text' in globals() else (homepage_info or "").strip()

    if not draft_text.strip():
        draft_text = "여기에 GPTs에서 만든 원고를 붙여넣기"

    current_len_for_mode = len(re.sub(r"\\s+", "", draft_text)) if spacing_type == "공백 제외" else len(draft_text)
    needs_length_boost = bool(target_len and current_len_for_mode < int(target_len * 0.85))
    needs_conversion_closing = article_style_group(article_style) == "conversion" and bool(brand_name or conversion_goal)
    package_mode = "보강수정" if needs_length_boost or needs_conversion_closing else "자연화"

    sensitive_extra = ""'''
s=s.replace(old,new)
# Replace return header paragraphs
s=s.replace('''return f"""[Claude 자연화 요청 패키지]

아래 원고를 자연스럽게 다듬어줘.
단, 이 요청은 단순 윤문용이다. 구조를 새로 짜거나 조건을 바꾸지 말고, 문장 리듬과 어색한 표현만 정리해줘.''',
'''mode_title = "Claude 보강수정 요청 패키지" if package_mode == "보강수정" else "Claude 자연화 요청 패키지"
    mode_intro = "아래 원고를 앱 검수 기준에 맞게 보강 수정해줘. 단순 윤문이 아니라, 기존 주제와 조건을 유지하면서 부족한 분량, 약한 마무리, 소제목 분리, 첫문장 고민 반영을 함께 보완해줘." if package_mode == "보강수정" else "아래 원고를 자연스럽게 다듬어줘. 구조를 새로 짜거나 조건을 바꾸지 말고, 문장 리듬과 어색한 표현만 정리해줘."
    boost_rules = []
    if needs_length_boost:
        boost_rules.append(f"- 현재 원고가 {spacing_type} 기준 약 {current_len_for_mode}자로 목표 {target_len}자 내외보다 짧다. 의미 없는 반복 없이 검사 기준, 상담 기준, 주의사항, 마무리 설명을 자연스럽게 보강해 목표 분량에 가깝게 늘릴 것.")
    if needs_conversion_closing:
        boost_rules.append("- 글 성격이 매출 전환형이므로 마무리는 단순 정보 요약에서 끝내지 말고, 확인된 병원/업체/법무법인 장점·장비·상담 기준·철학을 이번 주제와 연결해 2~4문장 보강할 것.")
        boost_rules.append("- 장점은 줄줄이 나열하지 말고, 왜 그 장점이 독자의 문제 해결이나 상담 판단에 필요한지로 연결할 것.")
        boost_rules.append("- 자료에 없는 장점, 최신/최고/완벽/보장 표현은 만들지 말 것.")
    boost_rules.append("- 소제목은 본문 문장과 분리해 한 줄 단독으로 유지할 것.")
    boost_rule_text = "\\n".join(boost_rules)

    return f"""[{mode_title}]

{mode_intro}''')
# Replace length_rule behavior maybe duplicate okay but avoid '단순 윤문' contradiction in 수정 범위: add possible boost rules after most important principles
s=s.replace('''- 수정 후에는 {output_rule}한다.
{sensitive_extra}{brand_rule}{conversion_rule}{length_rule}''', '''- 수정 후에는 {output_rule}한다.
{sensitive_extra}{brand_rule}{conversion_rule}{length_rule}

[이번 패키지 모드]
- 모드: {package_mode}
{boost_rule_text}''')
# 수정 범위 allow in boost
s=s.replace('''가능:
- 어색한 문장 자연화
- 반복 어미 줄이기
- 너무 딱딱한 연결어 완화
- 한 문장이 너무 길면 2문장으로 분리
- 사용처에 맞지 않는 말투를 조건 안에서 조정''', '''가능:
- 어색한 문장 자연화
- 반복 어미 줄이기
- 너무 딱딱한 연결어 완화
- 한 문장이 너무 길면 2문장으로 분리
- 사용처에 맞지 않는 말투를 조건 안에서 조정
- 보강수정 모드일 때는 분량 부족, 약한 마무리, 소제목 분리, 첫문장 고민 반영을 조건 안에서 수정''')
s=s.replace('''- 제목 유형 변경
- 도입 화법 변경''', '''- 제목 유형 자체 변경
- 도입 화법 자체 변경''')
s=s.replace('''- 전환문구 새로 추가''','''- 전환 목표를 넘어서는 과한 전환문구 새로 추가''')

# UI ② effective goal display and prompt uses
old='''            r_goal = st.text_input("원고 목적", value="", placeholder="예: 블로그 포트폴리오 및 지역 정보성 원고 / 체험수업 문의 유도", key="r_goal")
            st.subheader("브랜드·전환 설정")'''
new='''            r_goal = st.text_input("원고 목적", value="", placeholder="비워두면 분야·글성격·전환목표 기준으로 자동 생성됩니다", key="r_goal")
            st.caption("직접 쓰면 직접 입력값을 최우선 적용하고, 비워두면 앱이 자동 목적을 만들어 프롬프트에 넣습니다.")
            st.subheader("브랜드·전환 설정")'''
s=s.replace(old,new)
old='''            r_brand_intensity = st.selectbox("업체명 반영 강도", BRAND_INTENSITY_OPTIONS, index=0, key="r_brand_intensity")
            r_len_col1, r_len_col2 = st.columns(2)'''
new='''            r_brand_intensity = st.selectbox("업체명 반영 강도", BRAND_INTENSITY_OPTIONS, index=0, key="r_brand_intensity")
            r_effective_goal = effective_content_goal(r_goal, r_field, r_article_style, r_topic, r_keyword, r_conversion_goal, r_brand_name, r_usecase_mode, r_sub_keywords)
            st.info("적용 원고 목적: " + r_effective_goal)
            st.session_state["r_effective_goal"] = r_effective_goal
            r_len_col1, r_len_col2 = st.columns(2)'''
s=s.replace(old,new)
s=s.replace('research_prompt = build_research_prompt(r_topic, r_keyword, r_field, r_goal, r_extra_for_prompt,', 'research_prompt = build_research_prompt(r_topic, r_keyword, r_field, st.session_state.get("r_effective_goal", r_goal), r_extra_for_prompt,')
# Set d_goal in design from session/direct, show effective
s=s.replace('''        d_brand_intensity = st.session_state.get("r_brand_intensity", "업체명 없음")
        d_tone_detail = st.session_state.get("r_tone_detail", default_tone_by_article_style(d_article_style, d_writer_perspective))''',
'''        d_brand_intensity = st.session_state.get("r_brand_intensity", "업체명 없음")
        d_content_goal = st.session_state.get("r_effective_goal", effective_content_goal(st.session_state.get("r_goal", ""), d_field, d_article_style, d_topic, d_keyword, d_conversion_goal, d_brand_name, d_usecase_mode, d_sub_keywords))
        d_tone_detail = st.session_state.get("r_tone_detail", default_tone_by_article_style(d_article_style, d_writer_perspective))''')
s=s.replace('''                st.write(f"전환 목표: {d_conversion_goal or '없음'}")
                st.write(f"업체명 반영 강도: {d_brand_intensity}")''',
'''                st.write(f"전환 목표: {d_conversion_goal or '없음'}")
                st.write(f"적용 원고 목적: {d_content_goal}")
                st.write(f"업체명 반영 강도: {d_brand_intensity}")''')
# Direct design: set d_content_goal after conversion variables
s=s.replace('''            d_brand_intensity = st.selectbox("업체명 반영 강도", BRAND_INTENSITY_OPTIONS, index=0, key="d_brand_intensity")
            if d_usecase_mode == "홈피드형" or d_article_style in ["홈피드 후킹형", "홈피드 수익형 블로그 글"]:''',
'''            d_brand_intensity = st.selectbox("업체명 반영 강도", BRAND_INTENSITY_OPTIONS, index=0, key="d_brand_intensity")
            d_content_goal = auto_generate_content_goal(d_field, d_article_style, d_topic, d_keyword, d_conversion_goal, d_brand_name, d_usecase_mode, d_sub_keywords)
            st.info("자동 원고 목적: " + d_content_goal)
            if d_usecase_mode == "홈피드형" or d_article_style in ["홈피드 후킹형", "홈피드 수익형 블로그 글"]:''')
# store applied_goal and call build_draft
s=s.replace('''        st.session_state["applied_brand_intensity"] = d_brand_intensity
        st.session_state["applied_tone_detail"] = d_tone_detail''',
'''        st.session_state["applied_brand_intensity"] = d_brand_intensity
        st.session_state["applied_content_goal"] = d_content_goal
        st.session_state["applied_tone_detail"] = d_tone_detail''')
s=s.replace('''draft_prompt = build_draft_prompt(d_topic, d_keyword, d_field, d_content_type, d_voice, d_intro_type, d_title_type, a_lines, b_lines, c_lines, d_extra_rules, d_target_len, d_spacing_type, d_paragraph_option, d_prompt_mode, d_first_sentence_type, d_homepage_mode, d_homepage_info, d_keyword_delivery_text, d_keyword_placement_text, d_usecase_mode, d_writer_perspective, d_article_style, d_sub_keywords, d_brand_name, d_conversion_goal, d_brand_intensity, d_tone_detail, d_homefeed_category, d_homefeed_tone, d_homefeed_hook, d_homefeed_experience, d_homefeed_revenue, d_homefeed_issue, d_homefeed_overseas_policy, d_homefeed_overseas_usage)''',
'''draft_prompt = build_draft_prompt(d_topic, d_keyword, d_field, d_content_type, d_voice, d_intro_type, d_title_type, a_lines, b_lines, c_lines, d_extra_rules, d_target_len, d_spacing_type, d_paragraph_option, d_prompt_mode, d_first_sentence_type, d_homepage_mode, d_homepage_info, d_keyword_delivery_text, d_keyword_placement_text, d_usecase_mode, d_writer_perspective, d_article_style, d_sub_keywords, d_brand_name, d_conversion_goal, d_brand_intensity, d_tone_detail, d_homefeed_category, d_homefeed_tone, d_homefeed_hook, d_homefeed_experience, d_homefeed_revenue, d_homefeed_issue, d_homefeed_overseas_policy, d_homefeed_overseas_usage, d_content_goal)''')
# Check tab get content_goal and notes
s=s.replace('''            brand_intensity = st.session_state.get("applied_brand_intensity", st.session_state.get("r_brand_intensity", "업체명 없음"))
            tone_detail = st.session_state.get("applied_tone_detail", st.session_state.get("r_tone_detail", default_tone_by_article_style(article_style, writer_perspective)))''',
'''            brand_intensity = st.session_state.get("applied_brand_intensity", st.session_state.get("r_brand_intensity", "업체명 없음"))
            content_goal = st.session_state.get("applied_content_goal", st.session_state.get("r_effective_goal", st.session_state.get("r_goal", "")))
            tone_detail = st.session_state.get("applied_tone_detail", st.session_state.get("r_tone_detail", default_tone_by_article_style(article_style, writer_perspective)))''')
s=s.replace('''            conversion_goal = st.text_input("전환 목표", placeholder="예: 무료 체험수업 문의 유도", key="check_conversion_goal_manual")
            brand_intensity = st.selectbox("업체명 반영 강도", BRAND_INTENSITY_OPTIONS, index=0, key="check_brand_intensity_manual")''',
'''            conversion_goal = st.text_input("전환 목표", placeholder="예: 무료 체험수업 문의 유도", key="check_conversion_goal_manual")
            content_goal = effective_content_goal("", field, article_style, st.session_state.get("r_topic", ""), keyword, conversion_goal, brand_name, selected_usecase_mode, sub_keywords)
            brand_intensity = st.selectbox("업체명 반영 강도", BRAND_INTENSITY_OPTIONS, index=0, key="check_brand_intensity_manual")''')
s=s.replace('''    st.write("## v10.0.13 Claude 보강·자연화 복붙 패키지")
    st.caption("이 패키지는 Claude에 보내는 용도입니다. 여기서 만든 패키지를 Claude에 붙여넣고, Claude가 돌려준 수정본을 다시 위 원고 칸에 넣은 뒤 앱 검수를 실행하세요.")''',
'''    st.write("## v10.0.13 Claude 보강·자연화 복붙 패키지")
    st.caption("분량 부족·매출전환 마무리 약함이 있으면 자동으로 보강수정 모드가 되고, 충분하면 자연화 모드로 동작합니다.")''')
old='''    check_review_note_for_claude = f"검수 전 자연화 단계입니다. 사용처={selected_usecase_mode}, 분야={field}, 키워드={keyword}, 업체명={brand_name or '없음'}, 전환목표={conversion_goal or '없음'} 조건을 유지하세요."'''
new='''    extra_claude_notes = []
    if draft.strip():
        draft_len_for_note = len(re.sub(r"\\s+", "", draft))
        if check_target_len and draft_len_for_note < int(check_target_len * 0.85):
            extra_claude_notes.append(f"현재 원고가 공백 제외 {draft_len_for_note}자로 목표 {check_target_len}자 내외보다 짧으므로 보강수정이 필요합니다.")
        if article_style_group(article_style) == "conversion" and (brand_name or conversion_goal):
            extra_claude_notes.append("매출 전환형이므로 마무리에 확인된 병원/업체/법무법인 장점·상담 기준·장비/시스템·철학을 주제와 연결해 2~4문장 보강해야 합니다.")
        if selected_title_type == "6. 독자 상황 콕집기형":
            extra_claude_notes.append("제목 유형은 독자 상황 콕집기형입니다. '헷갈린다면/고민된다면/걱정된다면/망설여진다면' 같은 상황형 제목은 유지 가능합니다.")
    check_review_note_for_claude = f"검수 전 단계입니다. 사용처={selected_usecase_mode}, 분야={field}, 키워드={keyword}, 업체명={brand_name or '없음'}, 전환목표={conversion_goal or '없음'}, 원고목적={content_goal or '자동 생성'} 조건을 유지하세요." + ("\\n" + "\\n".join(extra_claude_notes) if extra_claude_notes else "")'''
s=s.replace(old,new)
# pass homepage args and include content_goal as required point? We can append to required_points
s=s.replace('''        required_points=check_required_for_claude,''','''        required_points=(("원고 목적: " + content_goal + "\\n") if content_goal else "") + (check_required_for_claude or ""),''')
s=s.replace('''        spacing_type="공백 제외",
        output_rule="최종 원고만 출력",
    )''','''        spacing_type="공백 제외",
        output_rule="최종 원고만 출력",
        homepage_mode=homepage_mode,
        homepage_info=homepage_info,
    )''',1)
# labels download names
s=s.replace('"Claude 자연화 패키지 txt 다운로드"','"Claude 보강·자연화 패키지 txt 다운로드"')
s=s.replace('dalrosom_claude_naturalize_package.txt','dalrosom_claude_boost_or_naturalize_package.txt')

p.write_text(s,encoding='utf-8')
