# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import date, timedelta
import pandas as pd
import streamlit as st

from database import (
    EXPECTED_COUNTS, add_custom, category_map, delete_custom,
    load_database_df, load_evergreen, load_master_df, save_evergreen,
)
from engine import ApiConfig, NaverApiError, analyze, call_api, collect, to_excel
from settings_store import delete_credentials, load_settings, save_settings

st.set_page_config(page_title="MarketScout v2", page_icon="📈", layout="wide")
st.title("📈 MarketScout")
st.caption("마스터 CSV 하나만 사용하는 세부품목 제철 분석기 · v2.0")

settings = load_settings()
master_df = load_master_df()  # 943개가 아니면 여기서 즉시 중단
products = category_map()
db_df = load_database_df()


def secret_config():
    try:
        n = st.secrets["naver"]
        return ApiConfig(str(n["client_id"]), str(n["client_secret"]), str(n.get("auth_mode", "hub")))
    except Exception:
        return None


def saved_config():
    if settings.get("client_id") and settings.get("client_secret"):
        return ApiConfig(settings["client_id"], settings["client_secret"], settings.get("auth_mode", "hub"))
    return None

config = saved_config() or secret_config()
for key, default in {"results": None, "raw": None, "analysis_key": None}.items():
    st.session_state.setdefault(key, default)

tabs = st.tabs(["🏠 대시보드", "🔎 분석", "📅 캘린더", "🗂 DB 관리", "⚙️ 설정"])

with tabs[4]:
    st.subheader("NAVER API 설정")
    modes = {"hub":"NAVER API HUB", "legacy_ncp":"NAVER Cloud 기존 방식", "developer":"NAVER Developers 데이터랩"}
    mode = st.selectbox("인증 방식", list(modes), format_func=lambda x:modes[x], index=list(modes).index(settings.get("auth_mode","hub")) if settings.get("auth_mode","hub") in modes else 0)
    cid = st.text_input("Client ID", value=settings.get("client_id", ""))
    secret = st.text_input("Client Secret", value=settings.get("client_secret", ""), type="password")
    a,b,c = st.columns(3)
    if a.button("저장", type="primary", use_container_width=True):
        settings.update({"auth_mode":mode,"client_id":cid.strip(),"client_secret":secret.strip()}); save_settings(settings); st.success("저장했습니다."); st.rerun()
    if b.button("연결 테스트", use_container_width=True):
        try:
            call_api(ApiConfig(cid.strip(), secret.strip(), mode), ["사과"], (date.today()-timedelta(days=30)).isoformat(), date.today().isoformat(), 1)
            st.success("API 연결 성공")
        except Exception as exc: st.error(str(exc))
    if c.button("저장 키 삭제", use_container_width=True):
        delete_credentials(); st.success("삭제했습니다.")

with tabs[3]:
    st.subheader("품목 DB 관리")
    base_counts = master_df.groupby("대분류")["세부품목"].nunique().to_dict()
    total_counts = db_df.groupby("대분류")["세부품목"].nunique().to_dict()
    st.success("마스터 DB 검증 완료: 총 943개 · " + " · ".join(f"{k} {base_counts.get(k,0)}개" for k in EXPECTED_COUNTS))
    st.caption("분석·화면·다운로드 모두 data/detailed_products_943.csv와 사용자 추가 CSV만 사용합니다. products.py/products.json은 사용하지 않습니다.")
    st.info("현재 분석 DB: 총 {:,}개 · ".format(len(db_df)) + " · ".join(f"{k} {total_counts.get(k,0):,}개" for k in products))
    wm = db_df[(db_df["대분류"]=="과일") & db_df["세부품목"].str.contains("수박", na=False)][["기준품목","세부품목","구분"]]
    st.write("**수박류 개별 키워드**")
    st.dataframe(wm, hide_index=True, use_container_width=True)
    category = st.selectbox("카테고리", list(products), key="dbcat")
    group = db_df[db_df["대분류"]==category][["기준품목","세부품목","구분"]]
    st.dataframe(group, hide_index=True, use_container_width=True, height=420)
    st.divider()
    st.write("**사용자 품목 추가**")
    base_product = st.text_input("기준품목(예: 수박)")
    new_items = st.text_area("추가할 세부품목 — 한 줄에 하나", height=120)
    if st.button("품목 추가", type="primary"):
        n=add_custom(category, base_product, new_items.splitlines()); st.success(f"{n}개 추가했습니다."); st.rerun()
    custom = db_df[(db_df["대분류"]==category)&(db_df["구분"]=="사용자추가")]["세부품목"].tolist()
    if custom:
        remove = st.multiselect("삭제할 사용자 추가 품목", custom)
        if st.button("선택 품목 삭제"):
            n=delete_custom(category, remove); st.success(f"{n}개 삭제했습니다."); st.rerun()

