import sys, runpy, json, os, re
from pathlib import Path
from run_menu_fake_test import FakeStreamlit
APP=Path(__file__).resolve().parent/'app.py'
os.chdir(APP.parent)
st=FakeStreamlit(press_buttons=False)
sys.modules['streamlit']=st
g=runpy.run_path(str(APP), run_name='__v1014_target__')
results=[]

def ok(name, cond, detail=''):
    results.append({'name':name,'ok':bool(cond),'detail':detail})

# 1. Purpose generation must reflect writing gyeol
purpose = g['auto_generate_content_goal']('병원 / 의료','매출 전환형','강남역 안과 라식 라섹 검사 전 확인할 점','강남역 안과','정밀검사 예약 유도','강남이오스안과의원','블로그 정보성','라식 라섹 검사','병원/업체 선택 기준형','장비보다 해석/판단 강조형','수술·시술·상담 전 체크형')
ok('purpose_contains_gyeol', '병원/업체 선택 기준형' in purpose and '장비보다 해석' in purpose, purpose[:250])
# 2. Draft prompt contains gyeol instruction block and flow
prompt = g['build_draft_prompt']('강남역 안과 라식 라섹 검사 전 확인할 점','강남역 안과','병원 / 의료','전문가 설명형','비교 고민형','1. 독자의 상황을 찔러주는 체크리스트 활용','6. 독자 상황 콕집기형',['각막두께와 안구건조증 검사가 중요하다'],['라식 라섹 차이가 헷갈린다'],[],target_len=2000,article_style='매출 전환형',brand_name='강남이오스안과의원',conversion_goal='정밀검사 예약 유도',content_goal='',primary_gyeol='병원/업체 선택 기준형',secondary_gyeol_1='장비보다 해석/판단 강조형',secondary_gyeol_2='수술·시술·상담 전 체크형')
ok('draft_prompt_has_gyeol_block', '[원고 글결 적용 지시]' in prompt and '대표 글결: 병원/업체 선택 기준형' in prompt and '장비보다 해석' in prompt, prompt[:500])
# 3. Claude package contains 글결 유지
claude = g['build_claude_naturalize_package'](topic='강남역 안과 라식 라섹 검사 전 확인할 점',keyword='강남역 안과',field='병원 / 의료',article_style='매출 전환형',brand_name='강남이오스안과의원',conversion_goal='정밀검사 예약 유도',draft_text='강남역 안과 라식 라섹 헷갈린다면\n검사 기준을 확인해야 합니다.',target_len=2000,primary_gyeol='병원/업체 선택 기준형',secondary_gyeol_1='장비보다 해석/판단 강조형')
ok('claude_has_gyeol', '대표 글결: 병원/업체 선택 기준형' in claude and '원고 글결은' in claude, claude[:500])
# 4. Alignment catches missing criteria for selection-criteria style
align = g['inspect_writing_gyeol_alignment']('좋은 병원입니다. 상담 가능합니다.', '병원/업체 선택 기준형', '', '', '병원 / 의료', '매출 전환형', '', '안과')
ok('alignment_catches_weak', bool(align.get('issues')), str(align))
Path('v1014_target_tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':{'total':len(results),'pass':sum(1 for r in results if r['ok']),'fail':sum(1 for r in results if not r['ok'])},'failed':[r for r in results if not r['ok']]},ensure_ascii=False,indent=2))
if any(not r['ok'] for r in results):
    raise SystemExit(1)
