import os, sys, types, runpy, json, traceback
from pathlib import Path
import pandas as pd
APP_DIR=Path(__file__).resolve().parent; os.chdir(APP_DIR)
class SS(dict):
 def __getattr__(self,k):
  try:return self[k]
  except KeyError: raise AttributeError(k)
 def __setattr__(self,k,v): self[k]=v
class Ctx:
 def __init__(self,st,n='ctx'): self.st=st; self.n=n
 def __enter__(self): return self
 def __exit__(self,*a): return False
 def __getattr__(self,n): return getattr(self.st,n)
class CC:
 def CheckboxColumn(self,*a,**k): return {}
class FS(types.ModuleType):
 def __init__(self): super().__init__('streamlit'); self.session_state=SS(); self.sidebar=Ctx(self); self.column_config=CC(); self._ctx_stack=[]
 def __getattr__(self,n):
  def f(*a,**k):
   if n=='tabs': return [Ctx(self,str(x)) for x in a[0]]
   if n=='columns': return [Ctx(self,str(i)) for i in range(a[0] if isinstance(a[0],int) else len(a[0]))]
   if n=='expander': return Ctx(self)
   if n in ['selectbox','radio']: return a[1][k.get('index',0)] if len(a)>1 and a[1] else None
   if n=='multiselect': return k.get('default', [])
   if n in ['text_input','text_area']: return k.get('value','') if 'value' in k else (a[1] if len(a)>1 else '')
   if n in ['number_input','slider']: return k.get('value',0)
   if n=='checkbox': return k.get('value',False)
   if n=='button': return False
   if n=='data_editor': return a[0]
   if n=='file_uploader': return None
   return None
  return f
sys.modules['streamlit']=FS(); G=runpy.run_path(str(APP_DIR/'app.py'), run_name='__integration__')
checks=[]
def add(name, fn):
 try:
  detail=fn(); checks.append({'name':name,'ok':True,'detail':detail})
 except Exception as e:
  checks.append({'name':name,'ok':False,'error':repr(e),'traceback':traceback.format_exc()})

add('①→②→③→⑩ 검색형 원고 흐름', lambda: (lambda topic,kw,field,body: {
 'research_len':len(G['build_research_prompt'](topic,kw,field,'','',1500,'공백 포함','5문단 짧게','자동 추천','자동 추천','자동 추천','자동','홈페이지 정보 없음','','','','','블로그 정보성','전문가 설명형','','','', '본문 1회만','','','','','','','','')),
 'draft_len':len(G['build_draft_prompt'](topic,kw,field,'정보성','자동 추천','자동 추천','자동 추천','A','B','C','',1500,'공백 포함','5문단 짧게','달로썸 GPTs용','자동','홈페이지 정보 없음','','','','블로그 정보성','전문가 설명형','','','', '본문 1회만','','','','','','','','')),
 'check_score':G['check_all'](kw+' 기준',body,kw,field,'','전문가','자동 추천','자동 추천','자동','미포함','',1000,2200,'자동','','자동','블로그 정보성','정보성','홈페이지 정보 없음','','','')[2],
 'gate':G['integrated_quality_gate'](kw+' 기준',body,'업체형 원고',field,'전문 정보형','업체 자료 소개형',kw,'','홈페이지 정보 없음','')['출고판정']
})('일산 매트리스 청소 맡기기 전 확인할 점','일산 매트리스 청소','청소 / 홈케어','일산 매트리스 청소는 소재와 얼룩 원인, 습식 가능 여부, 건조 시간을 확인해야 합니다. 100% 제거됩니다. 새것처럼 복원됩니다.'))

