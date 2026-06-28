from pathlib import Path
s=Path('app.py').read_text()
checks = {
    'kt_default_professional': 'kt_product = st.selectbox("상품 유형", PRODUCT_TYPES_V84, index=default_product_index("전문업종 원고"), key="kt_product")' in s,
    'kt_conditional_experience': 'if kt_product == "기자단 원고":\n            kt_experience = st.selectbox("기자단 체험 여부"' in s,
    'q_conditional_experience': 'if q_product == "기자단 원고":\n            q_experience = st.selectbox("기자단 체험 여부"' in s,
    'dash_conditional_experience': 'if dash_product == "기자단 원고":\n            dash_experience = st.selectbox("기자단 체험 여부"' in s,
    'prompt_conditional_experience': 'if product_type == "기자단 원고":\n        lines.append(f"- 기자단 체험 여부: {experience_mode}")' in s,
    'safe_export_line': 'def experience_export_line' in s,
}
print(checks)
assert all(checks.values()), checks
