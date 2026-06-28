from pathlib import Path
p=Path('/mnt/data/v1019_work/app.py')
s=p.read_text()

# 1) body label cleaner + extract_title cleanup
old='''def extract_title(title_input, draft):
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
'''
new='''def clean_body_label_text(text=""):
    """붙여넣기 원고 맨 앞의 '본문:' 라벨이 첫문장으로 잡히지 않게 제거한다."""
    text = (text or "").strip()
    text = re.sub(r"^본문\s*[:：]\s*", "", text).strip()
    return text


def extract_title(title_input, draft):
    title_input = (title_input or "").strip()
    draft = draft or ""
    if title_input:
        title = re.sub(r"^(최종\s*)?제목\s*[:：]\s*", "", title_input).strip()
        return title, clean_body_label_text(draft), "제목 입력칸"

    lines = [l.strip() for l in draft.splitlines() if l.strip()]
    if not lines:
        return "", "", "없음"
    first = lines[0]
    if first.startswith("#"):
        return first.lstrip("#").strip(), clean_body_label_text("\n".join(lines[1:])), "본문 첫 줄"
    m = re.match(r"^(?:최종\s*)?제목\s*[:：]\s*(.+)$", first)
    if m:
        return m.group(1).strip(), clean_body_label_text("\n".join(lines[1:])), "본문 제목표기"
    if len(first) <= 40 and not first.endswith(("다.", "요.", "니다.", "죠.", "?")):
        return first, clean_body_label_text("\n".join(lines[1:])), "본문 첫 줄 자동추출"
    return "", clean_body_label_text(draft), "없음"
'''
if old not in s:
    raise SystemExit('extract_title block not found')
s=s.replace(old,new)

# 2) humanization replacements: avoid '하는 데 판단하는 데' and overly awkward substitutions
s=s.replace('''        "도움이 될 수 있습니다": "판단하는 데 참고가 됩니다",''','''        "도움이 될 수 있습니다": "참고할 수 있습니다",''')
old='''    s = s.replace("도움이 될 수 있습니다", "판단하는 데 참고가 됩니다")
    s = s.replace("도움이 됩니다", "판단하는 데 참고가 됩니다")
    s = s.replace("중요합니다", "놓치기 쉽습니다")
    s = s.replace("필요합니다", "먼저 확인해야 합니다")
'''
new='''    # '선택을 하는 데 도움이 됩니다'처럼 이미 '하는 데'가 있는 문장은
    # '판단하는 데'를 덧붙이지 않는다. 자연스러운 참고 표현으로만 낮춘다.
    s = re.sub(r"(하는\s*데)\s*도움이\s*될\s*수\s*있습니다", r"\\1 참고할 수 있습니다", s)
    s = re.sub(r"(하는\s*데)\s*도움이\s*됩니다", r"\\1 참고가 됩니다", s)
    s = s.replace("도움이 될 수 있습니다", "참고할 수 있습니다")
    s = s.replace("도움이 됩니다", "참고가 됩니다")
    s = s.replace("중요합니다", "놓치기 쉽습니다")
    s = s.replace("필요합니다", "먼저 확인해야 합니다")
    s = re.sub(r"하는 데\s*판단하는 데", "판단하는 데", s)
'''
if old not in s:
    raise SystemExit('humanize replacements block not found')
s=s.replace(old,new)

# 3) prevent bad suggestions from being added
old='''    def add(reason, before, after):
        before = (before or "").strip()
        after = (after or "").strip()
        if not before or not after or before == after:
            return
        key = (reason, before[:80], after[:80])
        if key in seen:
            return
        seen.add(key)
        suggestions.append({"수정 이유": reason, "수정 전": before, "수정 후": after})
'''
new='''    def add(reason, before, after):
        before = (before or "").strip()
        after = (after or "").strip()
        if not before or not after or before == after:
            return
        # 자동 제안이 원문보다 어색해지는 대표 오류를 차단한다.
        bad_after_patterns = ["하는 데 판단하는 데", "데 데", "먼저 확인이 먼저", "확인해야 합니다 확인"]
        if any(pat in after for pat in bad_after_patterns):
            return
        key = (reason, before[:80], after[:80])
        if key in seen:
            return
        seen.add(key)
        suggestions.append({"수정 이유": reason, "수정 전": before, "수정 후": after})
'''
if old not in s:
    raise SystemExit('add suggestion block not found')
s=s.replace(old,new)