add('⑦ 상품별 원고 엔진→⑩ 품질게이트', lambda: {
 'prompt_len':len(G['build_multi_product_prompt']('기자단 원고','맛집 / 카페 / 외식','일산역 꽈배기 간식집','일산역 꽈배기','성수동꿀꽈배기','기자단형','사진 제공형','사진 5장','외관, 메뉴, 포장','직접 방문 금지','1500자','30초',2,'귀찮음+돈고민')),
 'gate':G['integrated_quality_gate']('일산역 꽈배기','제가 직접 방문해봤는데 맛있었어요. 사진 자료를 보면 포장과 메뉴 구성이 보입니다.','기자단 원고','맛집 / 카페 / 외식','기자단형','사진 제공형','일산역 꽈배기','성수동꿀꽈배기','홈페이지 정보 없음','')['출고판정']
})
add('⑧ 샘플테스트→DB후보→간단모드', lambda: (lambda result: (lambda rows, issue_rows, mined, recs: {'rows':len(rows), 'issue_rows':len(issue_rows), 'mined':len(mined), 'recs':len(recs), 'safe':G['stress_simple_action_summary'](recs)['safe_count']})(result[0], result[1], result[2], G['build_stress_auto_recommendations'](result[1],10)))(G['run_stress_test'](['기자단 원고'],5,'청소 / 홈케어')))
add('⑨ 국어선생님→⑩ 품질게이트 점수연동', lambda: (lambda body: {'kt_score':G['korean_teacher_review'](body,'업체형 원고','병원 / 의료','전문 정보형','업체 자료 소개형')['점수'], 'gate':G['integrated_quality_gate']('병원 글',body,'업체형 원고','병원 / 의료','전문 정보형','업체 자료 소개형','키워드','','홈페이지 정보 없음','')['출고판정']})('오늘은 병원 선택 기준에 대해 알아보겠습니다. 도움이 될 수 있습니다. 확인하는 것이 필요합니다.'))
add('⑬ 사진자료 기자단→⑩ 품질게이트', lambda: {'photo_rows':len(G['build_photo_flow_table'](G['parse_photo_lines']('1. 외관\n2. 메뉴\n3. 포장'), '맛집 / 카페 / 외식')), 'inspect_count':len(G['inspect_photo_press_text']('제가 직접 방문해봤는데 사진을 보니 메뉴가 보입니다.','맛집 / 카페 / 외식','사진 제공형'))})
add('⑭ 쇼츠→검수→납품포맷', lambda: (lambda s: {'script_len':len(s), 'issues':len(G['inspect_shorts_text'](s,'청소 / 홈케어','30초','체크리스트형')), 'delivery_len':len(G['build_shorts_delivery_format']('제목','후킹',s,'자막','컷','댓글','청소 / 홈케어','30초','체크리스트형'))})(G['build_sample_shorts_script']('매트리스 청소 전 확인할 점','매트리스 청소','청소 / 홈케어','30초','체크리스트형')))
add('⑮ 홈피드→점수→검수→납품포맷', lambda: {'titles':len(G['generate_homefeed_title_candidates']('야구 예매 어려운 이유','스포츠','웃픈 현실형',10)), 'score':G['score_homefeed_concept']('야구 예매 어려운 이유','스포츠','자료','야구 예매, 이 정도면 전쟁 아닌가요','표가 없다니','인기 없다던 종목인데 예매창엔 자리가 없습니다.')[1], 'inspect':len(G['inspect_homefeed_lab_text']('야구 예매','표가 없다니','인기 없다던 종목인데 예매창엔 자리가 없습니다.','본문','스포츠'))})
add('⑰→⑲→㉑ 월관리/통계/백업 연동', lambda: {'calendar':len(G['v10_build_topic_calendar']({'업체명':'남편홈케어','분야':'청소 / 홈케어','건당단가':50000}, '일산 매트리스 청소\n일산 소파 청소')), 'stats_keys':list(G['v10_build_stats']().keys()), 'backup_keys':list(G['v10_collect_backup_payload']().keys())[:5]})
add('⑱ 견적서→이력 형식', lambda: {'quote_len':len(G['v10_build_quote_text']('남편홈케어',[{'상품':'블로그 원고','수량':4,'단가':50000,'금액':200000}],0,'카톡 문의 유도 포함'))})
add('⑫ 이상문장DB→패턴후보', lambda: {'loaded':len(G['load_custom_weird_db']()), 'patterns':len(G['build_pattern_candidates_from_rows'](G['load_custom_weird_db']()[:5]))})

summary={'total':len(checks),'pass':sum(1 for c in checks if c['ok']),'error':sum(1 for c in checks if not c['ok'])}
(APP_DIR/'dalrosom_integration_harmony_report.json').write_text(json.dumps({'summary':summary,'checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':summary,'failed':[c for c in checks if not c['ok']]},ensure_ascii=False,indent=2)[:4000])
