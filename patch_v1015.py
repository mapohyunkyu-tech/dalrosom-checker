from pathlib import Path
p=Path('/mnt/data/v1015_work/app.py')
s=p.read_text()
# Version labels
s=s.replace('st.set_page_config(page_title="달로썸 원고 검수기 v10.0.14", layout="wide")','st.set_page_config(page_title="달로썸 원고 검수기 v10.0.15", layout="wide")')
s=s.replace('st.title("📝 달로썸 원고 검수기 v10.0.13")','st.title("📝 달로썸 원고 검수기 v10.0.15")')
s=s.replace('st.title("📝 달로썸 원고 검수기 v10.0.14")','st.title("📝 달로썸 원고 검수기 v10.0.15")')
# Top flow wording
s=s.replace('③ 조사 결과/초안 프롬프트 → GPTs 초안 생성 → ⑧ Claude 패키지 생성', '③ 조사 결과/초안 프롬프트 → 일반 GPT 또는 달로썸 GPTs 초안 생성 → ⑧ Claude 패키지 생성')
s=s.replace('GPTs 초안을 만든 뒤에는 ⑧', '일반 GPT 또는 GPTs에서 초안을 만든 뒤에는 ⑧')
# Add prompt execution mode and style safety functions after writing_gyeol_prompt_block
marker = 'def inspect_writing_gyeol_alignment(body="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style="", topic="", keyword=""):'
insert = r'''

# =========================
# v10.0.15: 일반 GPT용 실행 모드 / 전문직 문체 안전장치
# =========================
def prompt_execution_mode_block(prompt_mode="달로썸 GPTs용", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style="", topic="", keyword=""):
    """달로썸 GPTs 없이 일반 GPT에 붙여도 글결과 출력 구조가 무너지지 않게 하는 실행 모드 지시."""
    primary = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)
    seconds = clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)
    names = " + ".join([primary] + seconds) if seconds else primary
    if prompt_mode == "일반 GPT용":
        return f"""[일반 GPT용 실행 규칙]
- 이 프롬프트는 별도 GPTs 설정 없이 일반 GPT에 그대로 붙여넣는 용도다.
- 달로썸 GPTs 내부 규칙, 이전 대화, 숨은 프리셋이 없다고 가정하고 아래 조건만으로 원고를 작성한다.
- 대표 글결은 ‘{primary}’이며, 최종 글결 조합은 ‘{names}’이다. 이 글결이 제목, 도입, 소제목, 마무리에서 눈에 보이게 드러나야 한다.
- 단순 체크리스트 정보글로 축소하지 말고, 선택한 글결의 필수 흐름을 본문 구조로 구현한다.
- 조건 설명, 분석, 사과, 메모를 출력하지 말고 “제목 후보 / 최종 제목 / 본문”만 출력한다.
- 달로썸식 기존 문체가 필요하면 달로썸 GPTs용을 따로 사용하고, 일반 GPT용에서는 아래 명시 조건을 우선한다."""
    if prompt_mode == "외부 GPTs용 강제 프롬프트":
        return f"""[외부 GPTs용 강제 실행 규칙]
- 외부 GPTs의 기존 성격보다 아래 원고 조건을 우선한다.
- 대표 글결 ‘{primary}’와 보조 글결 ‘{', '.join(seconds) if seconds else '없음'}’을 반드시 반영한다.
- 원고 조건을 요약하거나 질문하지 말고 바로 초안을 작성한다."""
    return f"""[달로썸 GPTs용 실행 규칙]
- 달로썸 GPTs의 기존 말맛을 활용하되, 아래 선택 조건과 글결을 우선 적용한다.
- 대표 글결 ‘{primary}’와 보조 글결 ‘{', '.join(seconds) if seconds else '없음'}’을 무시하지 않는다.
- 달로썸식 원고가 필요할 때 사용하는 모드이며, 일반 GPT에 붙일 때는 ‘일반 GPT용’을 권장한다."""


def professional_style_safety_block(field="", writer_perspective="", usecase_mode=""):
    text = f"{field} {writer_perspective} {usecase_mode}"
    is_professional = any(x in text for x in ["병원", "의료", "법률", "변호사", "세무", "노무", "금융", "보험", "전문", "원장", "의사"])
    if not is_professional:
        return """[문체 안전장치]
- 자연스럽게 쓰되 비표준 어미나 장난스러운 말투를 사용하지 않는다.
- ‘입니다요’, ‘합니다요’, ‘됩니다요’, ‘좋습니다요’ 같은 어색한 종결은 절대 사용하지 않는다."""
    return """[전문직 문체 안전장치]
- 병원·법률·전문직 원고는 차분한 존댓말로 쓴다.
- 부드럽게 쓰더라도 비표준 어미, 장난스러운 구어체, 과한 친근체를 쓰지 않는다.
- ‘입니다요’, ‘합니다요’, ‘됩니다요’, ‘좋습니다요’, ‘필요합니다요’, ‘확인해야 합니다요’ 같은 표현은 절대 사용하지 않는다.
- 기본 종결은 ‘~입니다.’, ‘~합니다.’, ‘~할 수 있습니다.’, ‘~확인해야 합니다.’, ‘~상담이 필요합니다.’로 정리한다.
- ‘~하죠’, ‘~거든요’, ‘~잖아요’를 반복하지 않는다. 필요할 때만 1~2회 이하로 사용한다.
- 대표원장/변호사/전문가 관점이라도 실제 경험을 지어내지 않고, 판단 기준과 상담 기준 중심으로 설명한다."""


def detect_nonstandard_professional_endings(text=""):
    patterns = ["입니다요", "합니다요", "됩니다요", "좋습니다요", "필요합니다요", "확인해야 합니다요", "봅니다요", "들어갑니다요", "중요합니다요"]
    hits = []
    for p in patterns:
        if p in (text or ""):
            hits.append(p)
    return sorted(set(hits))

'''
if marker not in s:
    raise SystemExit('marker not found')
