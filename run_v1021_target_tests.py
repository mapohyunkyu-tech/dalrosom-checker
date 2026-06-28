import importlib.util, sys, types, json

# Fake streamlit for import if needed
class Dummy:
    def __init__(self):
        self.session_state = {}
    def __getattr__(self, name):
        if name == 'sidebar': return Dummy()
        def f(*args, **kwargs):
            if name == 'tabs': return [Dummy() for _ in (args[0] if args else [])]
            if name == 'expander': return Dummy()
            if name == 'columns':
                n = args[0] if args else 1
                if isinstance(n, (list, tuple)): n = len(n)
                return [Dummy() for _ in range(n)]
            if name == 'selectbox': return args[1][0] if len(args)>1 and args[1] else None
            if name == 'multiselect': return kwargs.get('default', [])
            if name == 'text_input': return kwargs.get('value','')
            if name == 'text_area': return kwargs.get('value','')
            if name == 'checkbox': return kwargs.get('value', False)
            if name == 'radio': return args[1][kwargs.get('index',0)] if len(args)>1 else None
            if name == 'number_input': return kwargs.get('value',0)
            if name == 'slider': return kwargs.get('value',0)
            if name == 'button': return False
            return None
        return f
    def __enter__(self): return self
    def __exit__(self,*a): return False

sys.modules['streamlit'] = Dummy()
spec = importlib.util.spec_from_file_location('app','app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

results=[]

def check(name, cond, detail=''):
    results.append({'name':name,'pass':bool(cond),'detail':detail})

check('AUTHOR_NARRATION_OPTIONS exists', hasattr(app,'AUTHOR_NARRATION_OPTIONS'))
check('direct narration resolves', app.resolve_author_narration('대표자 직접 서술형','피부과 원장/전문의','대표자 주장형','','','매출 전환형','OO의원','병원 / 의료')=='대표자 직접 서술형')
block=app.author_narration_block('대표자 직접 서술형','피부과 원장/전문의','대표자 주장형','','','매출 전환형','OO의원','병원 / 의료')
check('direct block has 저는', '저는' in block and '저희' in block, block[:200])
block2=app.author_narration_block('대표자 직접 서술형','피부과 원장/전문의','대표자 주장형','','','매출 전환형','','병원 / 의료')
check('no brand warns no 저희 병원', '업체명/병원명이 없으므로' in block2, block2[:200])
tone=app.apply_author_narration_to_tone('차분하게 작성','대표자 직접 서술형','피부과 원장/전문의','대표자 주장형','선택 기준형','책임 진료/책임 작업 강조형','매출 전환형','OO의원','병원 / 의료')
check('tone augmented', '[작성자 서술 강도' in tone and '대표자 직접 서술형' in tone, tone[:300])
prompt=app.build_draft_prompt(topic='써마지 시술', keyword='써마지', field='병원 / 의료', content_type='전문가 설명형', voice_type='비교 고민형', intro_type='1. 독자의 상황을 찔러주는 체크리스트 활용', title_type='4. 궁금증 자극형', a_lines=['써마지는 고주파 에너지를 이용한다.'], b_lines=['효과와 통증 비용이 헷갈린다.'], c_lines=[], article_style='매출 전환형', writer_perspective='피부과 원장/전문의', brand_name='OO의원', tone_detail=tone, primary_gyeol='대표자 주장형', secondary_gyeol_1='선택 기준형', secondary_gyeol_2='책임 진료/책임 작업 강조형', prompt_mode='일반 GPT용')
check('prompt includes narration', '[작성자 서술 강도' in prompt and '대표자 직접 서술형' in prompt, prompt[:500])
failed=[r for r in results if not r['pass']]
print(json.dumps({'summary':{'total':len(results),'pass':len(results)-len(failed),'error':len(failed)}, 'failed':failed}, ensure_ascii=False, indent=2))
raise SystemExit(1 if failed else 0)