with tabs[1]:
    st.subheader("월별 제철 분석")
    a,b,c,d=st.columns(4)
    target_year=int(a.number_input("적용 연도",2024,2035,date.today().year,1))
    target_month=int(b.selectbox("분석 월",range(1,13),index=max(0,min(11,int(settings.get("target_month",8))-1)),format_func=lambda x:f"{x}월"))
    top_n=int(c.selectbox("표시 개수",[20,30,50,100],index=2))
    exclude_low=d.checkbox("신뢰도 낮음 제외",value=False)
    selected=st.multiselect("분석할 카테고리", list(products), default=["과일"])
    st.caption("선택된 세부 키워드 수: {:,}개".format(sum(len(products[x]) for x in selected)))
    run=st.button("분석 시작",type="primary",disabled=(config is None or not selected),use_container_width=True)
    if config is None: st.warning("설정 탭에서 NAVER API 키를 먼저 저장하세요.")
    if run:
        all_items=[p for cat in selected for p in products[cat]]
        status=st.status("수집 중…",expanded=True); bar=st.progress(0)
        def progress(n,total,batch): bar.progress(n/total); status.write(f"{n}/{total} · {', '.join(batch)}")
        try:
            raw=collect(config,all_items,f"{target_year-3}-01-01",date.today().isoformat(),progress)
            results=analyze(raw,{cat:products[cat] for cat in selected},target_year,target_month)
            st.session_state.update(raw=raw,results=results,analysis_key=(target_year,target_month))
            status.update(label="분석 완료",state="complete",expanded=False)
        except NaverApiError as exc: status.update(label="API 오류",state="error"); st.error(str(exc))
        except Exception as exc: status.update(label="분석 실패",state="error"); st.exception(exc)
    results=st.session_state.results
    if results is not None:
        view=results.copy()
        if exclude_low: view=view[view["신뢰도"]!="하"]
        cats=[x for x in selected if x in set(view["카테고리"])] if not view.empty else []
        if cats:
            cat=st.segmented_control("카테고리",cats,default=cats[0])
            view=view[view["카테고리"]==cat].sort_values("계절성점수",ascending=False).head(top_n)
            cols=[x for x in ["카테고리순위","품목","현재상태","등록시작일","진입일","피크일","종료일","판매기간(일)","추천행동","신뢰도","계절성점수"] if x in view.columns]
            st.dataframe(view[cols],hide_index=True,use_container_width=True,height=650,column_config={"카테고리순위":st.column_config.NumberColumn("순위",format="%d"),"계절성점수":st.column_config.ProgressColumn("추천점수",min_value=0.0,max_value=100.0,format="%.1f")})
            st.download_button("전체 결과 Excel",to_excel(results,st.session_state.raw),file_name=f"MarketScout_v2_{target_year}_{target_month:02d}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tabs[0]:
    st.subheader("오늘 해야 할 일")
    results=st.session_state.results
    if results is None or results.empty:
        st.info("분석 탭에서 먼저 분석하세요.")
    else:
        today=date.today(); cards=[("상품 등록", "등록시작일"),("재고 확보","재고확보일"),("판매 시작","진입일"),("피크 대응","피크일"),("종료 임박","종료임박일")]
        columns=st.columns(len(cards))
        for col,(label,key) in zip(columns,cards): col.metric(label,int((pd.to_datetime(results[key]).dt.date==today).sum()))
        upcoming=[]
        for _,r in results.iterrows():
            for label,key in cards:
                day=pd.to_datetime(r[key]).date()
                if today<=day<=today+timedelta(days=14): upcoming.append({"날짜":day,"할 일":label,"품목":r["품목"],"카테고리":r["카테고리"]})
        st.dataframe(pd.DataFrame(upcoming).sort_values("날짜") if upcoming else pd.DataFrame(columns=["날짜","할 일","품목","카테고리"]),hide_index=True,use_container_width=True)

with tabs[2]:
    st.subheader("소싱 캘린더")
    results=st.session_state.results
    if results is None or results.empty: st.info("분석 결과가 없습니다.")
    else:
        events=[]
        for _,r in results.iterrows():
            for label,key in [("등록","등록시작일"),("발주","재고확보일"),("진입","진입일"),("피크","피크일"),("종료","종료일")]:
                events.append({"날짜":pd.to_datetime(r[key]).date(),"단계":label,"품목":r["품목"],"카테고리":r["카테고리"]})
        ev=pd.DataFrame(events).sort_values(["날짜","카테고리","품목"])
        st.dataframe(ev,hide_index=True,use_container_width=True,height=700)
