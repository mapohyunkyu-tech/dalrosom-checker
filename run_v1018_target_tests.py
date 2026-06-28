import sys, runpy, json, os
from pathlib import Path
from run_menu_fake_test import FakeStreamlit
APP=Path(__file__).resolve().parent/'app.py'
os.chdir(APP.parent)
st=FakeStreamlit(press_buttons=False)
sys.modules['streamlit']=st
g=runpy.run_path(str(APP), run_name='__v1018_target__')
results=[]
def ok(name, cond, detail=''):
    results.append({'name':name,'ok':bool(cond),'detail':detail})

body_safe='"써마지는 한 번만 받아도 충분한가요, 아니면 300샷과 600샷 차이를 먼저 봐야 하나요?" 상담에서 자주 나오는 질문입니다. 울쎄라와 비교하면 어떤 차이가 있는지 묻는 경우가 많습니다.'
emo_safe=g['detect_medical_emotion_mismatch']('병원 / 의료','써마지 전 확인할 5가지',body_safe,'써마지')
ok('sufficient_not_detected_as_bunhada', not emo_safe, str(emo_safe))
body_risk='비용을 내고도 설명을 제대로 듣지 못해 분합니다. 검사 선택이 억울하게 느껴질 수 있습니다.'
emo_risk=g['detect_medical_emotion_mismatch']('병원 / 의료','써마지 전 확인할 5가지',body_risk,'써마지')
ok('explicit_dispute_emotion_still_detected', '분하다' in emo_risk or '억울' in emo_risk, str(emo_risk))

risk_body='또 하나의 오해는 샷 수가 많을수록 무조건 좋다는 생각입니다. 실제로는 피부 상태를 먼저 확인해야 합니다.'
ok('mujogeon_misconception_context_safe', g['is_safe_risk_context'](risk_body,'무조건'), risk_body)
hard_body='이 시술은 누구에게나 무조건 효과가 있습니다.'
ok('mujogeon_hard_risk_not_safe', not g['is_safe_risk_context'](hard_body,'무조건'), hard_body)

section_body='''써마지 전 확인할 5가지

"써마지는 한 번만 받아도 충분한가요?" 상담에서 자주 나오는 질문입니다.

샷 수보다 먼저 보는 기준
피부과 의료진 입장에서 상담 때 먼저 보는 기준은 샷 수 자체가 아니라 피부 두께입니다.

한 번이면 충분하다는 오해
환자분들이 가장 헷갈려하는 부분입니다.

효과 시점과 유지기간은 다르게 봐야 합니다
유지기간은 개인차가 있습니다.

상담 전 정리해야 할 질문
써마지 시술은 장비명보다 내 피부 상태를 먼저 확인할 때 선택 기준이 분명해집니다.'''
sections=g['split_keyword_sections'](section_body)
ok('line_based_subheadings_split', len(sections) >= 4, str([(s['role'],s['heading']) for s in sections]))
report,_=g['keyword_placement_report']('써마지 전 확인할 5가지', section_body, '써마지', {'paragraph_max':1,'title_required':True})
ok('keyword_report_not_single_intro_only', '|도입|도입|0|5|5|' not in report, report)

Path('v1018_target_tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':{'total':len(results),'pass':sum(1 for r in results if r['ok']),'fail':sum(1 for r in results if not r['ok'])},'failed':[r for r in results if not r['ok']]},ensure_ascii=False,indent=2))
if any(not r['ok'] for r in results):
    raise SystemExit(1)
