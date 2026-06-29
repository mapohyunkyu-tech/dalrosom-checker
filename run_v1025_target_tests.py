import sys, runpy, json, os
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent
APP = APP_DIR / 'app.py'
os.chdir(APP_DIR)
# reuse fake streamlit from menu tester
ns = {'__file__': str((APP_DIR / 'run_menu_fake_test.py').resolve())}
code = (APP_DIR / 'run_menu_fake_test.py').read_text(encoding='utf-8').split('results=[]')[0]
exec(code, ns)
sys.modules['streamlit'] = ns['FakeStreamlit'](press_buttons=False)
g = runpy.run_path(str(APP), run_name='__v1025_target__')
checks=[]
def check(name, ok, detail=''):
    checks.append((name, bool(ok), detail))

text_all = APP.read_text(encoding='utf-8')
check('version_label_1025', 'v10.0.25' in text_all and '달로썸 원고 검수기 v10.0.25' in text_all)

sent = '써마지는 고주파 에너지로 피부 탄력 개선을 기대하는 시술이지만, 그 에너지를 어느 부위에 얼마나 조심스럽게 적용할지 해석하는 과정이 더 중요합니다.'
fixed = g['humanize_sentence_once'](sent, field='병원 / 의료', topic='써마지', keyword='써마지', writer_perspective='피부과 원장/전문의')
check('important_not_broken', '과정이 더 놓치기 쉽습니다' not in fixed and ('중요합니다' in fixed or '놓치기 쉽습니다' not in fixed), fixed)

sample = '최고의 전문성과 최신 장비로 100% 만족을 제공합니다.'
custom = g['match_custom_weird_db'](sample, product_type='업체형 원고', field='청소 / 홈케어')
check('custom_db_matches_cleaning', bool(custom) and any('100% 만족' in x['표현'] or '최고의' in x['표현'] for x in custom), custom)
issues = g['detect_humanization_issues']('청소 / 홈케어', sample * 20, '', '', '', '업체형 원고')
check('custom_db_in_humanization_issues', any('사용자DB' in x['표현'] for x in issues), issues)
medical_custom = g['match_custom_weird_db'](sample, product_type='블로그 정보성', field='병원 / 의료')
check('custom_db_no_cross_field_noise', not medical_custom, medical_custom)
kt = g['korean_teacher_review'](sample, product_type='업체형 원고', field='청소 / 홈케어')
check('custom_db_in_korean_teacher', any(str(r.get('구분','')).startswith('사용자DB/') for r in kt['검수결과']), kt['검수결과'][:5])

check_all = g['check_all']
body = ('겉보기에는 비슷해 보여도 작업 범위가 다를 수 있습니다. 최고의 전문성과 최신 장비로 100% 만족을 제공합니다. 작업 전 오염 원인과 소재를 먼저 확인하는 것이 좋습니다. ' * 8)
result = check_all('매트리스 청소 전 확인할 점', body, '매트리스 청소', '청소 / 홈케어', '매출 전환형', '청소업체 대표/전문가', '자동 추천', '1. 숫자/데이터 활용형', '관리 철학형', False, '', 500, 2000, '자동 추천', '', '자동 추천', '블로그 정보성')
# check_all returns tuple: scores, issues, total, caps, meta
issues_map = result[1]
check('custom_db_in_check_all_humanization', any('사용자DB' in str(x) for x in issues_map.get('사람화', [])), issues_map.get('사람화'))

failed=[{'name':n,'detail':str(d)[:700]} for n,ok,d in checks if not ok]
print(json.dumps({'total':len(checks),'pass':len(checks)-len(failed),'failed':failed}, ensure_ascii=False, indent=2))
raise SystemExit(1 if failed else 0)
