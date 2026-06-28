from pathlib import Path
p=Path('app.py')
s=p.read_text()

insert_after = 'WRITING_GYEOL_SECONDARY_OPTIONS = ["선택 안함"] + [x for x in WRITING_GYEOL_OPTIONS if x != "자동 추천"]\n'
if 'AUTHOR_NARRATION_OPTIONS' not in s:
    block = r'''

# =========================
# v10.0.21: 작성자 서술 강도
# =========================
AUTHOR_NARRATION_OPTIONS = [
    "자동 추천",
    "중립 정보형",
    "전문가 설명형",
    "대표자 관점형",
    "대표자 직접 서술형",
]
AUTHOR_NARRATION_ALIASES = {
    "": "자동 추천",
    "없음": "자동 추천",
    "원장 직접 서술형": "대표자 직접 서술형",
    "대표원장 직접 서술형": "대표자 직접 서술형",
    "변호사 직접 서술형": "대표자 직접 서술형",
    "대표 직접 서술형": "대표자 직접 서술형",
    "3자 정보형": "중립 정보형",
    "제3자 정보형": "중립 정보형",
}

def normalize_author_narration(mode=""):
    mode = (mode or "").strip()
    mode = AUTHOR_NARRATION_ALIASES.get(mode, mode)
    return mode if mode in AUTHOR_NARRATION_OPTIONS else "자동 추천"

def auto_recommend_author_narration(writer_perspective="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", article_style="", brand_name="", field=""):
    """대표자 주장형은 논지, 작성자 서술 강도는 말투로 분리한다."""
    active = [normalize_writing_gyeol(primary_gyeol)] + clean_secondary_gyeols(secondary_gyeol_1, secondary_gyeol_2)
    wp = writer_perspective or ""
    if "후기" in normalize_article_style(article_style or "") or "기자단" in normalize_article_style(article_style or ""):
        return "중립 정보형"
    if "대표자 주장형" in active or any(w in wp for w in ["대표", "원장", "전문의", "변호사", "세무사", "노무사", "전문업종 대표", "전문업체 대표"]):
        # 업체명/병원명이 있으면 저희/본원까지 허용 가능한 직접 서술형이 유리하다.
        return "대표자 직접 서술형" if brand_name else "대표자 관점형"
    if any(w in wp for w in ["전문가", "의료진", "상담", "담당자", "실무자"]):
        return "전문가 설명형"
    return "중립 정보형"

def resolve_author_narration(mode="", writer_perspective="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", article_style="", brand_name="", field=""):
    m = normalize_author_narration(mode)
    if m == "자동 추천":
        return auto_recommend_author_narration(writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)
    return m

def author_narration_block(mode="", writer_perspective="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", article_style="", brand_name="", field=""):
    resolved = resolve_author_narration(mode, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)
    lines = ["[작성자 서술 강도 · v10.0.21]", f"- 적용 서술 강도: {resolved}"]
    if resolved == "중립 정보형":
        lines += [
            "- 제3자가 정리한 정보성 글처럼 쓰되, 전문성과 신뢰가 느껴지게 한다.",
            "- ‘저는/저희는/본원은’ 같은 1인칭 표현은 쓰지 않는다.",
            "- 병원·업체 장점은 확인된 자료 안에서만 낮은 강도로 연결한다.",
        ]
    elif resolved == "전문가 설명형":
        lines += [
            "- 전문가가 기준을 설명하는 톤으로 쓴다.",
            "- ‘의료진은/전문가는/상담에서는/작업자는’ 같은 표현을 사용할 수 있다.",
            "- 다만 원장·대표가 직접 말하는 듯한 ‘저는/저희는’ 표현은 남발하지 않는다.",
        ]
    elif resolved == "대표자 관점형":
        lines += [
            "- 대표원장·변호사·대표의 판단 기준과 철학이 드러나게 쓴다.",
            "- ‘제가 중요하게 보는 기준은’ 같은 1인칭 표현을 일부 사용할 수 있으나, 전체를 자기소개처럼 만들지 않는다.",
            "- 병원명/업체명이 없으면 ‘저희 병원/본원’ 같은 특정 기관 표현은 쓰지 않는다.",
        ]
    elif resolved == "대표자 직접 서술형":
        lines += [
            "- 대표원장·변호사·대표가 직접 쓴 칼럼처럼 쓴다.",
            "- ‘의료진은’보다 ‘저는’, ‘상담에서는’보다 ‘제가 상담에서’, ‘확인하는 것이 좋습니다’보다 ‘저는 이 부분을 먼저 확인합니다’처럼 판단 주체가 보이게 쓴다.",
            "- 도입 또는 첫 본문에 ‘제가 상담에서 먼저 보는 부분은…’, ‘저는 이 기준을 중요하게 봅니다’처럼 직접 판단 문장을 넣는다.",
        ]
        if brand_name:
            lines.append("- 업체명/병원명이 제공되었으므로 자료 범위 안에서 ‘저희는/저희 병원에서는/본원은’ 표현을 사용할 수 있다.")
        else:
            lines.append("- 업체명/병원명이 없으므로 ‘저희 병원/본원/우리 업체’처럼 특정 기관을 지칭하는 표현은 만들지 않는다. ‘저는/제가’ 중심으로만 쓴다.")
        lines.append("- 실제 경험담·방문후기·치료성과를 지어내지 말고, 상담 기준과 판단 기준만 직접 서술한다.")
    return "\n".join(lines)

def apply_author_narration_to_tone(tone_detail="", mode="", writer_perspective="", primary_gyeol="", secondary_gyeol_1="", secondary_gyeol_2="", article_style="", brand_name="", field=""):
    block = author_narration_block(mode, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)
    base = (tone_detail or "").strip()
    if "[작성자 서술 강도" in base:
        return base
    return (base + "\n\n" + block).strip() if base else block
'''
    s=s.replace(insert_after, insert_after+block)