s=s.replace(marker, insert+marker)
# Add variable assignments in build_draft_prompt after gyeol_block
old='''    gyeol_block = writing_gyeol_prompt_block(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword)\n    homefeed_block = homefeed_planning_block(homefeed_category, homefeed_tone, homefeed_hook, homefeed_experience, homefeed_revenue, homefeed_issue, homefeed_overseas_policy, homefeed_overseas_usage) if usecase_mode == "홈피드형" or article_style in ["홈피드 후킹형", "홈피드 수익형 블로그 글", "홈판 후킹형"] else ""'''
new='''    gyeol_block = writing_gyeol_prompt_block(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword)\n    execution_mode_block = prompt_execution_mode_block(prompt_mode, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword)\n    style_safety_block = professional_style_safety_block(field, writer_perspective, usecase_mode)\n    homefeed_block = homefeed_planning_block(homefeed_category, homefeed_tone, homefeed_hook, homefeed_experience, homefeed_revenue, homefeed_issue, homefeed_overseas_policy, homefeed_overseas_usage) if usecase_mode == "홈피드형" or article_style in ["홈피드 후킹형", "홈피드 수익형 블로그 글", "홈판 후킹형"] else ""'''
if old not in s:
    raise SystemExit('gyeol block assignment marker not found')
s=s.replace(old,new)
# Mode notice tri-state
old='''    if prompt_mode == "외부 GPTs용 강제 프롬프트":\n        mode_notice = "외부 GPTs용입니다. 아래 조건은 추천이 아니라 필수 작성 조건입니다. 조건을 지키지 못하면 다시 작성해야 합니다."\n    else:\n        mode_notice = "달로썸 GPTs용입니다. 기존 GPTs 설정과 충돌하더라도 아래 선택 조건을 우선 적용합니다."'''
new='''    if prompt_mode == "일반 GPT용":\n        mode_notice = "일반 GPT용입니다. 별도 GPTs 설정이 없다고 가정하고 아래 조건만으로 작성합니다. 글결·분량·문체 안전장치를 반드시 지켜야 합니다."\n    elif prompt_mode == "외부 GPTs용 강제 프롬프트":\n        mode_notice = "외부 GPTs용입니다. 아래 조건은 추천이 아니라 필수 작성 조건입니다. 조건을 지키지 못하면 다시 작성해야 합니다."\n    else:\n        mode_notice = "달로썸 GPTs용입니다. 기존 GPTs 설정과 충돌하더라도 아래 선택 조건을 우선 적용합니다."'''
if old not in s:
    raise SystemExit('mode_notice marker not found')
s=s.replace(old,new)
# Insert execution/style blocks into prompt near purpose/gyeol
old='''{purpose_block}\n\n{gyeol_block}\n\n{brand_block}'''
new='''{purpose_block}\n\n{execution_mode_block}\n\n{gyeol_block}\n\n{style_safety_block}\n\n{brand_block}'''
if old not in s:
    raise SystemExit('prompt insertion marker not found')
