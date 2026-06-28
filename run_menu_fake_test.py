import sys, types, runpy, traceback, os, json, copy
from pathlib import Path
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
APP = APP_DIR / 'app.py'
os.chdir(APP_DIR)

class SessionState(dict):
    def __getattr__(self, k):
        try: return self[k]
        except KeyError: raise AttributeError(k)
    def __setattr__(self, k, v): self[k]=v
    def __delattr__(self, k):
        if k in self: del self[k]

class Ctx:
    def __init__(self, st, name='ctx'):
        self.st=st; self.name=name
    def __enter__(self):
        self.st._ctx_stack.append(self.name); return self
    def __exit__(self, exc_type, exc, tb):
        self.st._ctx_stack.pop(); return False
    def __getattr__(self, name):
        return getattr(self.st, name)

class ColConfig:
    def CheckboxColumn(self,*a,**k): return {'type':'checkbox','args':a,'kwargs':k}

class FakeStreamlit(types.ModuleType):
    def __init__(self, press_buttons=False, value_mode='sample'):
        super().__init__('streamlit')
        self.session_state=SessionState()
        self.press_buttons=press_buttons
        self.value_mode=value_mode
        self._ctx_stack=[]
        self.events=[]
        self.column_config=ColConfig()
        self.sidebar=Ctx(self,'sidebar')
    def _log(self,name,*args,**kwargs):
        self.events.append((name,args,kwargs, list(self._ctx_stack)))
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
    def tabs(self, labels):
        self._log('tabs',labels)
        return [Ctx(self, f'tab:{lab}') for lab in labels]
    def columns(self, spec):
        n = spec if isinstance(spec,int) else len(spec)
        self._log('columns',spec)
        return [Ctx(self, f'col:{i}') for i in range(n)]
    def expander(self, label, expanded=False):
        self._log('expander',label,expanded=expanded)
        return Ctx(self, f'expander:{label}')
    def selectbox(self,label, options, index=0, **kwargs):
        self._log('selectbox',label,options,index=index,**kwargs)
        if not options: return None
        # Keep default to avoid invalid choices, but prefer meaningful non-empty if default empty
        try:
            val=options[index]
        except Exception:
            val=options[0]
        if val=='' and len(options)>1:
            val=options[1]
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val)
        return self.session_state.get(key,val) if key else val
    def radio(self,label, options, index=0, **kwargs): return self.selectbox(label, options, index, **kwargs)
    def multiselect(self,label, options, default=None, **kwargs):
        self._log('multiselect',label,options,default=default,**kwargs)
        val = default if default is not None else []
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val)
        return self.session_state.get(key,val) if key else val
    def slider(self,label, min_value=None, max_value=None, value=None, step=None, **kwargs):
        self._log('slider',label,min_value,max_value,value,step,**kwargs)
        val=value if value is not None else min_value
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val)
        return self.session_state.get(key,val) if key else val
    def number_input(self,label, min_value=None, max_value=None, value=0, step=None, **kwargs):
        self._log('number_input',label,min_value,max_value,value,step,**kwargs)
        val=value
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val)
        return self.session_state.get(key,val) if key else val
    def checkbox(self,label, value=False, **kwargs):
        self._log('checkbox',label,value=value,**kwargs)
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,value)
        return self.session_state.get(key,value) if key else value
    def _sample_text(self,label, value=''):
        if value not in (None,''):
            return value
        label=str(label)
        if '원고' in label or '본문' in label or '초안' in label or '조사' in label or '내용' in label or '자료' in label or '사진' in label or '로그' in label:
            return '일산 매트리스 청소를 맡기기 전에는 소재, 얼룩 원인, 습식청소 가능 여부, 건조 시간, 오래된 오염의 한계를 확인해야 합니다. 사진 자료에는 작업 전 얼룩, 장비, 습식 작업 후 상태가 포함되어 있습니다. 새것처럼 복원된다는 표현은 피하고 확인 가능한 범위로 설명합니다.'
        if '업체' in label or '브랜드' in label:
            return '남편홈케어'
        if '주제' in label:
            return '일산 매트리스 청소 맡기기 전 확인할 점'
        if '키워드' in label:
            return '일산 매트리스 청소'
        if '지역' in label:
            return '일산'
        if '금지' in label:
            return '100% 제거, 새것처럼 복원, 완벽 보장'
        if '태그' in label:
            return '#일산매트리스청소 #매트리스청소 #홈케어'
        return '테스트 입력값'
    def text_input(self,label, value='', **kwargs):
        self._log('text_input',label,value=value,**kwargs)
        val=self._sample_text(label,value)
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val)
        return self.session_state.get(key,val) if key else val
    def text_area(self,label, value='', **kwargs):
        self._log('text_area',label,value=value,**kwargs)
        val=self._sample_text(label,value)
        key=kwargs.get('key')
        if key: self.session_state.setdefault(key,val)
        return self.session_state.get(key,val) if key else val
    def data_editor(self, data, **kwargs):
        self._log('data_editor',type(data).__name__,**kwargs)
        if isinstance(data, pd.DataFrame):
            df=data.copy()
            if '선택' in df.columns and self.press_buttons:
                # Keep whatever app chose, don't select all blindly
                pass
            return df
        return data
    def file_uploader(self,*a,**k): self._log('file_uploader',*a,**k); return None
    def button(self,label, *args, **kwargs):
        self._log('button',label,*args,**kwargs)
        if kwargs.get('disabled'): return False
        # avoid destructive/restore buttons in all-button test
        destructive=['전체 삭제','삭제','복원 실행']
        if any(x in str(label) for x in destructive): return False
        return self.press_buttons


def run_case(name, press=False):
    fake=FakeStreamlit(press_buttons=press)
    sys.modules['streamlit']=fake
    try:
        g=runpy.run_path(str(APP), run_name=f'__{name}__')
        return {'case':name,'ok':True,'events':len(fake.events),'errors':[], 'tabs':[e for e in fake.events if e[0]=='tabs'][:1]}
    except SystemExit as e:
        return {'case':name,'ok':True,'system_exit':str(e),'events':len(fake.events),'errors':[]}
    except Exception as e:
        return {'case':name,'ok':False,'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'events':len(fake.events)}

results=[]
for name,press in [('render_no_buttons',False),('all_non_destructive_buttons',True)]:
    results.append(run_case(name,press))

out=APP_DIR/'menu_1_15_fake_streamlit_results.json'
out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2)[:4000])
