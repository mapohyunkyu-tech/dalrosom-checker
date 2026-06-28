import os, sys, types, runpy, json, csv, traceback, re, random
from pathlib import Path
from datetime import datetime
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
APP = APP_DIR / 'app.py'
os.chdir(APP_DIR)

class SessionState(dict):
    def __getattr__(self,k):
        try: return self[k]
        except KeyError: raise AttributeError(k)
    def __setattr__(self,k,v): self[k]=v

class Ctx:
    def __init__(self, st, name='ctx'): self.st=st; self.name=name
    def __enter__(self): self.st._ctx_stack.append(self.name); return self
    def __exit__(self, exc_type, exc, tb): self.st._ctx_stack.pop(); return False
    def __getattr__(self,n): return getattr(self.st,n)

class ColConfig:
    def CheckboxColumn(self,*a,**k): return {'type':'checkbox'}

class FakeStreamlit(types.ModuleType):
    def __init__(self, press_buttons=False):
        super().__init__('streamlit')
        self.session_state=SessionState(); self.press_buttons=press_buttons; self.events=[]; self._ctx_stack=[]; self.sidebar=Ctx(self,'sidebar'); self.column_config=ColConfig()
    def _log(self,name,*args,**kwargs): self.events.append((name,args,kwargs,list(self._ctx_stack)))
    def set_page_config(self,*a,**k): self._log('set_page_config',*a,**k)
    def title(self,*a,**k): self._log('title',*a,**k)
    def header(self,*a,**k): self._log('header',*a,**k)
    def subheader(self,*a,**k): self._log('subheader',*a,**k)
    def caption(self,*a,**k): self._log('caption',*a,**k)
    def markdown(self,*a,**k): self._log('markdown',*a,**k)
    def write(self,*a,**k): self._log('write',*a,**k)
    def text(self,*a,**k): self._log('text',*a,**k)
    def info(self,*a,**k): self._log('info',*a,**k)
    def success(self,*a,**k): self._log('success',*a,**k)
    def warning(self,*a,**k): self._log('warning',*a,**k)
    def error(self,*a,**k): self._log('error',*a,**k)
    def toast(self,*a,**k): self._log('toast',*a,**k)
    def divider(self,*a,**k): self._log('divider',*a,**k)
    def metric(self,*a,**k): self._log('metric',*a,**k)
    def json(self,*a,**k): self._log('json',*a,**k)
    def dataframe(self,*a,**k): self._log('dataframe',*a,**k)
    def table(self,*a,**k): self._log('table',*a,**k)
    def download_button(self,*a,**k): self._log('download_button',*a,**k); return False
    def stop(self): raise SystemExit('st.stop')
    def rerun(self): self._log('rerun')
    def tabs(self, labels): self._log('tabs',labels); return [Ctx(self,f'tab:{x}') for x in labels]
    def columns(self, spec):
        n=spec if isinstance(spec,int) else len(spec); self._log('columns',spec); return [Ctx(self,f'col:{i}') for i in range(n)]
    def expander(self,label, expanded=False): self._log('expander',label,expanded=expanded); return Ctx(self,f'expander:{label}')
    def selectbox(self,label, options, index=0, **kwargs):
        val=(options[index] if options and index < len(options) else (options[0] if options else None)); key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val); return self.session_state[key]
        return val
    def radio(self,label, options, index=0, **kwargs): return self.selectbox(label,options,index,**kwargs)
    def multiselect(self,label, options, default=None, **kwargs):
        val=default if default is not None else []; key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val); return self.session_state[key]
        return val
    def slider(self,label, min_value=None, max_value=None, value=None, step=None, **kwargs):
        val=value if value is not None else min_value; key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val); return self.session_state[key]
        return val
    def number_input(self,label, min_value=None, max_value=None, value=0, step=None, **kwargs):
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,value); return self.session_state[key]
        return value
    def checkbox(self,label, value=False, **kwargs):
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,value); return self.session_state[key]
        return value
    def _sample_text(self,label,value=''):
        if value not in (None,''): return value
        label=str(label)
        if any(x in label for x in ['원고','본문','초안','조사','내용','자료','사진','로그']): return '샘플 원고입니다. 오늘은 알아보겠습니다. 100% 제거됩니다.'
        if '업체' in label or '브랜드' in label: return '테스트업체'
        if '주제' in label: return '테스트 주제'
        if '키워드' in label: return '테스트 키워드'
        if '지역' in label: return '일산'
        return '테스트 입력값'
    def text_input(self,label,value='',**kwargs):
        val=self._sample_text(label,value); key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val); return self.session_state[key]
        return val
    def text_area(self,label,value='',**kwargs):
        val=self._sample_text(label,value); key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val); return self.session_state[key]
        return val
    def data_editor(self,data,**kwargs): return data.copy() if isinstance(data,pd.DataFrame) else data
    def file_uploader(self,*a,**k): return None
    def button(self,label,*a,**k):
        if k.get('disabled'): return False
        return self.press_buttons and not any(x in str(label) for x in ['삭제','복원 실행'])

