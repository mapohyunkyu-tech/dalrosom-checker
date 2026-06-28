import sys, types, runpy, re, json, os
from pathlib import Path
import pandas as pd
APP_DIR=Path(__file__).resolve().parent
APP=APP_DIR/'app.py'
os.chdir(APP_DIR)

class SessionState(dict):
    def __getattr__(self,k):
        try:return self[k]
        except KeyError: raise AttributeError(k)
    def __setattr__(self,k,v): self[k]=v
class Ctx:
    def __init__(self, st, name='ctx'): self.st=st; self.name=name
    def __enter__(self): self.st._ctx_stack.append(self.name); return self
    def __exit__(self,*a): self.st._ctx_stack.pop(); return False
    def __getattr__(self,name): return getattr(self.st,name)
class ColConfig:
    def CheckboxColumn(self,*a,**k): return {}
class FakeStreamlit(types.ModuleType):
    def __init__(self):
        super().__init__('streamlit'); self.session_state=SessionState(); self._ctx_stack=[]; self.events=[]; self.sidebar=Ctx(self,'sidebar'); self.column_config=ColConfig()
    def _log(self,n,*a,**k): self.events.append((n,a,k,list(self._ctx_stack)))
    def __getattr__(self,name):
        def f(*a,**k): self._log(name,*a,**k); return None
        return f
    def set_page_config(self,*a,**k): self._log('set_page_config',*a,**k)
    def tabs(self, labels): self._log('tabs',labels); return [Ctx(self,f'tab:{x}') for x in labels]
    def columns(self, spec): n=spec if isinstance(spec,int) else len(spec); return [Ctx(self,f'col:{i}') for i in range(n)]
    def expander(self,label, expanded=False): return Ctx(self,f'expander:{label}')
    def selectbox(self,label, options, index=0, **k):
        val=options[index] if options else None; key=k.get('key')
        if key: self.session_state.setdefault(key,val); return self.session_state[key]
        return val
    def radio(self,*a,**k): return self.selectbox(*a,**k)
    def multiselect(self,label, options, default=None, **k): val=default or []; key=k.get('key'); self.session_state.setdefault(key,val) if key else None; return self.session_state.get(key,val)
    def number_input(self,label, min_value=None, max_value=None, value=0, step=None, **k): key=k.get('key'); self.session_state.setdefault(key,value) if key else None; return self.session_state.get(key,value)
    def slider(self,label, min_value=None, max_value=None, value=None, step=None, **k):
        val = value if value is not None else min_value
        key=k.get('key')
        if key: self.session_state.setdefault(key,val); return self.session_state.get(key,val)
        return val
    def checkbox(self,label, value=False, **k): key=k.get('key'); self.session_state.setdefault(key,value) if key else None; return self.session_state.get(key,value)
    def button(self,*a,**k): return False
    def text_input(self,label,value='',**k): key=k.get('key'); self.session_state.setdefault(key,value) if key else None; return self.session_state.get(key,value)
    def text_area(self,label,value='',**k): key=k.get('key'); self.session_state.setdefault(key,value) if key else None; return self.session_state.get(key,value)
    def data_editor(self,data,**k): return data.copy() if hasattr(data,'copy') else data
    def file_uploader(self,*a,**k): return None
    def stop(self): raise SystemExit('stop')

fake=FakeStreamlit(); sys.modules['streamlit']=fake
g=runpy.run_path(str(APP), run_name='__audit__')

b_lines=[
    '[3] B등급 잠재고객 고민패턴',
    '검사 결과가 정확하지 않을까 봐 걱정 수술 후 건조감과 빛번짐에 대한 걱정 라식과 라섹 중 잘못 선택할까 봐 망설임 렌즈 중단 기간을 지키지 못했을 때 검사 연기 가능성 회복기간과 일상 복귀 시점의 개인차',
    '라식과 라섹의 차이를 이름만 알고 실제 기준은 모름 각막두께 수치만 보면 되는지, 각막 모양도 함께 봐야 하는지 헷갈림 안구건조증 검사 결과가 수술 선택에 어떻게 연결되는지 모름 빛번짐 검사가 왜 필요한지 이해가 부족함',
    '제목으로 바꿀 수 있는 질문',
    '“제 눈에는 라식이 맞나요, 라섹이 맞나요?” “렌즈를 오래 꼈는데 검사 결과가 괜찮을까요?”',
]
prompt=g['build_draft_prompt'](
    topic='강남역 안과 라식 라섹 검사 전 확인할 점', keyword='강남역 안과', field='병원 / 의료', content_type='전문가 설명형',
    voice_type='비교 고민형', intro_type='1. 독자의 상황을 찔러주는 체크리스트 활용', title_type='1. 숫자/데이터 활용형',
    a_lines=['라식·라섹 전에는 굴절 상태, 각막 상태, 각막두께, 동공 크기, 안구건조 여부 등을 종합적으로 확인해야 합니다.'],
    b_lines=b_lines, c_lines=['검사만 받아도 되는지 궁금하다','라식과 라섹 중 뭐가 맞는지 헷갈린다'],
    target_len=2000, spacing_type='공백 제외', usecase_mode='블로그 정보성', writer_perspective='안과 원장/전문의',
    article_style='매출 전환형', sub_keywords='라식 라섹 검사, 시력교정 상담, 안구건조증 검사, 정밀검사, 각막두께 검사, 빛번짐 검사', brand_name='강남이오스안과의원', conversion_goal='정밀검사 또는 시력교정 상담 문의 유도', brand_intensity='본문 1회만', tone_detail='의료진이 상담 기준을 차분히 설명하듯 쓴다.'
)
patterns={
    'bad_joined_numbers': r'\b\d{4,}(?:자|곳|회|개|문단)',
    'bad_b_heading_sentence': r'B등급 잠재고객 고민패턴 때문에|\[3\] B등급',
    'old_compress_conflict': r'짧으면.*압축|분량이 짧으면.*압축|압축하거나 확장',
    'old_claude_in_3': r'③.*Claude용 윤문|Claude용 윤문 지시문 기본형',
    'old_button_label': r'검수 시작',
}
findings={name: re.findall(pat,prompt) for name,pat in patterns.items()}
# Also ensure positive requirements are present
positives={
    'length_priority_top': '[분량 최우선 지시' in prompt and '공백 제외 2000자 내외' in prompt,
    'hard_min_present': '1700자 미만이면 분량 미달' in prompt,
    'self_check_present': '[출력 전 자체 점검]' in prompt,
    'cleaned_b_section': '[3] B등급' not in prompt,
}
(Path('prompt_audit_generated_prompt.txt')).write_text(prompt,encoding='utf-8')
(Path('prompt_audit_report.json')).write_text(json.dumps({'findings':findings,'positives':positives,'prompt_len':len(prompt)},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'findings':findings,'positives':positives,'prompt_len':len(prompt)},ensure_ascii=False,indent=2))
