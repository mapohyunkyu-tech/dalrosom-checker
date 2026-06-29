from pathlib import Path
s = Path('app.py').read_text(encoding='utf-8')
checks = {
    'version_label_1026': 'v10.0.26' in s,
    'humanity_export_helper': 'def humanity_external_prompt_block' in s,
    'research_prompt_humanity_export': 'humanity_export = humanity_external_prompt_block(field, usecase_mode, article_style, "조사 프롬프트")' in s,
    'draft_prompt_humanity_export': 'humanity_export = humanity_external_prompt_block(field, usecase_mode, article_style, prompt_mode)' in s,
    'claude_prompt_humanity_export': 'humanity_export = humanity_external_prompt_block(field, usecase_mode, article_style, "Claude 패키지")' in s,
    'external_gpt_notice': '외부 GPT/GPTs는 달로썸 앱 내부 DB 파일을 직접 읽을 수 없으므로' in s,
    'sensitive_field_guard': '직접 치료·소송·상담을 받은 척하지 않는다' in s,
}
failed = [k for k,v in checks.items() if not v]
print({'total': len(checks), 'pass': len(checks)-len(failed), 'failed': failed})
raise SystemExit(1 if failed else 0)