sys.modules['streamlit'] = FakeStreamlit(False)
G = runpy.run_path(str(APP), run_name='__backtest_import__')


def make_body(case):
    k=case.get('keyword','') or '키워드'
    topic=case.get('topic','주제')
    risk=case.get('risk','normal')
    field=case.get('field','기타')
    base = f"{topic}을 찾는 사람은 {k}만 반복해서 보기보다 실제 기준을 확인해야 합니다. 상담이나 선택 전에는 비용, 진행 범위, 한계, 확인 자료를 차분히 보는 편이 안전합니다. "
    if risk=='medical': return base + "무조건 효과 있습니다. 완치 가능합니다. 부작용 없습니다. 누구나 가능합니다."
    if risk=='law': return base + "승소 보장됩니다. 무조건 받을 수 있습니다. 고소하면 바로 처벌됩니다. 100% 회수됩니다."
    if risk=='cleaning': return base + "100% 제거됩니다. 새것처럼 복원됩니다. 완벽하게 복원됩니다. 냄새가 완전히 사라집니다."
    if risk=='education': return base + "성적 보장됩니다. 합격 보장합니다. 무조건 향상됩니다."
    if risk=='fake_exp': return base + "제가 직접 방문해봤는데 사장님이 너무 꼼꼼하게 해주셨어요. 직접 받아보니 확실히 다르더라고요."
    if risk=='ai_style': return base + "오늘은 이 주제에 대해 알아보겠습니다. 도움이 될 수 있습니다. 확인하는 것이 필요합니다. 중요한 부분을 살펴보겠습니다."
    if risk=='tone_conflict': return base + "진료 기준을 확인해야 합니다. 근데 솔직히 개꿀이죠ㅋㅋ 문의하면 바로 해결될 수 있습니다."
    if risk=='homefeed_stiff': return "본 포스팅에서는 최신 이슈에 대해 알아보겠습니다. 해당 내용은 독자에게 도움이 될 수 있습니다. 자세한 기준을 살펴보겠습니다."
    if risk=='missing': return ""
    return base + "확인 가능한 정보 중심으로 정리하고, 과장된 표현보다는 독자가 실제로 비교할 기준을 잡을 수 있게 설명합니다."

FIELDS = {
 'hospital':'병원 / 의료', 'law':'법률', 'clean':'청소 / 홈케어', 'edu':'학원 / 교육', 'food':'맛집 / 카페 / 외식',
 'side':'기타', 'sports':'홈피드 / 생활 이슈', 'life':'홈피드 / 생활 이슈', 'cafe':'기타', 'etc':'기타 전문업종'
}

