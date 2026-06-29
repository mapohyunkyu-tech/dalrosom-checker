import sys, runpy, json
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent
APP = APP_DIR / 'app.py'
ns = {'__file__': str((APP_DIR / 'run_menu_fake_test.py').resolve())}
code = (APP_DIR / 'run_menu_fake_test.py').read_text(encoding='utf-8').split('results=[]')[0]
exec(code, ns)
sys.modules['streamlit'] = ns['FakeStreamlit'](press_buttons=False)
g = runpy.run_path(str(APP), run_name='__v1024_target__')
checks = []
def check(name, ok, detail=''):
    checks.append((name, bool(ok), detail))
text = APP.read_text(encoding='utf-8')
check('version_label_1024', 'v10.0.24' in text and '달로썸 원고 검수기 v10.0.24' in text)
emo = g['detect_medical_emotion_mismatch']
check('medical_emotion_no_sufficient_false_positive', emo('병원 / 의료', '', '써마지는 한 번으로 충분한지 궁금합니다. 흥분한 상태는 아닙니다.', '써마지') == [])
check('medical_emotion_detect_real_dispute', bool(emo('병원 / 의료', '', '치료 결과가 안 좋아 억울하고 분하다. 손해 보는 느낌입니다.', '치료')))
intro_block = g['intro_body_variation_block']('써마지 시술', '써마지', '1. 독자의 상황을 찔러주는 체크리스트 활용', '자동 추천', '대표자 주장형', '선택 기준형', '책임 진료/책임 작업 강조형', '병원 / 의료', '매출 전환형')
check('intro_variation_contains_banned_starts', '첫 문장 금지 패턴' in intro_block and '알아보다 보면' in intro_block and '대표자형' in intro_block)
no_brand = g['detect_no_brand_institution_phrases']('저희 병원에서는 본원 기준으로 안내합니다. 저희는 무리하지 않습니다.', '', '업체명 없음')
check('no_brand_institution_detects', {'저희 병원','본원','저희는'}.issubset(set(no_brand)), no_brand)
allowed = g['detect_no_brand_institution_phrases']('저희 병원에서는 본원 기준으로 안내합니다.', '달로썸의원', '본문 1회만')
check('brand_context_allows_institution', allowed == [], allowed)
auth = g['inspect_author_narration_alignment']('써마지 상담에서는 샷 수를 확인하는 것이 좋습니다. 의료진은 피부 상태를 봅니다. 상담에서는 계획을 세웁니다.', '대표자 직접 서술형', '피부과 원장/전문의', '대표자 주장형', '선택 기준형', '책임 진료/책임 작업 강조형', '매출 전환형', '', '업체명 없음', '병원 / 의료')
check('direct_narration_weak_detected', any(i.get('type') == 'direct_voice_weak' for i in auth['issues']), auth)
check_all = g['check_all']
body = '써마지 상담에서는 샷 수만 비교하는 분들이 많습니다. 저희 병원에서는 본원 기준으로 안내합니다. 의료진은 확인하는 것이 좋습니다. 상담에서는 계획을 잡습니다. 마무리도 상담이 필요합니다.'
scores, issues, total, caps, meta = check_all('써마지 확인 기준', body, '써마지', '병원 / 의료', '마케팅 회사 테스트 원고', '피부과 원장/전문의', '5. 독자에게 질문 던지기', '4. 궁금증 자극형', '관리 철학형', False, '', 500, 1000, '자동 추천', '', '자동 추천', '블로그 정보성', '매출 전환형', '홈페이지 정보 없음', '', '', '', '대표자 주장형', '선택 기준형', '책임 진료/책임 작업 강조형', '대표자 직접 서술형', '업체명 없음')
check('check_all_caps_no_brand_and_direct', total <= 86 and any('업체명 없음' in c for c in caps) and 'author_narration' in meta, {'total': total, 'caps': caps, 'issues': issues.get('작성자 관점')})
failed = [{'name': n, 'detail': str(d)[:500]} for n, ok, d in checks if not ok]
print(json.dumps({'total': len(checks), 'pass': len(checks)-len(failed), 'failed': failed}, ensure_ascii=False, indent=2))
raise SystemExit(1 if failed else 0)
