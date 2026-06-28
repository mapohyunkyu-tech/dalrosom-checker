import sys, runpy, json, os
from pathlib import Path
from run_menu_fake_test import FakeStreamlit
APP=Path(__file__).resolve().parent/'app.py'
os.chdir(APP.parent)
st=FakeStreamlit(press_buttons=False)
sys.modules['streamlit']=st
g=runpy.run_path(str(APP), run_name='__v1019_target__')
results=[]
def ok(name, cond, detail=''):
    results.append({'name':name,'ok':bool(cond),'detail':detail})

raw='''최종 제목: 써마지 전 확인할 5가지

본문: 써마지 한 번으로 충분할지, 300샷과 600샷 중 무엇이 맞을지 헷갈리시나요? 본문입니다.'''
title, body, source = g['extract_title']('', raw)
ok('extract_final_title_label', title=='써마지 전 확인할 5가지', f'{title}/{source}')
ok('strip_body_label_after_title', not body.startswith('본문:'), body[:30])
first = g['extract_first_content_sentence'](body)
ok('first_sentence_no_body_prefix', not first.startswith('본문:'), first)

sent='상담 전 이 기준들을 정리해두면 불필요한 비교를 줄이고, 본인에게 맞는 선택을 하는 데 도움이 됩니다.'
fixed=g['humanize_sentence_once'](sent, '병원 / 의료', '써마지', '써마지', '피부과 원장/전문의')
ok('humanize_help_no_duplicate_de', '하는 데 판단하는 데' not in fixed and '데 데' not in fixed, fixed)
ok('humanize_help_is_natural_reference', '참고' in fixed, fixed)

# 세부 필수 기준이 1개라도 빠지면 100점은 제한되어야 한다.
sample_body='''써마지 한 번으로 충분할지, 300샷과 600샷 중 무엇이 맞을지 헷갈리시나요?

한 번보다 먼저 볼 피부 기준
써마지는 피부 두께, 탄력 저하 정도, 시술 부위, 통증, 붓기, 열감, 효과 시점, 유지기간을 상담에서 확인해야 합니다.

내 피부 기준으로 결정해야 합니다
가격이나 샷수만 보지 말고 피부 상태를 기준으로 상담받는 편이 좋습니다.'''
scores, issues, total, cap_reasons, meta = g['check_all'](
    '써마지 전 확인할 5가지', sample_body, '써마지', '병원 / 의료', '써마지 시술',
    '피부과 원장/전문의', '5. 독자에게 질문 던지기', '1. 숫자/데이터 활용형', '관리 철학형',
    False, '', 1000, 1800, first_sentence_type='의문문 강제', selected_usecase_mode='블로그 정보성',
    article_style='매출 전환형', primary_gyeol='대표자 주장형', secondary_gyeol_1='선택 기준형', secondary_gyeol_2='수술·시술·상담 전 체크형')
ok('specialty_missing_caps_below_100', total <= 94, f'total={total}, missing={meta.get("specialty_missing")}, caps={cap_reasons}')

grade, note = g['final_delivery_grade'](100, [], [], [{'수정 이유':'평평한 종결','수정 전':'A','수정 후':'B'}])
ok('grade_100_with_optional_sentence_suggestion_still_ok', grade=='바로 납품 가능', f'{grade}/{note}')

Path('v1019_target_tests.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':{'total':len(results),'pass':sum(1 for r in results if r['ok']),'fail':sum(1 for r in results if not r['ok'])},'failed':[r for r in results if not r['ok']]},ensure_ascii=False,indent=2))
if any(not r['ok'] for r in results):
    raise SystemExit(1)