def add_cases():
    cases=[]
    def add(group,n,field,usecase,topics,risks):
        for i in range(n):
            topic,kw=topics[i%len(topics)]
            risk=risks[i%len(risks)]
            cases.append({'id':f'{group}-{i+1:03d}','group':group,'field':field,'usecase':usecase,'topic':topic,'keyword':kw,'brand':'테스트업체' if i%3!=1 else '', 'conversion':'상담 문의' if i%3==0 else '', 'risk':risk})
    add('HOSP',15,FIELDS['hospital'],'블로그 정보성', [('라식 라섹 검사 전 확인할 점','강남역 안과'),('써마지 시술 전 확인할 점','써마지'),('발기부전 치료 전 확인할 점','일산 비뇨기과'),('어린이 감기 진료 전 체크','소아청소년과'),('도수치료 상담 전 확인할 점','재활의학과')], ['normal','medical','ai_style','missing','tone_conflict'])
    add('LAW',10,FIELDS['law'],'전문가 설명형', [('빌려준 돈 반환청구 전 확인할 점','대여금반환청구소송'),('상간소송 전 준비사항','상간소송'),('음주운전 대응 전 확인할 점','음주운전 변호사'),('보증금 반환 내용증명','임대차 보증금')], ['normal','law','ai_style','missing'])
    add('CLEAN',10,FIELDS['clean'],'블로그 업체형', [('일산 매트리스 청소 맡기기 전 확인할 점','일산 매트리스 청소'),('입주청소 업체 선택 전 확인할 점','입주청소 업체'),('소파 청소 전 체크','소파 청소'),('에어컨 청소 맡기기 전 기준','에어컨 청소')], ['normal','cleaning','ai_style','missing'])
    add('EDU',10,FIELDS['edu'],'블로그 정보성', [('어린이 수영장 선택 전 확인할 점','어린이 수영장'),('초등 영어학원 선택 기준','초등 영어학원'),('수학학원 상담 전 확인','수학학원'),('태권도장 등록 전 확인','어린이 태권도')], ['normal','education','ai_style','missing'])
    add('FOOD',10,FIELDS['food'],'사진 제공형 기자단', [('일산역 꽈배기 간식집 고르는 기준','일산역 꽈배기'),('신상 카페 방문 전 확인할 점','일산 카페'),('가족 외식 장소 고르는 법','일산 맛집'),('포장 간식 추천 기준','도너츠')], ['normal','fake_exp','ai_style','missing'])
    add('SIDE',10,FIELDS['side'],'카페 정보성', [('카페 게시글 업로드 알바 시작 전 확인할 점','카페 게시글 업로드 알바'),('재택 부업 구할 때 주의사항','재택 부업'),('쿠팡플렉스 시작 전 기준','쿠팡플렉스'),('블로그 원고 알바 주의점','원고 알바')], ['normal','ai_style','fake_exp','missing'])
    add('SPORTS',10,FIELDS['sports'],'홈피드형', [('야구 예매 어려운 이유','야구 예매'),('농구 인기 없다더니 표가 없는 이유','농구 예매'),('축구 경우의 수 또 나온 이유','축구 경우의 수'),('이강인 경기 반응이 갈린 이유','이강인')], ['normal','homefeed_stiff','ai_style','missing'])
    add('LIFE',10,FIELDS['life'],'홈피드형', [('창문형 에어컨 가격 보고 멈칫한 이유','창문형 에어컨'),('아이방 비염 때문에 에어컨 고른 기준','아이방 에어컨'),('맥주 줄이려다 실패한 현실','다이어트'),('집안 냄새 잡는 방법 비교','생활정보')], ['normal','homefeed_stiff','ai_style','missing'])
    add('CAFE',10,FIELDS['cafe'],'카페 정보성', [('네이버 카페 글 쓸 때 주의할 점','카페 글쓰기'),('육아 카페 정보글 자연스럽게 쓰는 법','육아 카페'),('지역 카페 홍보글 티 안 나게 쓰는 기준','지역 카페'),('알바 후기글 쓸 때 조심할 표현','알바 후기')], ['normal','fake_exp','ai_style','tone_conflict'])
    add('ETC',5,FIELDS['etc'],'블로그 정보성', [('누수 업체 부르기 전 확인할 점','누수 업체'),('자동차 정비소 선택 기준','자동차 정비'),('반려동물 미용 맡기기 전 체크','펫미용')], ['normal','ai_style','missing'])
    return cases[:100]

cases=add_cases()

risk_expect = {
    'medical':['의료','결과','완치','무조건'],
    'law':['승소','무조건','처벌','회수'],
    'cleaning':['100%','새것','완벽','냄새'],
    'education':['성적','합격','무조건'],
    'fake_exp':['직접','방문','체험','가짜'],
    'ai_style':['오늘은','알아보겠습니다','도움','필요'],
    'tone_conflict':['관점','말투','ㅋㅋ','톤'],
    'homefeed_stiff':['홈피드','검색형','첫문장','AI'],
    'missing':['길이','부족','누락'],
}