# Insert author narration into build_draft_prompt string headers after 작성자 관점.
s=s.replace('작성자 관점: {writer_perspective}\n보조 키워드:', '작성자 관점: {writer_perspective}\n작성자 서술 강도: 말투 세부 지시 참조\n보조 키워드:')

# Add author narration block line after style_safety_block in prompt: since tone_detail block is in brand_block, maybe enough but add explicit impossible? brand_block contains. skip.

# UI ②: add selectbox after writer_perspective, before article_style. Ensure only once.
old='''            if r_field == "병원 / 의료":\n                st.caption(f"병원 자동 추천: {r_auto_writer} · 주제/키워드가 바뀌면 세부 진료과 관점도 함께 바뀝니다.")\n            else:\n                st.caption("분야에 맞게 앞에서 선택합니다. 에스테틱 원장으로 고정되지 않게 검수/초안까지 이어집니다.")\n            r_article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="r_article_style")'''
new='''            if r_field == "병원 / 의료":\n                st.caption(f"병원 자동 추천: {r_auto_writer} · 주제/키워드가 바뀌면 세부 진료과 관점도 함께 바뀝니다.")\n            else:\n                st.caption("분야에 맞게 앞에서 선택합니다. 에스테틱 원장으로 고정되지 않게 검수/초안까지 이어집니다.")\n            r_author_narration = st.selectbox("작성자 서술 강도", AUTHOR_NARRATION_OPTIONS, index=0, key="r_author_narration")\n            st.caption("대표자 주장형은 글의 논지, 작성자 서술 강도는 말투입니다. 원장이 직접 쓴 듯한 글은 ‘대표자 직접 서술형’을 선택하세요.")\n            r_article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="r_article_style")'''
if old in s and 'r_author_narration' not in s[s.find(old)-500:s.find(old)+1000]:
    s=s.replace(old,new)

# After r_effective_goal info session set applied? Add tone detail effective before research prompt call.
old='''            st.session_state["r_resolved_primary_gyeol"] = resolve_primary_gyeol(r_primary_gyeol, r_field, r_article_style, r_topic, r_keyword)\n            st.session_state["r_effective_goal"] = r_effective_goal'''
new='''            st.session_state["r_resolved_primary_gyeol"] = resolve_primary_gyeol(r_primary_gyeol, r_field, r_article_style, r_topic, r_keyword)\n            st.session_state["r_author_narration"] = r_author_narration\n            st.session_state["r_effective_goal"] = r_effective_goal'''
s=s.replace(old,new)

