from pathlib import Path
import json

APP = Path(__file__).with_name('app.py')
text = APP.read_text(encoding='utf-8')

tests = []

def check(name, cond, detail=''):
    tests.append({'name': name, 'ok': bool(cond), 'detail': detail})

check('version title updated', 'v10.0.28' in text and 'v10.0.27' not in text.split('st.title', 1)[-1][:120])
check('db router function present', 'def humanity_db_router_block' in text and 'DB 라우터 적용 지시 · v10.0.28' in text)
check('category selector present', 'def humanity_router_categories' in text and '선별 카테고리' in text)
check('sensitive field guard present', 'def is_sensitive_humanity_field' in text and '직접 치료·상담·소송·구매를 경험한 척하지 않는다' in text)
check('custom weird generation guard present', 'def custom_weird_generation_guard_block' in text and '사용자 이상문장 DB 선별 금지 패턴' in text)
check('research prompt uses router context', 'humanity_external_prompt_block(field, usecase_mode, article_style, "조사 프롬프트", primary_gyeol' in text)
check('draft prompt uses router context', 'humanity_external_prompt_block(field, usecase_mode, article_style, prompt_mode, primary_gyeol' in text)
check('claude prompt uses router context', 'humanity_external_prompt_block(field, usecase_mode, article_style, "Claude 패키지"' in text)
check('api caption mentions router', 'v10.0.28 DB 라우터' in text and '선별해 draft_prompt' in text)
check('api developer note mentions selected db', 'DB 라우터가 선별한 인간성 DB/이상문장 DB' in text)
check('no all-db dumping rule present', '전체 DB를 다 넣지 않고' in text and '조건 기반 라우터로 선별한다' in text)

summary = {'total': len(tests), 'pass': sum(1 for t in tests if t['ok']), 'failed': [t for t in tests if not t['ok']]}
Path(__file__).with_name('v1028_target_tests.json').write_text(json.dumps({'summary': summary, 'tests': tests}, ensure_ascii=False, indent=2), encoding='utf-8')
print(summary)
if summary['failed']:
    raise SystemExit(1)