# 4) total consistency: one missing specialty requirement should not still be 100
old='''    if specialty_profile and len(specialty_missing) >= 4:
        total = min(total, 89)
        cap_reasons.append(f"{specialty_profile.get('display')} 세부 업종 필수 기준이 많이 빠져 납품 상한 89점 적용")
    if delivery_risks:
'''
new='''    if specialty_profile and len(specialty_missing) >= 4:
        total = min(total, 89)
        cap_reasons.append(f"{specialty_profile.get('display')} 세부 업종 필수 기준이 많이 빠져 납품 상한 89점 적용")
    elif specialty_profile and len(specialty_missing) >= 2:
        total = min(total, 92)
        cap_reasons.append(f"{specialty_profile.get('display')} 세부 업종 필수 기준 보강 항목이 남아 납품 상한 92점 적용")
    elif specialty_profile and len(specialty_missing) == 1:
        total = min(total, 94)
        cap_reasons.append(f"{specialty_profile.get('display')} 세부 업종 필수 기준 1개 보강 여지가 있어 100점 판정은 제한")
    if delivery_risks:
'''
if old not in s:
    raise SystemExit('specialty cap block not found')
s=s.replace(old,new)

# 5) final delivery grade: avoid downgrading solely because optional sentence suggestions exist, but respect total score
old='''def final_delivery_grade(total=0, risks=None, human_issues=None, sentence_suggestions=None):
    risks = risks or []
    human_issues = human_issues or []
    sentence_suggestions = sentence_suggestions or []
    high = sum(1 for r in risks if r.get("등급") == "높음")
    if high:
        return "전면 수정 필요", "높음 등급 납품 리스크가 있어 그대로 제출하면 위험합니다."
    if total >= 95 and not human_issues and not sentence_suggestions:
        return "바로 납품 가능", "오탈자와 줄바꿈만 확인하면 됩니다."
    if total >= 92:
        return "소폭 수정 후 납품 가능", "첫문장, 제목 말맛, 반복 표현만 정리하면 제출권입니다."
'''
new='''def final_delivery_grade(total=0, risks=None, human_issues=None, sentence_suggestions=None):
    risks = risks or []
    human_issues = human_issues or []
    sentence_suggestions = sentence_suggestions or []
    high = sum(1 for r in risks if r.get("등급") == "높음")
    if high:
        return "전면 수정 필요", "높음 등급 납품 리스크가 있어 그대로 제출하면 위험합니다."
    if total >= 95 and not human_issues:
        if sentence_suggestions:
            return "바로 납품 가능", "강한 리스크는 없습니다. 자동 문장 제안은 선택사항이므로 오탈자와 줄바꿈만 확인하세요."
        return "바로 납품 가능", "오탈자와 줄바꿈만 확인하면 됩니다."
    if total >= 92:
        return "소폭 수정 후 납품 가능", "첫문장, 제목 말맛, 반복 표현만 정리하면 제출권입니다."
'''
if old not in s:
    raise SystemExit('final_delivery_grade block not found')
s=s.replace(old,new)

# 6) Add TXT download for Korean teacher, not just CSV
old='''        if rows:
            st.download_button(
                "국어선생님 검수 결과 CSV 다운로드",
                data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
                file_name="korean_teacher_review.csv",
                mime="text/csv",
                key="download_korean_teacher_csv",
            )
'''
new='''        kt_export_lines = [
            "# 달로썸 ⑩ 국어선생님 퇴고 결과",
            "",
            f"- 상품 유형: {kt_product}",
            f"- 분야: {kt_field}",
            f"- 문체: {kt_style}",
            f"- 기자단 체험 여부: {kt_experience}",
            f"- 점수: {kt_result.get('점수', 0)}",
            f"- 등급: {kt_result.get('등급', '-')}",
            "",
            "## 문장별 검수 결과",
        ]
        if rows:
            for i, row in enumerate(rows, 1):
                kt_export_lines += [
                    f"{i}. [{row.get('구분','')}]",
                    f"- 어색한 문장: {row.get('어색한 문장','')}",
                    f"- 문제 이유: {row.get('문제 이유','')}",
                    f"- 수정 문장: {row.get('수정 문장','')}",
                    "",
                ]
            st.download_button(
                "국어선생님 검수 결과 CSV 다운로드",
                data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
                file_name="korean_teacher_review.csv",
                mime="text/csv",
                key="download_korean_teacher_csv",
            )
        else:
            kt_export_lines.append("- 강하게 걸리는 문장론/이상 문체 문제는 많지 않습니다.")
        kt_export_lines += ["", "## 최종 문단", kt_result.get("최종문단", "")]
        st.download_button(
            "국어선생님 공유용 TXT 다운로드",
            data="\n".join(kt_export_lines).encode("utf-8-sig"),
            file_name="korean_teacher_review_share.txt",
            mime="text/plain",
            key="download_korean_teacher_txt",
        )
'''
if old not in s:
    raise SystemExit('korean teacher csv block not found')
s=s.replace(old,new)

# 7) Version labels v10.0.18 -> v10.0.19 in visible header if present
s=s.replace('📝 달로썸 원고 검수기 v10.0.18','📝 달로썸 원고 검수기 v10.0.19')
s=s.replace('v10.0.18','v10.0.19')

p.write_text(s)
print('patched v1019')