# Before build_research_prompt call, insert effective tone assignment maybe right before if homefeed else.
old='''    if is_homefeed_research:\n        research_prompt = build_homefeed_research_prompt('''
new='''    if not is_homefeed_research:\n        r_tone_detail = apply_author_narration_to_tone(r_tone_detail, r_author_narration, r_writer_perspective, r_primary_gyeol, r_secondary_gyeol_1, r_secondary_gyeol_2, r_article_style, r_brand_name, r_field)\n    if is_homefeed_research:\n        research_prompt = build_homefeed_research_prompt('''
s=s.replace(old,new)

# ③ use research inputs: set d_author_narration from session
old='''        d_writer_perspective = st.session_state.get("r_writer_perspective", recommended_writer_perspective(d_field, d_usecase_mode))\n        d_article_style = st.session_state.get("r_article_style", "일반 정보성")'''
new='''        d_writer_perspective = st.session_state.get("r_writer_perspective", recommended_writer_perspective(d_field, d_usecase_mode))\n        d_author_narration = st.session_state.get("r_author_narration", "자동 추천")\n        d_article_style = st.session_state.get("r_article_style", "일반 정보성")'''
s=s.replace(old,new)

# ③ manual add after writer perspective caption block.
old='''            if d_field == "병원 / 의료":\n                st.caption(f"병원 자동 추천: {d_auto_writer} · 주제/키워드에 맞춰 피부과/통증·척추관절/치과/안과 등으로 바뀝니다.")\n            else:\n                st.caption("이 값이 초안 프롬프트와 검수 모드까지 이어집니다.")\n            d_article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="d_article_style")'''
new='''            if d_field == "병원 / 의료":\n                st.caption(f"병원 자동 추천: {d_auto_writer} · 주제/키워드에 맞춰 피부과/통증·척추관절/치과/안과 등으로 바뀝니다.")\n            else:\n                st.caption("이 값이 초안 프롬프트와 검수 모드까지 이어집니다.")\n            d_author_narration = st.selectbox("작성자 서술 강도", AUTHOR_NARRATION_OPTIONS, index=0, key="d_author_narration")\n            st.caption("대표자 주장형은 논지, 작성자 서술 강도는 말투입니다. 직접 칼럼 느낌은 ‘대표자 직접 서술형’." )\n            d_article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="d_article_style")'''
s=s.replace(old,new)

# In d use inputs info add narration maybe no need; but session applied set below.
old='''        st.session_state["applied_tone_detail"] = d_tone_detail\n        st.session_state["applied_content_goal"] = d_content_goal'''
new='''        d_tone_detail = apply_author_narration_to_tone(d_tone_detail, d_author_narration, d_writer_perspective, d_primary_gyeol, d_secondary_gyeol_1, d_secondary_gyeol_2, d_article_style, d_brand_name, d_field)\n        st.session_state["applied_author_narration"] = d_author_narration\n        st.session_state["applied_tone_detail"] = d_tone_detail\n        st.session_state["applied_content_goal"] = d_content_goal'''
s=s.replace(old,new)

# if use research inputs before build_draft_prompt: d_tone_detail from session not yet enhanced; above applied set only after? Need check. For use inputs, d_tone_detail is session r_tone_detail maybe not enhanced. We'll add after variable definition.
old='''        d_tone_detail = st.session_state.get("r_tone_detail", default_tone_by_article_style(d_article_style, d_writer_perspective))'''
new='''        d_tone_detail = st.session_state.get("r_tone_detail", default_tone_by_article_style(d_article_style, d_writer_perspective))\n        d_tone_detail = apply_author_narration_to_tone(d_tone_detail, d_author_narration, d_writer_perspective, d_primary_gyeol, d_secondary_gyeol_1, d_secondary_gyeol_2, d_article_style, d_brand_name, d_field)'''
s=s.replace(old,new)

# ⑧ use_flow auto: set author from applied. Insert after writer perspective.
old='''            writer_perspective = st.selectbox("작성자 관점", WRITER_PERSPECTIVES, index=writer_index(field, selected_usecase_mode, auto_writer_perspective))\n            article_style = st.session_state.get("applied_article_style", st.session_state.get("r_article_style", "일반 정보성"))'''
new='''            writer_perspective = st.selectbox("작성자 관점", WRITER_PERSPECTIVES, index=writer_index(field, selected_usecase_mode, auto_writer_perspective))\n            author_narration = st.session_state.get("applied_author_narration", st.session_state.get("r_author_narration", "자동 추천"))\n            article_style = st.session_state.get("applied_article_style", st.session_state.get("r_article_style", "일반 정보성"))'''
s=s.replace(old,new)

