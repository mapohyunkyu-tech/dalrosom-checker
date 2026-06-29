import sys, runpy
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
APP = APP_DIR / 'app.py'

# Reuse fake Streamlit class without running its bottom test block.
ns = {'__file__': str((APP_DIR / 'run_menu_fake_test.py').resolve())}
code = (APP_DIR / 'run_menu_fake_test.py').read_text(encoding='utf-8').split('results=[]')[0]
exec(code, ns)
sys.modules['streamlit'] = ns['FakeStreamlit'](press_buttons=False)
g = runpy.run_path(str(APP), run_name='__v1023_target__')

checks = []

def check(name, ok, detail=''):
    checks.append((name, bool(ok), detail))

emo = g['detect_medical_emotion_mismatch']
intro = g['detect_intro_types']
hum = g['humanize_sentence_once']
kw_report = g['keyword_placement_report']

check('version_label_1023', 'v10.0.23' in APP.read_text(encoding='utf-8'))
check('medical_emotion_no_sufficient_false_positive', emo('병원 / 의료', '', '써마지는 한 번으로 충분한지 궁금합니다. 흥분한 상태는 아닙니다.', '써마지') == [])
check('medical_emotion_detect_real_dispute', bool(emo('병원 / 의료', '', '치료 결과가 안 좋아 억울하고 분하다. 손해 보는 느낌입니다.', '치료')))
check('checklist_intro_detects_three_boxes', '1. 독자의 상황을 찔러주는 체크리스트 활용' in intro('써마지 한 번으로 충분할지 헷갈리시나요?\n□ 효과가 궁금하다\n□ 통증이 걱정된다\n□ 유지기간이 알고 싶다'))
check('humanize_confirm_needed_abnormal_context', hum('증상이 오래가면 확인이 필요합니다', field='병원 / 의료') == '증상이 오래가면 의료진에게 확인하는 편이 안전합니다')
report, _ = kw_report('써마지 결과', '써마지 도입 문단입니다.\n\n효과는 바로 단정하지 않습니다\n이 문단은 키워드가 없습니다.\n\n마무리\n써마지 기준을 확인합니다.', '써마지', {'title_required': True, 'first_required': False, 'body_min': 1, 'body_max': 3, 'total_min': 2, 'total_max': 4, 'paragraph_max': 1})
check('keyword_missing_mid_is_recommendation_only', '보완 추천' in report and '키워드가 빠진 문단이 있습니다' not in report, report)

failed = [{'name': n, 'detail': d} for n, ok, d in checks if not ok]
print({'total': len(checks), 'pass': len(checks) - len(failed), 'failed': failed})
raise SystemExit(1 if failed else 0)
