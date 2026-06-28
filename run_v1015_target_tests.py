import sys, runpy, json, os
from pathlib import Path
from run_menu_fake_test import FakeStreamlit
APP=Path(__file__).resolve().parent/'app.py'
os.chdir(APP.parent)
st=FakeStreamlit(press_buttons=False)
sys.modules['streamlit']=st
g=runpy.run_path(str(APP), run_name='__v1015_target__')
results=[]
def ok(name, cond, detail=''):
    results.append({'name':name,'ok':bool(cond),'detail':detail})

prompt = g['build_draft_prompt'](
    'C-ARM 주사치료 전 확인할 점','C-ARM 주사치료','병원 / 의료','전문가 설명형',
    '비교 고민형','1. 독자의 상황을 찔러주는 체크리스트 활용','자동 추천',
    ['C-ARM은 영상유도 장비다','주사 위치와 통증 원인 확인이 중요하다'],
    ['장비만 있으면 괜찮을지 걱정된다','반복 주사가 부담될까 걱정된다'],[],
    target_len=2000, article_style='매출 전환형', writer_perspective='대표원장/전문의',
    conversion_goal='통증 주사치료 상담 문의 유도', prompt_mode='일반 GPT용',
    primary_gyeol='오해 반박형', secondary_gyeol_1='장비보다 해석/판단 강조형', secondary_gyeol_2='대표자 주장형')
ok('general_gpt_mode_block', '[일반 GPT용 실행 규칙]' in prompt and '별도 GPTs 설정 없이' in prompt, prompt[:700])
ok('gyeol_not_checklist_only', '단순 체크리스트 정보글로 축소하지 말고' in prompt and '오해 반박형' in prompt and '장비보다 해석' in prompt, prompt[:900])
ok('professional_style_guard', '[전문직 문체 안전장치]' in prompt and '입니다요' in prompt and '비표준 어미' in prompt, prompt[:1200])

hits = g['detect_nonstandard_professional_endings']('C-ARM 주사치료는 확인이 필요합니다요. 상담 기준이 됩니다요.')
ok('detect_weird_endings', '필요합니다요' in hits and '됩니다요' in hits, str(hits))

review = g['check_all'](
    'C-ARM 주사치료 확인할 5가지',
    'C-ARM 주사치료는 확인이 필요합니다요. 왜 영상유도가 필요한가요\n아픈 곳에 그냥 주사하면 된다고 생각하기 쉽습니다. 하지만 실제로는 원인 확인이 먼저입니다요.',
    'C-ARM 주사치료','병원 / 의료','납품','대표원장/전문의',
    '1. 독자의 상황을 찔러주는 체크리스트 활용','자동 추천','상담 유도형',False,'',1000,2200,
    selected_voice_type='비교 고민형', article_style='매출 전환형', primary_gyeol='오해 반박형')
_scores, issues, _total, cap_reasons, _extra = review
issues_text = json.dumps(issues, ensure_ascii=False)
cap_text = json.dumps(cap_reasons, ensure_ascii=False)
ok('review_flags_weird_endings', '비표준 어미' in issues_text and '문체 오류 상한' in cap_text, issues_text + cap_text)

claude = g['build_claude_naturalize_package'](
    topic='C-ARM 주사치료 전 확인할 점', keyword='C-ARM 주사치료', field='병원 / 의료',
    writer_perspective='대표원장/전문의', article_style='매출 전환형', conversion_goal='통증 주사치료 상담 문의 유도',
    draft_text='C-ARM 주사치료는 확인이 필요합니다요.', target_len=2000,
    primary_gyeol='오해 반박형', secondary_gyeol_1='장비보다 해석/판단 강조형')
ok('claude_style_guard', '[전문직 문체 안전장치]' in claude and '입니다요' in claude and '대표 글결: 오해 반박형' in claude, claude[:1200])

Path('v1015_target_tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':{'total':len(results),'pass':sum(1 for r in results if r['ok']),'fail':sum(1 for r in results if not r['ok'])},'failed':[r for r in results if not r['ok']]},ensure_ascii=False,indent=2))
if any(not r['ok'] for r in results):
    raise SystemExit(1)