s=s.replace(old,new)
# Add writing instruction emphasizing normal GPT and style, after 0-5 maybe
old='''0-5. 위 [원고 글결 적용 지시]를 반드시 지킨다. 대표 글결이 선택 기준형이면 기준을, 오해 반박형이면 오해와 반박을, 대표자 주장형이면 판단 기준과 철학을, 증상 공감형이면 불편 공감과 치료/해결 흐름을 분명히 만든다.'''
new='''0-5. 위 [원고 글결 적용 지시]를 반드시 지킨다. 대표 글결이 선택 기준형이면 기준을, 오해 반박형이면 오해와 반박을, 대표자 주장형이면 판단 기준과 철학을, 증상 공감형이면 불편 공감과 치료/해결 흐름을 분명히 만든다.\n0-5-1. 일반 GPT용 모드에서는 달로썸 GPTs가 대신 잡아준다고 생각하지 말고, 글결 구조를 소제목과 문단 흐름에 직접 반영한다.\n0-5-2. 전문직 문체 안전장치를 지켜 ‘입니다요/합니다요/됩니다요’ 같은 비표준 어미를 절대 쓰지 않는다.'''
if old not in s:
    raise SystemExit('instruction 0-5 marker not found')
s=s.replace(old,new)
# Prompt avoid list add weird endings
old='''- 힘드셨나요/불안하시죠/걱정되시죠의 반복\n- 병원/의료 일반 검사·시술 글에서 억울하다/억울하고 답답하다/손해 보는 느낌 같은 분쟁성 감정 표현'''
new='''- 힘드셨나요/불안하시죠/걱정되시죠의 반복\n- 입니다요/합니다요/됩니다요/좋습니다요/필요합니다요 같은 비표준 어미\n- 병원/의료 일반 검사·시술 글에서 억울하다/억울하고 답답하다/손해 보는 느낌 같은 분쟁성 감정 표현'''
if old not in s:
    raise SystemExit('avoid list marker not found')
s=s.replace(old,new)
# check_all weird endings variables and AI issue
old='''    gyeol_alignment = inspect_writing_gyeol_alignment(body, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, title, keyword)\n\n    # 제목'''
new='''    gyeol_alignment = inspect_writing_gyeol_alignment(body, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, title, keyword)\n    nonstandard_endings = detect_nonstandard_professional_endings(body)\n\n    # 제목'''
if old not in s:
    raise SystemExit('gyeol_alignment marker not found')
s=s.replace(old,new)
# remove premature total/cap block
old='''    if gyeol_alignment.get("issues"):\n        total = min(total, 91)\n        cap_reasons.append("선택한 대표 글결이 본문 흐름에 충분히 반영되지 않아 글결 상한 91점 적용")\n'''
if old not in s:
    raise SystemExit('premature cap marker not found')
s=s.replace(old,'')
# Add nonstandard to AI티 before scores
old='''    if human_issues:\n        for hi in human_issues[:5]:\n            issues["사람화"].append((hi["표현"], f"{hi['설명']} 수정 방향: {hi['수정']}"))\n        ai_score -= min(6, 2 + len(human_issues))\n    scores["AI티"] = max(ai_score, 0)'''
new='''    if human_issues:\n        for hi in human_issues[:5]:\n            issues["사람화"].append((hi["표현"], f"{hi['설명']} 수정 방향: {hi['수정']}"))\n        ai_score -= min(6, 2 + len(human_issues))\n    if nonstandard_endings:\n        issues["AI티"].append(("비표준 어미", "전문직 원고에 맞지 않는 어색한 종결입니다: " + ", ".join(nonstandard_endings)))\n        ai_score -= min(8, 4 + len(nonstandard_endings))\n    scores["AI티"] = max(ai_score, 0)'''
if old not in s:
    raise SystemExit('AI block marker not found')
