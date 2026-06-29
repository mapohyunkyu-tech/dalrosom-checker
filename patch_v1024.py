from pathlib import Path
import re
p = Path('app.py')
s = p.read_text(encoding='utf-8')
# version bumps visible strings
s = s.replace('달로썸 원고 검수기 v10.0.23', '달로썸 원고 검수기 v10.0.24')
s = s.replace('## v10.0.23 Claude 보강·자연화 복붙 패키지', '## v10.0.24 Claude 보강·자연화 복붙 패키지')
s = s.replace('# v10.0.23: 작성자 서술 강도', '# v10.0.24: 작성자 서술 강도/반복 방지 보강')
s = s.replace('[작성자 서술 강도 · v10.0.23]', '[작성자 서술 강도 · v10.0.24]')

insert_after = '''def apply_author_narration_to_tone(tone_detail="", mode="", writer_perspective="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", article_style="", brand_name="", field=""):\n    block = author_narration_block(mode, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)\n    base = (tone_detail or "").strip()\n    if "[작성자 서술 강도" in base:\n        return base\n    return (base + "\\n\\n" + block).strip() if base else block\n'''
helper_block = r'''

# =========================
# v10.0.24: 반복 방지·직접 서술 안정화 패치
# =========================
def has_brand_context(brand_name="", brand_intensity="업체명 없음", homepage_mode="홈페이지 정보 없음", homepage_info=""):
    """업체명/브랜드명이 실제로 주어진 경우에만 기관 1인칭을 허용한다."""
    return bool((brand_name or "").strip()) and (brand_intensity or "업체명 없음") != "업체명 없음"


def detect_no_brand_institution_phrases(body="", brand_name="", brand_intensity="업체명 없음"):
    """업체명 없음 상태에서 저희 병원/본원 같은 임의 기관 표현을 감지한다."""
    if has_brand_context(brand_name, brand_intensity):
        return []
    text = body or ""
    patterns = [
        "저희 병원", "저희 의원", "저희 클리닉", "저희 한의원", "저희 치과", "저희 안과",
        "본원", "당원", "우리 병원", "우리 의원", "우리 클리닉", "우리 업체", "저희 업체",
        "저희 법무법인", "저희 사무실", "저희 센터", "저희 학원", "저희 매장", "저희 샵",
        "저희는"
    ]
    found = []
    for pat in patterns:
        if pat in text and pat not in found:
            found.append(pat)
    return found


def inspect_author_narration_alignment(body="", mode="자동 추천", writer_perspective="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", article_style="", brand_name="", brand_intensity="업체명 없음", field=""):
    """대표자 직접 서술형이 실제 원고에 반영됐는지 검수한다."""
    resolved = resolve_author_narration(mode, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)
    text = body or ""
    direct_markers = [
        "저는", "제가", "제 기준", "제가 상담", "제가 먼저", "제가 중요", "제가 보는", "저는 이", "저는 상담", "저는 무리"
    ]
    third_person_markers = [
        "의료진은", "전문가는", "전문가들은", "상담 때는", "상담에서는", "시술한 의료기관", "의료기관에 확인", "일반적으로는", "확인하는 것이 좋습니다"
    ]
    direct_count = sum(text.count(m) for m in direct_markers)
    third_count = sum(text.count(m) for m in third_person_markers)
    institution_hits = detect_no_brand_institution_phrases(text, brand_name, brand_intensity)
    issues = []
    if institution_hits:
        issues.append({
            "type": "no_brand_institution",
            "level": "높음",
            "title": "업체명 없음 상태의 기관 표현",
            "message": "업체명/병원명이 없는데 특정 기관을 지칭하는 표현이 들어갔습니다: " + ", ".join(institution_hits[:8]),
            "fix": "‘저희 병원/본원/저희는’은 삭제하고 ‘저는/제가/상담에서는’ 또는 중립 문장으로 바꾸세요."
        })
    if resolved == "대표자 직접 서술형":
        if direct_count < 2:
            issues.append({
                "type": "direct_voice_weak",
                "level": "중간",
                "title": "대표자 직접 서술 약함",
                "message": "대표자 직접 서술형인데 ‘저는/제가’ 중심의 판단 문장이 부족합니다.",
                "fix": "도입 또는 첫 본문에 ‘제가 상담에서 먼저 보는 기준은…’, ‘저는 이 부분을 중요하게 봅니다’ 같은 문장을 1~2개 넣으세요."
            })
        if third_count >= 3:
            issues.append({
                "type": "third_person_tone",
                "level": "중간",
                "title": "3자 정보글 느낌 강함",
                "message": "대표자 직접 서술형인데 ‘의료진은/상담에서는/일반적으로는’ 같은 제3자 표현이 많습니다.",
                "fix": "판단 주체가 필요한 문장은 ‘제가 상담에서…’, ‘저는 …을 먼저 봅니다’로 바꾸세요."
            })
        if direct_count > 10:
            issues.append({
                "type": "direct_voice_overuse",
                "level": "낮음",
                "title": "저는/제가 반복 과다",
                "message": f"직접 서술 표현이 {direct_count}회로 많아 자기소개처럼 느껴질 수 있습니다.",
                "fix": "핵심 판단 문장에만 1인칭을 남기고 나머지는 중립 설명문으로 정리하세요."
            })
    elif resolved in ["중립 정보형", "전문가 설명형"]:
        if sum(text.count(m) for m in ["저는", "제가", "저희는"]) >= 4:
            issues.append({
                "type": "first_person_too_much",
                "level": "낮음",
                "title": "1인칭 표현 과다",
                "message": f"서술 강도는 {resolved}인데 1인칭 표현이 많습니다.",
                "fix": "중립 정보형/전문가 설명형에서는 1인칭을 줄이고 기준 설명 중심으로 바꾸세요."
            })
    return {"resolved": resolved, "direct_count": direct_count, "third_count": third_count, "institution_hits": institution_hits, "issues": issues}


def intro_body_variation_block(topic="", keyword="", intro_type="자동 추천", first_sentence_type="자동 추천", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", field="", article_style=""):
    """같은 주제 반복 생성 시 도입과 본문 흐름이 복붙처럼 나오는 것을 줄이는 지시."""
    resolved = resolve_primary_gyeol(primary_gyeol, field, article_style, topic, keyword)
    seconds = clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)
    active = [resolved] + seconds
    flows = [
        "A형: 고민 → 원리/개념 → 선택 기준 → 주의사항 → 상담 필요성",
        "B형: 흔한 오해 → 실제 판단 기준 → 체크리스트 → 유지·관리 기준",
        "C형: 상담 장면 → 부위/상황별 판단 → 비용·샷 수·장비 기준 → 마무리",
        "D형: 가격·후기 비교에서 생기는 혼란 → 차이가 나는 이유 → 확인 기준 → 문의 전 정리",
        "E형: 실패/불만족이 생기는 이유 → 사전 확인 기준 → 전문가 판단 → 관리 철학"
    ]
    if "대표자 주장형" in active:
        flows.insert(0, "대표자형: 제가 먼저 보는 기준 → 왜 그 기준이 중요한지 → 독자가 확인할 질문 → 신중한 상담 유도")
    if "선택 기준형" in active or "병원/업체 선택 기준형" in active:
        flows.insert(0, "선택기준형: 비교가 어려운 이유 → 고르면 안 되는 기준 → 확인 기준 3~5개 → 상담 전 질문")
    if "오해 반박형" in active:
        flows.insert(0, "오해반박형: 흔한 착각 1개 → 실제로 다른 이유 → 상황별 기준 → 안전한 마무리")
    flow_text = "\n".join([f"- {x}" for x in flows[:5]])
    banned_starts = [
        "~을 알아보다 보면", "~을 고민하는 분들이", "~ 전 확인해야 할 것은", "많은 분들이 ~라고 생각합니다",
        "가장 많이 묻는 질문은", "~는 단순히 ~가 아닙니다", "오늘은", "이번 글에서는", "알아보겠습니다"
    ]
    banned_text = ", ".join(banned_starts)
    return f"""[반복 방지·도입/본문 변주 지시 · v10.0.24]
- 같은 주제 원고가 반복 생산될 수 있으므로 첫 문장과 본문 순서를 매번 안전한 검색형 공식으로 고정하지 않는다.
- 선택 도입 방식은 유지하되 첫 문장은 장면, 질문, 반박, 판단 기준, 체크 항목 중 하나로 변주한다.
- 첫 문장 금지 패턴: {banned_text}
- 핵심 키워드가 ‘{keyword or topic}’라도 첫 문장을 반드시 키워드로 시작할 필요는 없다. 단, 첫 문단 안에는 자연스럽게 1회 연결한다.
- 본문은 아래 흐름 중 하나를 골라 쓰되, 매번 ‘개념 설명 → 장점 → 체크리스트 → 마무리’로만 쓰지 않는다.
{flow_text}
- 소제목도 ‘{keyword or topic}란 무엇인가요/선택 기준/마무리하며’처럼 흔한 형태만 반복하지 말고, 본문 판단 기준이 보이게 쓴다."""


def no_brand_institution_guard_block(brand_name="", brand_intensity="업체명 없음"):
    if has_brand_context(brand_name, brand_intensity):
        return f"[업체명/브랜드명 반영]\n- 업체명/브랜드명 ‘{brand_name}’이 제공되었으므로 반영 강도 ‘{brand_intensity}’ 안에서만 사용한다."
    return """[업체명 없음 하드 규칙 · v10.0.24]
- 업체명/병원명/브랜드명이 없으므로 ‘저희 병원’, ‘본원’, ‘저희 클리닉’, ‘저희 의원’, ‘저희는’, ‘우리 업체’ 같은 특정 기관 표현을 쓰지 않는다.
- 대표자 직접 서술형이어도 기관 1인칭이 아니라 ‘저는/제가’ 중심으로만 쓴다.
- 마무리도 ‘저희 병원으로 문의’가 아니라 ‘상담에서 부위별 계획을 확인해보는 것이 좋습니다’처럼 확인 행동으로 연결한다."""


def revision_integrity_guard_block(author_narration="자동 추천", writer_perspective="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", article_style="", brand_name="", brand_intensity="업체명 없음", field=""):
    resolved = resolve_author_narration(author_narration, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)
    lines = [
        "[수정본 조건 이탈 방지 · v10.0.24]",
        "- Claude/국어선생님/사람화 수정 후에도 주제, 키워드, 글 성격, 글결, 작성자 관점, 전환 목표를 바꾸지 않는다.",
        "- 문장을 자연스럽게 다듬더라도 핵심 키워드, 선택 기준, 상담 필요성, 주의사항을 삭제하지 않는다.",
        "- 자연화 과정에서 새 경험담, 새 병원 장점, 새 성과 사례를 추가하지 않는다.",
        f"- 작성자 서술 강도는 ‘{resolved}’로 유지한다."
    ]
    if resolved == "대표자 직접 서술형":
        lines.append("- 대표자 직접 서술형 원고는 ‘저는/제가’ 중심의 판단 주체를 유지하고, 중립 정보글처럼 3자화하지 않는다.")
    if not has_brand_context(brand_name, brand_intensity):
        lines.append("- 업체명 없음 조건이므로 수정 과정에서 ‘저희 병원/본원/저희는/우리 업체’를 새로 만들지 않는다.")
    return "\n".join(lines)
'''
if helper_block.strip() not in s:
    s = s.replace(insert_after, insert_after + helper_block)