# ⑧ manual add after writer_perspective.
old='''            writer_perspective = st.selectbox("작성자 관점", WRITER_PERSPECTIVES, index=writer_index(field, st.session_state.get("r_usecase_mode", "블로그 정보성")))\n            article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="check_article_style_manual")'''
new='''            writer_perspective = st.selectbox("작성자 관점", WRITER_PERSPECTIVES, index=writer_index(field, st.session_state.get("r_usecase_mode", "블로그 정보성")))\n            author_narration = st.selectbox("작성자 서술 강도", AUTHOR_NARRATION_OPTIONS, index=0, key="check_author_narration_manual")\n            st.caption("원장이 직접 쓴 듯한 문체가 필요하면 ‘대표자 직접 서술형’을 선택하세요.")\n            article_style = st.selectbox("글 성격", ARTICLE_STYLES, index=0, key="check_article_style_manual")'''
s=s.replace(old,new)

# ⑧ st.info add author narration.
s=s.replace('대표글결={resolve_primary_gyeol(primary_gyeol, field, article_style, check_topic_for_claude if \'check_topic_for_claude\' in globals() else st.session_state.get("r_topic", ""), keyword)} / 업체명=', '대표글결={resolve_primary_gyeol(primary_gyeol, field, article_style, check_topic_for_claude if \'check_topic_for_claude\' in globals() else st.session_state.get("r_topic", ""), keyword)} / 서술강도={resolve_author_narration(author_narration, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)} / 업체명=')

# ⑧ apply narration to tone before Claude package call
old='''    check_review_note_for_claude = f"검수 전 단계입니다. 사용처={selected_usecase_mode}, 분야={field}, 키워드={keyword}, 업체명={brand_name or '없음'}, 전환목표={conversion_goal or '없음'}, 원고목적={content_goal or '자동 생성'} 조건을 유지하세요." + ("\n" + "\n".join(extra_claude_notes) if extra_claude_notes else "")'''
new='''    tone_detail = apply_author_narration_to_tone(tone_detail, author_narration, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)\n    check_review_note_for_claude = f"검수 전 단계입니다. 사용처={selected_usecase_mode}, 분야={field}, 키워드={keyword}, 업체명={brand_name or '없음'}, 전환목표={conversion_goal or '없음'}, 원고목적={content_goal or '자동 생성'}, 작성자서술강도={resolve_author_narration(author_narration, writer_perspective, primary_gyeol, secondary_gyeol_1, secondary_gyeol_2, article_style, brand_name, field)} 조건을 유지하세요." + ("\n" + "\n".join(extra_claude_notes) if extra_claude_notes else "")'''
s=s.replace(old,new)

# add author narration to check report? Find build_review_share_report lines, add parameter? Too much. Skip.

# Modify writing_gyeol_mandatory direct example for 대표자 주장형 to not force 저는 unless direct? Since tone block controls. Slight change
s=s.replace("- 예시 방향: ‘제가 상담에서 먼저 보는 기준은…’, ‘의료진 입장에서 중요하게 보는 것은…’, ‘현장에서 자주 듣는 질문은…’처럼 판단 기준을 드러낸다.", "- 예시 방향: ‘의료진 입장에서 중요하게 보는 것은…’, ‘현장에서 자주 듣는 질문은…’, 직접 서술형일 때는 ‘제가 상담에서 먼저 보는 기준은…’처럼 판단 기준을 드러낸다.")

# Add author narration to report lines where input conditions built? Search add lines. We'll add minimal in create_review_share_report call? Let's skip due complexity.

# README update
Path('README.md').write_text('# 달로썸 원고 검수기 v10.0.21\n\n작성자 서술 강도 패치. 대표자 주장형(논지)과 대표자 직접 서술형(말투)을 분리했습니다. 일반 정보형, 전문가 설명형, 대표자 관점형, 대표자 직접 서술형을 선택해 원장/변호사/대표가 직접 쓴 듯한 원고와 제3자 정보성 원고를 구분할 수 있습니다.\n', encoding='utf-8')

p.write_text(s)
