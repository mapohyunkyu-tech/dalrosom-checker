import sys, runpy, json, os
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
import run_menu_fake_test as t
fake=t.FakeStreamlit(press_buttons=False)
sys.modules['streamlit']=fake
g=runpy.run_path('app.py', run_name='__v1013_target__')
res={}
res['title_cockjip']=g['detect_title_types']('강남역 안과 라식 라섹 헷갈린다면')
res['b_terms']=g['extract_b_concern_terms']('라식 라섹 차이와 렌즈 중단 기간, 빛번짐, 안구건조증이 걱정된다', '강남역 안과')
res['first_sentence']=g['evaluate_first_sentence_grounding']('라식과 라섹 중 무엇이 맞는지 헷갈리고, 검사 전 무엇부터 확인해야 할지 망설여지는 분들이 많습니다.', '라식 라섹 차이와 렌즈 중단 기간, 빛번짐, 안구건조증이 걱정된다', '강남역 안과')
res['auto_goal']=g['auto_generate_content_goal']('병원 / 의료','매출 전환형','강남역 안과 라식 라섹 검사 전 확인할 점','강남역 안과','정밀검사 예약 또는 시력교정 상담 문의 유도','강남이오스안과의원','블로그 정보성','라식 라섹 검사, 시력교정 상담')
res['weak_ending']=g['conversion_ending_weak']('강남이오스안과의원에서 상담을 고려하신다면 렌즈 종류와 건조감, 야간 운전 여부를 정리해두면 도움이 됩니다. 강남역 안과를 알아보는 단계라면 정밀검사 예약을 통해 현재 눈 상태를 확인하는 것부터 시작해보시기 바랍니다.','매출 전환형','강남이오스안과의원','정밀검사 예약 또는 시력교정 상담 문의 유도','병원 / 의료')
res['claude_mode_has_boost']='[Claude 보강수정 요청 패키지]' in g['build_claude_naturalize_package'](topic='강남역 안과 라식 라섹 검사 전 확인할 점', keyword='강남역 안과', field='병원 / 의료', article_style='매출 전환형', brand_name='강남이오스안과의원', conversion_goal='정밀검사 예약 또는 시력교정 상담 문의 유도', draft_text='짧은 원고입니다.', target_len=2000)
Path('v1013_target_tests.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(res,ensure_ascii=False,indent=2))
