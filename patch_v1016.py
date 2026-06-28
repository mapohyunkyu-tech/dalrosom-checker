from pathlib import Path
p=Path('/mnt/data/v1016_work/app.py')
s=p.read_text(encoding='utf-8')

s=s.replace('달로썸 원고 검수기 v10.0.15','달로썸 원고 검수기 v10.0.16')
s=s.replace('page_title="달로썸 원고 검수기 v10.0.15"','page_title="달로썸 원고 검수기 v10.0.16"')
s=s.replace('## v10.0.15 Claude 보강·자연화 복붙 패키지','## v10.0.16 Claude 보강·자연화 복붙 패키지')

marker = 'def writing_gyeol_prompt_block(primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style="", topic="", keyword=""):'
insert = '''

def writing_gyeol_mandatory_block(primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style="", topic="", keyword=""):
    """v10.0.16: 선택한 글결이 실제 본문에서 보이도록 필수 장치를 강제한다."""
    primary = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)
    seconds = clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)
    active = [primary] + [g for g in seconds if g != primary]
    lines = ["[글결 필수 장치 · v10.0.16]", "- 아래 필수 장치는 원고 본문에 실제 문장으로 드러나야 한다. 조건 설명으로만 쓰지 말 것."]
    if "대표자 주장형" in active:
        lines += [
            "- 대표자 주장형 필수: 도입 또는 첫 번째 본문 구간에 대표원장·변호사·대표가 직접 기준을 설명하는 관점 문장을 넣는다.",
            "- 예시 방향: ‘제가 상담에서 먼저 보는 기준은…’, ‘의료진 입장에서 중요하게 보는 것은…’, ‘현장에서 자주 듣는 질문은…’처럼 판단 기준을 드러낸다.",
            "- 단, 실제 경험을 과장하거나 치료·승소·효과를 보장하는 표현은 쓰지 않는다.",
            "- 대표자 주장형인데 단순 정보 나열만 하면 지시 불이행이다.",
        ]
    if "오해 반박형" in active:
        lines += [
            "- 오해 반박형 필수: 독자가 흔히 착각하는 기준 1개 이상을 먼저 제시하고 ‘하지만 실제로는…’ 흐름으로 반박한다.",
            "- 예시 방향: 장비명, 샷 수, 횟수, 가격, 수술명, 후기만 보고 판단하면 부족한 이유를 설명한다.",
        ]
    if "장비보다 해석/판단 강조형" in active:
        lines += [
            "- 장비보다 해석/판단 강조형 필수: 장비나 방법 설명 후 반드시 ‘그 결과를 어떻게 해석하고 적용할지’가 더 중요하다는 문장을 넣는다.",
            "- 의료 분야라면 검사 결과·영상·피부 상태·통증 원인·각막 상태 등을 의료진이 어떻게 판단하는지로 연결한다.",
        ]
    if "병원/업체 선택 기준형" in active or "선택 기준형" in active:
        lines += [
            "- 선택 기준형 필수: 독자가 병원·업체·서비스를 고를 때 확인할 기준을 최소 3개 이상 제시한다.",
            "- 장점은 단순 홍보가 아니라 각 기준과 연결해 설명한다.",
        ]
    if "증상 공감형" in active:
        lines += [
            "- 증상 공감형 필수: 첫 700자 안에 독자의 불편·걱정·망설임을 구체적으로 짚고, 단순 공감에서 끝내지 말고 원인 확인으로 연결한다.",
        ]
    if "수술·시술·상담 전 체크형" in active:
        lines += [
            "- 체크형 필수: 상담·검사·수술·시술 전 확인할 항목을 본문 중간에 3개 이상 설명한다. 체크리스트만 던지고 끝내지 않는다.",
        ]
    if "치료·해결 방법 설명형" in active:
        lines += [
            "- 치료·해결 방법 설명형 필수: 초기 관리, 검사/진단, 치료/작업 선택지, 상담 필요성을 단계적으로 연결한다.",
        ]
    if "병원/업체 시스템 연결형" in active:
        lines += [
            "- 시스템 연결형 필수: 확인된 자료가 있을 때 상담·검사·작업·진료 시스템을 주제 해결과 연결한다. 자료 없는 장점은 만들지 않는다.",
        ]
    return "\\n".join(lines)
'''
if 'def writing_gyeol_mandatory_block(' not in s:
    s=s.replace(marker, insert+'\n'+marker)