else:
    print('helper block already present')

# check_all signature and call additions
old_sig = 'def check_all(title, body, keyword, field, purpose, writer_perspective, selected_intro_type, selected_title_type, ending_type, include_philosophy, philosophy_text, min_len, max_len, first_sentence_type="자동 추천", b_concern_text="", selected_voice_type="자동 추천", selected_usecase_mode="블로그 정보성", article_style="", homepage_mode="홈페이지 정보 없음", homepage_info="", brand_name="", conversion_goal="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2=""):'
new_sig = 'def check_all(title, body, keyword, field, purpose, writer_perspective, selected_intro_type, selected_title_type, ending_type, include_philosophy, philosophy_text, min_len, max_len, first_sentence_type="자동 추천", b_concern_text="", selected_voice_type="자동 추천", selected_usecase_mode="블로그 정보성", article_style="", homepage_mode="홈페이지 정보 없음", homepage_info="", brand_name="", conversion_goal="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", author_narration="자동 추천", brand_intensity="업체명 없음"):'
s = s.replace(old_sig, new_sig)
# issues keys add 조건이탈? use 작성자 관점 & 위험표현
# delivery_risks call pass gyeol args
old = 'delivery_risks = detect_delivery_risks(title, body, keyword, field, purpose, writer_perspective, selected_intro_type, selected_usecase_mode, homepage_mode, homepage_info, brand_name, article_style, conversion_goal)'
new = 'delivery_risks = detect_delivery_risks(title, body, keyword, field, purpose, writer_perspective, selected_intro_type, selected_usecase_mode, homepage_mode, homepage_info, brand_name, article_style, conversion_goal, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2)'
s = s.replace(old, new)
# add author alignment after gyeol_alignment
anchor = '    gyeol_alignment = inspect_writing_gyeol_alignment(body, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, title, keyword)\n    nonstandard_endings = detect_nonstandard_professional_endings(body)'
replacement = '    gyeol_alignment = inspect_writing_gyeol_alignment(body, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, title, keyword)\n    author_alignment = inspect_author_narration_alignment(body, author_narration, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, brand_intensity, field)\n    nonstandard_endings = detect_nonstandard_professional_endings(body)'
s = s.replace(anchor, replacement)
# add no-brand risk in detect_delivery_risks before common returns maybe after unsupported claim check
anchor = '    if detect_unsupported_homepage_claims(body, homepage_mode, homepage_info):\n        add("높음", "자료 없는 장점 생성", "홈페이지·공식자료 없이 경력, 철학, 시스템, 1위성 장점이 만들어진 흔적이 있습니다.", "확인된 자료가 없으면 장점 문장을 삭제하고 ‘확인 기준’ 중심으로 마무리하세요.")'
replacement = anchor + '\n    no_brand_hits = detect_no_brand_institution_phrases(text, brand_name, "업체명 없음")\n    if no_brand_hits and not (brand_name or "").strip():\n        add("높음", "업체명 없음 기관 표현", "업체명/병원명이 없는데 특정 기관 표현이 들어갔습니다: " + ", ".join(no_brand_hits[:8]), "저희 병원/본원/저희는을 삭제하고 저는/제가 또는 중립 표현으로 바꾸세요.")'
s = s.replace(anchor, replacement)
# Add author alignment issue handling in persona section after forced_doctor_tone maybe before scores
anchor = '    if forced_doctor_tone:\n        issues["작성자 관점"].append(("원장톤 억지 삽입", "대표원장/전문의 말투가 실제 상담 질문 없이 장식처럼 들어간 부분이 있습니다: " + ", ".join(forced_doctor_tone[:4])))\n        persona_score -= 4'
replacement = anchor + '\n    if author_alignment.get("issues"):\n        for ai in author_alignment.get("issues", [])[:5]:\n            issues["작성자 관점"].append((ai.get("title", "작성자 서술 강도"), ai.get("message", "") + " 수정 방향: " + ai.get("fix", "")))\n        hard_author_issues = [x for x in author_alignment.get("issues", []) if x.get("level") == "높음"]\n        persona_score -= min(6, 2 + len(author_alignment.get("issues", [])) + len(hard_author_issues))'
s = s.replace(anchor, replacement)
# Add danger expression for no brand in 위험표현 after unsupported_homepage_claims
anchor = '    if unsupported_homepage_claims:\n        issues["위험표현"].append(("자료 없는 장점·철학", "홈페이지/공식 자료 없이 병원·업체 장점이나 철학처럼 보이는 표현이 들어갔습니다: " + ", ".join(unsupported_homepage_claims[:6])))\n        comp_score -= min(8, 4 + len(unsupported_homepage_claims))'
replacement = anchor + '\n    if author_alignment.get("institution_hits"):\n        issues["위험표현"].append(("업체명 없음 기관 표현", "업체명/병원명 없음 조건인데 기관 표현이 들어갔습니다: " + ", ".join(author_alignment.get("institution_hits")[:8])))\n        comp_score -= min(8, 4 + len(author_alignment.get("institution_hits")))'
s = s.replace(anchor, replacement)
# Add caps before min len caps
anchor = '    if conversion_ending_weak(body, article_style, brand_name, conversion_goal, field):\n        total = min(total, 90)\n        cap_reasons.append("매출 전환형인데 마무리 병원/업체 장점 연결이 약해 총점 상한 90점 적용")'
replacement = anchor + '\n    if author_alignment.get("institution_hits"):\n        total = min(total, 86)\n        cap_reasons.append("업체명 없음 조건에서 저희 병원/본원/저희는 표현이 감지되어 총점 상한 86점 적용")\n    if any(x.get("type") == "direct_voice_weak" for x in author_alignment.get("issues", [])):\n        total = min(total, 90)\n        cap_reasons.append("대표자 직접 서술형인데 저는/제가 중심의 판단 문장이 부족해 총점 상한 90점 적용")'
s = s.replace(anchor, replacement)
# meta add author alignment
old = '        "writing_gyeol": gyeol_alignment,\n        "style_ending_alignment": style_ending_alignment,\n    }'
new = '        "writing_gyeol": gyeol_alignment,\n        "author_narration": author_alignment,\n        "style_ending_alignment": style_ending_alignment,\n    }'
s = s.replace(old, new)
# Update check_all call with author_narration and brand_intensity
old = 'selected_voice_type, selected_usecase_mode, article_style, homepage_mode, homepage_info, brand_name, conversion_goal, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2\n        )'
new = 'selected_voice_type, selected_usecase_mode, article_style, homepage_mode, homepage_info, brand_name, conversion_goal, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, author_narration, brand_intensity\n        )'
s = s.replace(old, new, 1)
# Add prompt blocks variables in research and draft
anchor = '    gyeol_block = writing_gyeol_prompt_block(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword)\n    style_safety_block = professional_style_safety_block(field, writer_perspective, usecase_mode)'
replacement = '    gyeol_block = writing_gyeol_prompt_block(primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style, topic, keyword)\n    variation_block = intro_body_variation_block(topic, keyword, intro_type, first_sentence_type, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, field, article_style)\n    no_brand_guard = no_brand_institution_guard_block(brand_name, brand_intensity)\n    revision_guard = revision_integrity_guard_block("자동 추천", writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, brand_intensity, field)\n    style_safety_block = professional_style_safety_block(field, writer_perspective, usecase_mode)'
# replace first occurrence for research and second for draft? Since same anchor twice, replace all.
s = s.replace(anchor, replacement)
# Insert variables into research prompt after gyeol block
old = '{gyeol_block}\n{brand_block}\n{length_plan}'
new = '{gyeol_block}\n{variation_block}\n{no_brand_guard}\n{revision_guard}\n{brand_block}\n{length_plan}'
s = s.replace(old, new, 1)
# Insert variables into draft prompt after gyeol block & before style
old = '{gyeol_block}\n\n{style_safety_block}'
new = '{gyeol_block}\n\n{variation_block}\n\n{no_brand_guard}\n\n{revision_guard}\n\n{style_safety_block}'
s = s.replace(old, new, 1)
# Add to mode important maybe no need
# Claude naturalize: variables and boost rules
anchor = '    style_safety_for_claude = professional_style_safety_block(field, writer_perspective, usecase_mode)\n\n    brand_rule = ""'
replacement = '    style_safety_for_claude = professional_style_safety_block(field, writer_perspective, usecase_mode)\n    no_brand_guard_for_claude = no_brand_institution_guard_block(brand_name, brand_intensity)\n    revision_guard_for_claude = revision_integrity_guard_block("자동 추천", writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, brand_intensity, field)\n\n    brand_rule = ""'
s = s.replace(anchor, replacement)
old = '{style_safety_for_claude}\n\n[작업 조건]'
new = '{style_safety_for_claude}\n\n{no_brand_guard_for_claude}\n\n{revision_guard_for_claude}\n\n[작업 조건]'
s = s.replace(old, new)
# Improve brand_rule no brand in Claude naturalize
s = s.replace('brand_rule = "\\n- 업체명/브랜드명이 없으면 저희/본원/우리 업체/문의 유도 문장을 새로 만들지 말 것."', 'brand_rule = "\\n- 업체명/브랜드명이 없으면 저희 병원/본원/저희는/우리 업체 같은 기관 표현과 과한 문의 유도 문장을 새로 만들지 말 것."')
# Add safety to old build_claude_prompt if possible after homepage guard maybe simple string replacement at 금지 list already includes. Append direct.
s = s.replace('- 홈페이지 정보가 없는데 “저희 병원은”, “본원은”, “저희는”, “우리 병원은” 등 기관 철학·장점을 지어내기 금지\n', '- 홈페이지 정보가 없는데 “저희 병원은”, “본원은”, “저희는”, “우리 병원은” 등 기관 철학·장점을 지어내기 금지\n- 대표자 직접 서술형 조건이 있으면 문장을 다듬어도 “저는/제가” 중심의 판단 주체를 3자 정보글로 바꾸지 말 것\n')
# UI label v10.0.23 occurrences maybe page still? replace visible remaining v10.0.23 to v10.0.24 except comments? okay global for visible is safe now
s = s.replace('v10.0.23', 'v10.0.24')
# But comments about v10.0.23 changelog become v10.0.24. Accept.
p.write_text(s, encoding='utf-8')
print('patched app.py')
