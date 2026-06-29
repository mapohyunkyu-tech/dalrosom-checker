from pathlib import Path
import json

APP = Path(__file__).with_name('app.py')
REQ = Path(__file__).with_name('requirements.txt')
text = APP.read_text(encoding='utf-8')
req = REQ.read_text(encoding='utf-8')

tests = []

def check(name, cond, detail=''):
    tests.append({'name': name, 'ok': bool(cond), 'detail': detail})

check('version title updated', 'v10.0.27' in text)
check('openai requirement added', any(line.strip() == 'openai' for line in req.splitlines()))
check('api key not hardcoded', 'sk-' not in text and 'OPENAI_API_KEY' in text)
check('responses api wrapper present', 'client.responses.create' in text and 'dalrosom_openai_generate' in text)
check('draft api generation UI present', 'API로 초안 생성' in text and 'api_generated_draft' in text)
check('homefeed api generation UI present', 'API로 홈피드 초안 생성' in text and 'api_generated_homefeed_draft' in text)
check('revision api UI present', 'API로 보강·자연화 실행' in text and 'api_revised_draft' in text)
check('check prefill bridge present', 'check_draft_prefill' in text and 'check_draft_text_area' in text)
check('fake streamlit safe spinner', 'dalrosom_spinner' in text and 'nullcontext' in text)

summary = {'total': len(tests), 'pass': sum(1 for t in tests if t['ok']), 'failed': [t for t in tests if not t['ok']]}
Path(__file__).with_name('v1027_target_tests.json').write_text(json.dumps({'summary': summary, 'tests': tests}, ensure_ascii=False, indent=2), encoding='utf-8')
print(summary)
if summary['failed']:
    raise SystemExit(1)