def flatten_issues(issues):
    out=[]
    if isinstance(issues,dict):
        for cat, arr in issues.items():
            if isinstance(arr,list):
                for it in arr:
                    if isinstance(it, tuple): out.append(f'{cat}:{it[0]}:{it[1]}')
                    elif isinstance(it, dict): out.append(f'{cat}:{json.dumps(it,ensure_ascii=False)}')
                    else: out.append(f'{cat}:{it}')
    return ' | '.join(out)

def run_case(case):
    body=make_body(case)
    title=(case.get('keyword') or case['topic']) + ' 확인 기준'
    field=case['field']; keyword=case.get('keyword',''); topic=case['topic']; brand=case.get('brand','')
    errors=[]; warns=[]; actual=[]
    try:
        rp=G['build_research_prompt'](topic, keyword, field, '', '', 1500, '공백 포함', '5문단 짧게', '자동 추천', '자동 추천', '자동 추천', '자동', '홈페이지 정보 없음', '', '', '', '', case['usecase'], G['recommended_writer_perspective'](field, case['usecase'], topic, keyword), '정보성', '', brand, case.get('conversion',''), '본문 1회만', '', '', '', '', '', '', '', '')
        if topic and topic not in rp: warns.append('조사 프롬프트에 주제 반영 약함')
        if keyword and keyword not in rp: warns.append('조사 프롬프트에 키워드 반영 약함')
        actual.append('조사프롬프트 생성')
    except Exception as e:
        errors.append('메뉴1 조사프롬프트 오류:'+repr(e))
    try:
        dp=G['build_draft_prompt'](topic, keyword, field, '정보성', '자동 추천', '자동 추천', '자동 추천', '핵심 팩트 요약', '잠재고객 고민 요약', '주의사항 요약', '', 1500, '공백 포함', '5문단 짧게', '달로썸 GPTs용', '자동', '홈페이지 정보 없음', '', '', '', case['usecase'], G['recommended_writer_perspective'](field, case['usecase'], topic, keyword), '정보성', '', brand, case.get('conversion',''), '본문 1회만', '', '', '', '', '', '', '')
        if keyword and keyword not in dp: warns.append('원고 프롬프트에 키워드 반영 약함')
        actual.append('원고프롬프트 생성')
    except Exception as e:
        errors.append('메뉴2 원고프롬프트 오류:'+repr(e))
    try:
        scores, issues, total, caps, meta = G['check_all'](title, body, keyword, field, '', G['recommended_writer_perspective'](field,case['usecase'],topic,keyword), '자동 추천', '자동 추천', '자동', '미포함', '', 1000, 2200, '자동', '', '자동', case['usecase'], '정보성', '홈페이지 정보 없음', '', brand, case.get('conversion',''))
        issue_text=flatten_issues(issues)+' '+json.dumps(meta.get('delivery_risks',[]),ensure_ascii=False)
        actual.append(f'최종검수 {total}점')
        if case['risk'] in ['medical','law','cleaning','education','fake_exp']:
            expected_terms=risk_expect[case['risk']]
            if not any(t in issue_text for t in expected_terms):
                errors.append(f'DB 미검출:{case["risk"]}')
        if case['risk']=='normal' and total < 55:
            warns.append('정상샘플 점수 과도하게 낮음')
    except Exception as e:
        errors.append('메뉴3 검수 오류:'+repr(e))
        issue_text=''
    try:
        kt=G['korean_teacher_review'](body, '업체형 원고', field, '전문 정보형', '업체 자료 소개형')
        if case['risk']=='ai_style' and not any('AI식' in str(row.get('구분','')) for row in kt.get('검수결과', [])):
            errors.append('국어선생님 AI문체 미검출')
        if case['risk']=='tone_conflict' and not any('관점 충돌' in str(row.get('구분','')) for row in kt.get('검수결과', [])):
            errors.append('국어선생님 관점충돌 미검출')
        actual.append(f'국어 {kt.get("점수")}점')
    except Exception as e: errors.append('메뉴9 국어 오류:'+repr(e))
    try:
        gate=G['integrated_quality_gate'](title, body, '업체형 원고' if '홈피드' not in case['usecase'] else '홈피드 글', field, '전문 정보형', '사진 제공형' if case['usecase']=='사진 제공형 기자단' else '업체 자료 소개형', keyword, brand, '홈페이지 정보 없음', '')
        actual.append('출고판정 '+str(gate.get('출고판정')))
        if case['risk'] in ['medical','law','cleaning','education','fake_exp'] and gate.get('출고판정')=='출고 가능':
            errors.append('통합판정 위험샘플 출고 가능 처리')
    except Exception as e: errors.append('메뉴10 출고판정 오류:'+repr(e))
    # product-specific menus
    try:
        if case['usecase']=='사진 제공형 기자단':
            pp=G['build_photo_press_prompt'](brand, field, '일산', topic, keyword, '사진 제공형', '사진 기반 자연 소개형', '1. 외관 사진\n2. 작업 전 사진\n3. 작업 후 사진', '업체 제공 자료', '핵심 포인트', '직접 방문해봤다 금지', '제목/본문 상단 표시', '본문 1회만')
            insp=G['inspect_photo_press_text'](body, field, '사진 제공형')
            actual.append('사진기자단')
            if case['risk']=='fake_exp' and not insp: errors.append('사진기자단 체험위장 미검출')
        if '홈피드' in case['usecase']:
            titles=G['generate_homefeed_title_candidates'](topic, '스포츠' if case['group']=='SPORTS' else '생활', '웃픈 현실형', 5)
            thumb=G['generate_homefeed_thumbnail_phrases'](topic, '스포츠', '웃픈 현실형', 5)
            first=G['generate_homefeed_first_sentences'](topic, '스포츠', '웃픈 현실형', 5)
            insp=G['inspect_homefeed_lab_text'](titles[0], thumb[0], first[0], body, '스포츠')
            actual.append('홈피드랩')
        if case['group'] in ['HOSP','LAW','CLEAN','EDU','FOOD']:
            sp=G['build_sample_shorts_script'](topic, keyword, field, '30초', '체크리스트형')
            si=G['inspect_shorts_text'](sp, field, '30초', '체크리스트형')
            actual.append('쇼츠')
    except Exception as e: errors.append('상품별 메뉴 오류:'+repr(e))
    if errors: verdict='오류'
    elif warns: verdict='주의'
    else: verdict='통과'
    return {
        '테스트번호':case['id'], '분야':field, '사용처':case['usecase'], '입력값':f"주제={topic} / 키워드={keyword} / 업체명={'있음' if brand else '없음'} / risk={case['risk']}",
        '기대결과':('위험표현/충돌 감지' if case['risk']!='normal' else '기본 프롬프트 생성 및 과검출 없음'),
        '실제결과':' / '.join(actual), '판정':verdict, '오류유형':'; '.join(errors) if errors else ('; '.join(warns) if warns else ''), '수정메모':'' if not errors else '규칙 보강 필요 또는 추가 점검 필요'
    }

results=[run_case(c) for c in cases]
summary={
    'generated_at':datetime.now().isoformat(),
    'total':len(results),
    'pass':sum(1 for r in results if r['판정']=='통과'),
    'warn':sum(1 for r in results if r['판정']=='주의'),
    'error':sum(1 for r in results if r['판정']=='오류'),
    'by_group':{}
}
for r,c in zip(results,cases):
    d=summary['by_group'].setdefault(c['group'], {'total':0,'통과':0,'주의':0,'오류':0})
    d['total']+=1; d[r['판정']]+=1

csv_path=APP_DIR/'dalrosom_100_sample_backtest_report.csv'
json_path=APP_DIR/'dalrosom_100_sample_backtest_report.json'
with csv_path.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f, fieldnames=['테스트번호','분야','사용처','입력값','기대결과','실제결과','판정','오류유형','수정메모'])
    writer.writeheader(); writer.writerows(results)
json_path.write_text(json.dumps({'summary':summary,'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
errs=[r for r in results if r['판정']=='오류'][:10]
print('sample errors', json.dumps(errs,ensure_ascii=False,indent=2)[:3000])