old = '''    flow = flow_map.get(primary, flow_map["기본 정보성"])
    extra = ""
    if seconds:
        extra = "\\n- 보조 글결은 대표 글결을 흐리지 않는 선에서 문단 전환부와 마무리에만 자연스럽게 섞는다."
    return "\\n".join([
        "[원고 글결 적용 지시]",
        f"- 대표 글결: {primary}",
        f"- 보조 글결: {', '.join(seconds) if seconds else '없음'}",
        f"- 최종 글결 조합: {names}",
        "- 글 성격은 큰 분류이고, 글결은 실제 본문 흐름이다. 단순 정보 나열로 쓰지 말고 아래 흐름을 우선한다.",
        "- 권장 흐름: " + " → ".join(flow),
        "- 병원·법률·금융 등 민감 업종은 글결이 강해도 결과 보장, 과장, 공포 조장은 피한다.",
        "- 매출 전환형이라도 장점 나열문으로 끝내지 말고, 선택 기준·판단 기준과 연결해 자연스럽게 마무리한다." + extra,
    ])
'''
new = '''    flow = flow_map.get(primary, flow_map["기본 정보성"])
    extra = ""
    if seconds:
        extra = "\\n- 보조 글결은 대표 글결을 흐리지 않는 선에서 문단 전환부와 마무리에만 자연스럽게 섞되, 최소 1개 이상의 보조 글결은 실제 본문 문장으로 보이게 한다."
    mandatory = writing_gyeol_mandatory_block(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword)
    return "\\n".join([
        "[원고 글결 적용 지시]",
        f"- 대표 글결: {primary}",
        f"- 보조 글결: {', '.join(seconds) if seconds else '없음'}",
        f"- 최종 글결 조합: {names}",
        "- 글 성격은 큰 분류이고, 글결은 실제 본문 흐름이다. 단순 정보 나열로 쓰지 말고 아래 흐름을 우선한다.",
        "- 권장 흐름: " + " → ".join(flow),
        "- 병원·법률·금융 등 민감 업종은 글결이 강해도 결과 보장, 과장, 공포 조장은 피한다.",
        "- 매출 전환형이라도 장점 나열문으로 끝내지 말고, 선택 기준·판단 기준과 연결해 자연스럽게 마무리한다." + extra,
        mandatory,
    ])
'''
if old in s:
    s=s.replace(old,new)
else:
    print('writing_gyeol_prompt_block return block not found')

s=s.replace('- 단순 체크리스트 정보글로 축소하지 말고, 선택한 글결의 필수 흐름을 본문 구조로 구현한다.', '- 단순 체크리스트 정보글로 축소하지 말고, 선택한 글결의 필수 흐름과 [글결 필수 장치]를 본문 구조로 구현한다.\n- 대표자 주장형이 포함되면 대표/전문가가 중요하게 보는 기준 문장을 반드시 넣고, 오해 반박형이 포함되면 흔한 오해와 반박 문장을 반드시 넣는다.')