s=s.replace(old,new)
# Add cap after totals for gyeol and nonstandard
old='''    if selected_intro_type not in detected_intro:\n        total = min(total, 90)\n        cap_reasons.append("선택한 달로썸 도입 방식과 실제 도입 방식이 달라 총점 상한 90점 적용")'''
new='''    if gyeol_alignment.get("issues"):\n        total = min(total, 91)\n        cap_reasons.append("선택한 대표 글결이 본문 흐름에 충분히 반영되지 않아 글결 상한 91점 적용")\n    if nonstandard_endings:\n        total = min(total, 86)\n        cap_reasons.append("입니다요/합니다요/됩니다요 같은 비표준 어미가 감지되어 문체 오류 상한 86점 적용")\n    if selected_intro_type not in detected_intro:\n        total = min(total, 90)\n        cap_reasons.append("선택한 달로썸 도입 방식과 실제 도입 방식이 달라 총점 상한 90점 적용")'''
if old not in s:
    raise SystemExit('cap insert marker not found')
s=s.replace(old,new)
# Claude placeholder
s=s.replace('draft_text = "여기에 GPTs에서 만든 원고를 붙여넣기"','draft_text = "여기에 일반 GPT 또는 GPTs에서 만든 원고를 붙여넣기"')
# Claude package style safety add variables after sensitive_extra maybe
old='''    sensitive_extra = ""\n    if any(x in field for x in ["병원", "의료", "법률", "보험", "금융", "투자", "주식", "코인"]):\n        sensitive_extra = "\\n- 이 분야는 민감 업종이므로 효과·승소·수익·완치·부작용 없음 같은 결과 보장 표현을 절대 추가하지 말 것."'''
new='''    sensitive_extra = ""\n    if any(x in field for x in ["병원", "의료", "법률", "보험", "금융", "투자", "주식", "코인"]):\n        sensitive_extra = "\\n- 이 분야는 민감 업종이므로 효과·승소·수익·완치·부작용 없음 같은 결과 보장 표현을 절대 추가하지 말 것."\n    style_safety_for_claude = professional_style_safety_block(field, writer_perspective, usecase_mode)'''
if old not in s:
    raise SystemExit('claude sensitive marker not found')
s=s.replace(old,new)
old='''[이번 패키지 모드]\n- 모드: {package_mode}\n{boost_rule_text}\n\n[작업 조건]'''
new='''[이번 패키지 모드]\n- 모드: {package_mode}\n{boost_rule_text}\n\n{style_safety_for_claude}\n\n[작업 조건]'''
if old not in s:
    raise SystemExit('claude style insert marker not found')
s=s.replace(old,new)
# UI prompt modes (two occurrences)
s=s.replace('["달로썸 GPTs용", "외부 GPTs용 강제 프롬프트"]', '["일반 GPT용", "달로썸 GPTs용", "외부 GPTs용 강제 프롬프트"]')
s=s.replace('index=0, key="d_prompt_mode"', 'index=0, key="d_prompt_mode"') # no-op explicit
s=s.replace('네가 만든/달로썸 GPTs에는 기본값, 남의 GPTs에는 외부 GPTs용 강제 프롬프트를 사용하세요.', '기본은 일반 GPT용입니다. 달로썸식 기존 말맛이 필요할 때만 달로썸 GPTs용을 선택하세요. 남의 GPTs는 외부 GPTs용 강제 프롬프트를 사용하세요.')
# Labels/captions
s=s.replace('GPTs에 복붙', '일반 GPT/GPTs에 복붙')
s=s.replace('GPTs용 초안 프롬프트 txt 다운로드', 'GPT/GPTs용 초안 프롬프트 txt 다운로드')
s=s.replace('## GPTs용 초안 프롬프트', '## 일반 GPT/GPTs용 초안 프롬프트')
s=s.replace('GPTs 초안 또는 Claude 수정본 붙여넣기', '일반 GPT/GPTs 초안 또는 Claude 수정본 붙여넣기')
s=s.replace('1차: GPTs 초안을 붙여 Claude 패키지를 만듭니다.', '1차: 일반 GPT/GPTs 초안을 붙여 Claude 패키지를 만듭니다.')
s=s.replace('GPTs 초안 붙여넣기 → Claude 자연화 패키지 복사', '일반 GPT/GPTs 초안 붙여넣기 → Claude 자연화 패키지 복사')
s=s.replace('1차: GPTs 초안을 붙여 Claude 패키지를 만들고', '1차: 일반 GPT/GPTs 초안을 붙여 Claude 패키지를 만들고')
# Header version Claude area
s=s.replace('## v10.0.13 Claude 보강·자연화 복붙 패키지','## v10.0.15 Claude 보강·자연화 복붙 패키지')
# README maybe separate
p.write_text(s)
print('patched v1015')
