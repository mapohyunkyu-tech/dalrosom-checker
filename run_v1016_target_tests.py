import sys, runpy, json, os
from pathlib import Path
from run_menu_fake_test import FakeStreamlit
APP=Path(__file__).resolve().parent/'app.py'
os.chdir(APP.parent)
st=FakeStreamlit(press_buttons=False)
sys.modules['streamlit']=st
g=runpy.run_path(str(APP), run_name='__v1016_target__')
results=[]
def ok(name, cond, detail=''):
    results.append({'name':name,'ok':bool(cond),'detail':detail})

prompt = g['build_draft_prompt'](
    '써마지 시술 전 확인할 점','써마지','병원 / 의료','전문가 설명형',
    '비교 고민형','1. 독자의 상황을 찔러주는 체크리스트 활용','자동 추천',
    ['써마지는 고주파 장비다','샷 수보다 피부 상태와 에너지 배분이 중요하다'],
    ['샷 수만 보면 되는지 헷갈린다','내 피부에 맞는지 걱정된다'],[],
    target_len=2000, article_style='매출 전환형', writer_perspective='대표원장/전문의',
    conversion_goal='리프팅 상담 문의 유도', prompt_mode='일반 GPT용',
    primary_gyeol='오해 반박형', secondary_gyeol_1='장비보다 해석/판단 강조형', secondary_gyeol_2='대표자 주장형')
ok('mandatory_block_present', '[글결 필수 장치 · v10.0.16]' in prompt, prompt[:1200])
ok('representative_mandatory_present', '대표자 주장형 필수' in prompt and '제가 상담에서 먼저 보는 기준' in prompt, prompt[:1800])
ok('misconception_and_interpretation_mandatory', '오해 반박형 필수' in prompt and '장비보다 해석/판단 강조형 필수' in prompt, prompt[:2200])
ok('general_gpt_mentions_mandatory', '필수 흐름' in prompt and '[글결 필수 장치]' in prompt and '대표/전문가가 중요하게 보는 기준 문장' in prompt, prompt[:1000])

weak_text='써마지는 고주파 에너지를 사용하는 시술입니다. 샷 수와 효과 시점을 확인하는 것이 좋습니다.'
align = g['inspect_writing_gyeol_alignment'](weak_text, '오해 반박형', '장비보다 해석/판단 강조형', '대표자 주장형', '병원 / 의료', '매출 전환형', '써마지 시술 전 확인할 점', '써마지')
issues=' '.join(align.get('issues',[]))
ok('alignment_checks_secondary_gyeols', '대표자 주장형' in issues and '장비보다 해석/판단' in issues, issues)

strong_text='환자분들이 흔히 하는 오해는 써마지 샷 수만 많으면 충분하다는 생각입니다. 하지만 실제로는 피부 두께와 탄력 상태를 어떻게 분석하고 에너지를 배분할지 판단하는 과정이 더 중요합니다. 제가 상담에서 먼저 보는 기준은 얼굴 전체의 처짐 위치와 볼륨 상태입니다.'
align2 = g['inspect_writing_gyeol_alignment'](strong_text, '오해 반박형', '장비보다 해석/판단 강조형', '대표자 주장형', '병원 / 의료', '매출 전환형', '써마지 시술 전 확인할 점', '써마지')
ok('alignment_passes_strong_text', not align2.get('issues'), str(align2))

claude = g['build_claude_naturalize_package'](
    topic='써마지 시술 전 확인할 점', keyword='써마지', field='병원 / 의료',
    writer_perspective='대표원장/전문의', article_style='매출 전환형', conversion_goal='리프팅 상담 문의 유도',
    draft_text='써마지는 샷 수가 중요합니다. 상담이 필요합니다.', target_len=2000,
    primary_gyeol='오해 반박형', secondary_gyeol_1='장비보다 해석/판단 강조형', secondary_gyeol_2='대표자 주장형')
ok('claude_has_representative_boost', '대표자 주장형이 포함되어 있으므로' in claude and '[글결 필수 장치 · v10.0.16]' in claude, claude[:2500])

Path('v1016_target_tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':{'total':len(results),'pass':sum(1 for r in results if r['ok']),'fail':sum(1 for r in results if not r['ok'])},'failed':[r for r in results if not r['ok']]},ensure_ascii=False,indent=2))
if any(not r['ok'] for r in results):
    raise SystemExit(1)