# Replace inspect function
start=s.index('def inspect_writing_gyeol_alignment(')
end=s.index('\n\n# =========================\n# v10.0.13', start)
new_func = '''def inspect_writing_gyeol_alignment(body="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style="", topic="", keyword=""):
    primary = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)
    seconds = clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)
    active = [primary] + [g for g in seconds if g != primary]
    text = body or ""
    issues = []
    def has(words):
        return any(w in text for w in words)
    def count(words):
        return sum(text.count(w) for w in words)

    if "오해 반박형" in active:
        if not has(["무조건", "같을까요", "좋을까요", "오해", "착각", "그럴까요", "아닙니다", "다릅니다", "하지만", "실제로는", "보다 먼저", "만 보면", "만으로"]):
            issues.append("오해 반박형인데 흔한 오해를 제시하고 반박하는 문장이 약합니다.")
    if "병원/업체 선택 기준형" in active or "선택 기준형" in active:
        if count(["기준", "확인", "살펴", "피하", "고를", "선택", "봐야", "따져", "먼저 볼"]) < 5:
            issues.append("선택 기준형인데 독자가 확인할 기준이 충분히 보이지 않습니다.")
    if "대표자 주장형" in active:
        perspective_hits = count(["제가", "저희가", "의료진", "전문의", "원장", "변호사", "대표", "상담에서", "진료실", "현장에서", "중요하게 보는", "먼저 보는", "중요하게 봅니다", "중요하게 생각", "판단 기준", "원칙", "철학"])
        if perspective_hits < 2:
            issues.append("대표자 주장형인데 대표/전문가가 중요하게 보는 판단 기준이나 관점 문장이 약합니다.")
    if "장비보다 해석/판단 강조형" in active:
        if not has(["해석", "판단", "분석", "결과를", "상태를", "검사 결과", "세팅", "기준", "배분", "위치", "적용", "설계"]):
            issues.append("장비보다 해석/판단 강조형인데 장비 이후의 해석·판단 기준 설명이 약합니다.")
        if has(["장비", "C-ARM", "써마지", "울쎄라", "검사", "시술"]) and not has(["만으로", "보다", "해석", "판단", "분석", "배분", "설계"]):
            issues.append("장비/시술 설명은 있지만 ‘장비보다 해석·판단이 중요하다’는 주장이 약합니다.")
    if "증상 공감형" in active:
        if not has(["아프", "통증", "불편", "반복", "답답", "걱정", "헷갈", "망설", "냄새", "얼룩", "문제", "붓기", "열감"]):
            issues.append("증상 공감형인데 독자의 증상·불편·문제 상황을 짚는 문장이 약합니다.")
    if "수술·시술·상담 전 체크형" in active:
        if not has(["전 확인", "먼저", "체크", "주의", "준비", "검사", "상담 전", "예약 전", "시술 전", "수술 전"]):
            issues.append("체크형인데 상담·검사·시술 전 확인해야 할 항목이 약합니다.")
    if "치료·해결 방법 설명형" in active:
        if not has(["치료", "해결", "관리", "방법", "초기", "검사", "상담", "계획"]):
            issues.append("치료·해결 방법 설명형인데 원인 확인 후 해결/치료 방향 설명이 약합니다.")
    if "병원/업체 시스템 연결형" in active:
        if not has(["시스템", "과정", "절차", "장비", "상담 기준", "검사", "관리", "사후", "협진", "체계"]):
            issues.append("병원/업체 시스템 연결형인데 확인된 시스템이나 과정 설명이 약합니다.")
    return {"primary": primary, "secondary": seconds, "active": active, "issues": issues}
'''
s=s[:start]+new_func+s[end:]

needle='''    boost_rules.append("- 소제목은 본문 문장과 분리해 한 줄 단독으로 유지할 것.")
    boost_rules.append(f"- 원고 글결은 ‘{resolved_gyeol}’입니다. 문장을 다듬더라도 이 글결 흐름을 유지하고, 단순 정보 나열이나 장점 나열문으로 바꾸지 말 것.")
    boost_rule_text = "\\n".join(boost_rules)
'''
replace='''    boost_rules.append("- 소제목은 본문 문장과 분리해 한 줄 단독으로 유지할 것.")
    boost_rules.append(f"- 원고 글결은 ‘{resolved_gyeol}’입니다. 문장을 다듬더라도 이 글결 흐름을 유지하고, 단순 정보 나열이나 장점 나열문으로 바꾸지 말 것.")
    if "대표자 주장형" in ([resolved_gyeol] + resolved_secondary_gyeols):
        boost_rules.append("- 대표자 주장형이 포함되어 있으므로 대표원장·변호사·대표 등 전문가가 중요하게 보는 판단 기준 문장을 1~2개 이상 보강할 것. 단, 실제 경험을 과장하거나 결과를 보장하지 말 것.")
    if "오해 반박형" in ([resolved_gyeol] + resolved_secondary_gyeols):
        boost_rules.append("- 오해 반박형이 포함되어 있으므로 흔한 오해 1개와 ‘하지만 실제로는…’에 해당하는 반박 흐름을 유지하거나 보강할 것.")
    if "장비보다 해석/판단 강조형" in ([resolved_gyeol] + resolved_secondary_gyeols):
        boost_rules.append("- 장비보다 해석/판단 강조형이 포함되어 있으므로 장비·방법 설명에서 끝내지 말고 해석·판단·배분·적용 기준을 보강할 것.")
    boost_rules.append(writing_gyeol_mandatory_block(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword))
    boost_rule_text = "\\n".join(boost_rules)
'''
if needle in s:
    s=s.replace(needle, replace)
else:
    print('Claude boost block not found')

p.write_text(s, encoding='utf-8')
print('patched v1016')
