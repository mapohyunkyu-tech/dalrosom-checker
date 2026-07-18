# -*- coding: utf-8 -*-
from datetime import date
import pandas as pd
import streamlit as st
from engine import ApiConfig, NaverApiError, analyze, collect, to_excel
from products import PRODUCTS

st.set_page_config(page_title="MarketScout 제철 선점", page_icon="📈", layout="wide")
st.title("📈 MarketScout 제철 선점")
st.caption("항상 팔리는 품목은 제외하고, 선택한 달의 과일·채소·수산물·버섯 TOP 50을 표시합니다.")

def load_config():
    try:
        n=st.secrets["naver"]
        return ApiConfig(str(n["client_id"]),str(n["client_secret"]),str(n.get("auth_mode","hub")))
    except Exception:
        return None

config=load_config()
with st.sidebar:
    st.header("분석 설정")
    target_year=st.number_input("적용 연도",min_value=2024,max_value=2035,value=date.today().year,step=1)
    target_month=st.selectbox("분석 월",range(1,13),index=7,format_func=lambda x:f"{x}월")
    top_n=st.slider("카테고리 표시 개수",10,100,50,10)
    st.divider()
    if config:
        st.success(f"NAVER API 연결 설정됨 ({config.auth_mode})")
        st.caption(f"Client ID: {'*'*max(4,len(config.client_id)-4)}{config.client_id[-4:]}")
    else:
        st.error(".streamlit/secrets.toml 또는 Community Cloud Secrets에 API 키를 저장하세요.")
    run=st.button("전체 카테고리 분석 시작",type="primary",use_container_width=True,disabled=config is None)

if "results" not in st.session_state: st.session_state.results=None
if "raw" not in st.session_state: st.session_state.raw=None
if "analysis_key" not in st.session_state: st.session_state.analysis_key=None

if run:
    all_items=[]
    for values in PRODUCTS.values(): all_items.extend(values)
    status=st.status("네이버 검색 트렌드를 수집하고 있습니다…",expanded=True)
    bar=st.progress(0)
    def progress(n,total,batch):
        bar.progress(n/total); status.write(f"{n}/{total} · {', '.join(batch)}")
    try:
        # 완료된 최근 3개년 + 적용연도 현재자료까지 넉넉히 수집
        start_year=min(int(target_year)-3,date.today().year-3)
        end_year=max(int(target_year),date.today().year)
        end_date=min(date.today(),date(end_year,12,31))
        raw=collect(config,all_items,f"{start_year}-01-01",end_date.isoformat(),progress)
        results=analyze(raw,PRODUCTS,int(target_year),int(target_month))
        st.session_state.raw=raw; st.session_state.results=results; st.session_state.analysis_key=(target_year,target_month)
        status.update(label="분석 완료",state="complete",expanded=False)
    except NaverApiError as exc:
        status.update(label="API 오류",state="error"); st.error(str(exc))
    except Exception as exc:
        status.update(label="분석 실패",state="error"); st.exception(exc)

results=st.session_state.results
if results is None:
    st.info("왼쪽에서 월을 고르고 ‘전체 카테고리 분석 시작’을 누르세요. 분석은 한 번만 실행하며, 이후 카테고리 버튼은 즉시 바뀝니다.")
    st.stop()

ay,am=st.session_state.analysis_key
st.subheader(f"{ay}년 {am}월 제철 후보")
counts=results.groupby("카테고리").size().to_dict() if not results.empty else {}
category=st.segmented_control("카테고리",list(PRODUCTS.keys()),default="과일",format_func=lambda x:f"{x} ({counts.get(x,0)})")
category=category or "과일"
view=results[results["카테고리"]==category].head(top_n).copy()
if view.empty:
    st.warning(f"{category}에서 선택 월과 시즌이 겹치는 품목이 없습니다.")
else:
    show_cols=["카테고리순위","품목","진입일","피크일","종료일","판매기간(일)","현재상태","진입까지(일)","추천행동","신뢰도","계절성점수"]
    st.dataframe(view[show_cols],hide_index=True,use_container_width=True,height=720,
        column_config={"카테고리순위":st.column_config.NumberColumn("순위",format="%d"),"계절성점수":st.column_config.ProgressColumn("계절성점수",min_value=0,max_value=100,format="%.1f")})
    selected=st.selectbox("그래프 확인 품목",view["품목"].tolist())
    series=st.session_state.raw[selected].dropna().rename("검색지수")
    if not series.empty:
        st.line_chart(series,use_container_width=True)

c1,c2=st.columns(2)
with c1:
    st.download_button(f"{category} TOP {top_n} 엑셀 다운로드",to_excel(view,st.session_state.raw[[x for x in view['품목'] if x in st.session_state.raw.columns]]),file_name=f"MarketScout_{ay}_{am:02d}_{category}_TOP{top_n}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
with c2:
    st.download_button("전체 결과 엑셀 다운로드",to_excel(results,st.session_state.raw),file_name=f"MarketScout_{ay}_{am:02d}_전체.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)

with st.expander("제외 기준과 판정 방식"):
    st.markdown("""
- 쌀·잡곡·콩·소고기·돼지고기·닭·계란·상시 가공식품은 분석 대상에서 처음부터 제외합니다.
- 남은 품목도 월별 그래프가 거의 평평하고 연중 활성 월이 많은 경우 `상시형`으로 판정해 숨깁니다.
- 최근 완료된 최대 3개년의 진입일·피크일·종료일을 평균해 적용 연도의 날짜로 환산합니다.
- 프로그램은 후보 순위를 정하는 도구이며, 이상한 그래프나 실제 출하 여부는 최종적으로 직접 확인해야 합니다.
""")
