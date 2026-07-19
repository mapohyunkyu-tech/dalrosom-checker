# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import date, timedelta
import pandas as pd
import streamlit as st

from database import load_evergreen, load_products, reset_products, save_evergreen, save_products
from engine import ApiConfig, NaverApiError, analyze, call_api, collect, to_excel
from settings_store import delete_credentials, load_settings, save_settings

st.set_page_config(page_title="MarketScout", page_icon="📈", layout="wide")
st.title("📈 MarketScout")
st.caption("943개 세부품목을 각각 별도 키워드로 분석해 D-14 등록, 진입, 피크, 종료까지 관리합니다. · v1.0.5")

settings = load_settings()
products = load_products()

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
    st.caption("로컬 실행에서는 이 PC의 사용자 폴더에 암호화되지 않은 설정 파일로 저장됩니다. 공용 PC에서는 저장하지 마세요. Streamlit Cloud는 앱 Secrets 사용을 권장합니다.")
    mode_labels = {
        "hub": "NAVER API HUB (2026년 신규 권장)",
        "legacy_ncp": "NAVER Cloud Search Trend (기존 NCP)",
        "developer": "NAVER Developers 데이터랩 (구형 키)",
    }
    auth_mode = st.selectbox(
        "인증 방식",
        list(mode_labels),
        index=list(mode_labels).index(settings.get("auth_mode", "hub")) if settings.get("auth_mode", "hub") in mode_labels else 0,
        format_func=lambda x: mode_labels[x],
    )
    st.info("API HUB에서 발급한 키는 ‘NAVER API HUB’를 선택하세요. developers.naver.com에서 발급한 키는 ‘NAVER Developers 데이터랩’을 선택해야 합니다.")
    cid = st.text_input("Client ID", value=settings.get("client_id", ""))
    csecret = st.text_input("Client Secret", value=settings.get("client_secret", ""), type="password")
    c1,c2,c3 = st.columns(3)
    if c1.button("저장", type="primary", use_container_width=True):
        settings.update({"auth_mode":auth_mode,"client_id":cid.strip(),"client_secret":csecret.strip()})
        save_settings(settings); st.success("저장했습니다."); st.rerun()
    if c2.button("연결 테스트", use_container_width=True):
        try:
            test = ApiConfig(cid.strip(), csecret.strip(), auth_mode)
            call_api(test,["사과"],(date.today()-timedelta(days=30)).isoformat(),date.today().isoformat(),1)
            st.success("Search Trend API 연결 성공")
        except Exception as exc: st.error(str(exc))
    if c3.button("저장 키 삭제", use_container_width=True):
        delete_credentials(); st.success("저장된 키를 삭제했습니다. 새로고침하세요.")

with tabs[3]:
    st.subheader("품목 DB 관리")
    st.info(f"현재 세부품목 DB: 총 {sum(len(v) for v in products.values()):,}개 · " + " · ".join(f"{k} {len(v):,}개" for k,v in products.items()))
    st.caption("DB 원본: data/detailed_products_943.csv · 강제 검증: 943개")
    if "과일" in products:
        watermelon = [x for x in products["과일"] if "수박" in x]
        st.caption("수박류 개별 분석 키워드: " + ", ".join(watermelon))
    category = st.selectbox("카테고리", list(products.keys()), key="db_category")
    edited = st.text_area("한 줄에 한 품목", value="\n".join(products[category]), height=360)
    c1,c2=st.columns(2)
    if c1.button("이 카테고리 저장", type="primary", use_container_width=True):
        products[category]=[x.strip() for x in edited.splitlines() if x.strip()]
        save_products(products); st.success("저장했습니다.")
    if c2.button("기본 DB로 초기화", use_container_width=True):
        reset_products(); st.success("초기화했습니다. 새로고침하세요.")
    st.divider()
    evergreen=load_evergreen()
    ever_text=st.text_area("상시 판매 제외 품목", value="\n".join(evergreen), height=180)
    if st.button("상시 품목 저장"):
        save_evergreen([x.strip() for x in ever_text.splitlines() if x.strip()]); st.success("저장했습니다.")

with tabs[1]:
    st.subheader("월별 제철 분석")
    a,b,c,d=st.columns([1,1,1,1])
    target_year=int(a.number_input("적용 연도",2024,2035,date.today().year,1))
    target_month=int(b.selectbox("분석 월",range(1,13),index=max(0,min(11,int(settings.get("target_month",8))-1)),format_func=lambda x:f"{x}월"))
    top_n=int(c.selectbox("표시 개수",[20,30,50,100],index=[20,30,50,100].index(settings.get("top_n",50)) if settings.get("top_n",50) in [20,30,50,100] else 2))
    exclude_low=d.checkbox("신뢰도 낮음 제외",value=bool(settings.get("exclude_low_confidence",False)))
    selected_run_categories = st.multiselect(
        "분석할 카테고리",
        list(products.keys()),
        default=[list(products.keys())[0]],
        help="세부품목이 943개이므로 필요한 카테고리만 선택하면 API 호출 시간을 크게 줄일 수 있습니다.",
    )
    run=st.button("선택 카테고리 분석 시작",type="primary",disabled=(config is None or not selected_run_categories),use_container_width=True)
    if config is None: st.warning("먼저 설정 탭에서 NAVER API 키를 저장하세요.")
    if run:
        settings.update({"target_month":target_month,"top_n":top_n,"exclude_low_confidence":exclude_low}); save_settings(settings)
        all_items=[]
        for cat in selected_run_categories: all_items.extend(products[cat])
        status=st.status("검색 트렌드를 수집하고 있습니다…",expanded=True); bar=st.progress(0)
        def progress(n,total,batch): bar.progress(n/total); status.write(f"{n}/{total} · {', '.join(batch)}")
        try:
            start_year=min(target_year-3,date.today().year-3); end_year=max(target_year,date.today().year)
            end_date=min(date.today(),date(end_year,12,31))
            raw=collect(config,all_items,f"{start_year}-01-01",end_date.isoformat(),progress)
            results=analyze(raw,{cat: products[cat] for cat in selected_run_categories},target_year,target_month)
            st.session_state.update(raw=raw,results=results,analysis_key=(target_year,target_month))
            status.update(label="분석 완료",state="complete",expanded=False)
        except NaverApiError as exc: status.update(label="API 오류",state="error"); st.error(str(exc))
        except Exception as exc: status.update(label="분석 실패",state="error"); st.exception(exc)

    results=st.session_state.results
    if results is not None:
        ay,am=st.session_state.analysis_key
        if exclude_low: results=results[results["신뢰도"]!="하"]
        counts=results.groupby("카테고리").size().to_dict() if not results.empty else {}
        available_categories=[x for x in products.keys() if x in counts]
        category=st.segmented_control("카테고리",available_categories,default=available_categories[0],format_func=lambda x:f"{x} ({counts.get(x,0)})") or available_categories[0]
        sort_by=st.selectbox("정렬",["추천순","등록시작일순","진입일순","종료일순"])
        view=results[results["카테고리"]==category].copy()
        sort_map={"추천순":("계절성점수",False),"등록시작일순":("등록시작일",True),"진입일순":("진입일",True),"종료일순":("종료일",True)}
        col,asc=sort_map[sort_by]; view=view.sort_values(col,ascending=asc).head(top_n)
        cols=["카테고리순위","품목","등록시작일","재고확보일","진입일","피크일","종료일","현재상태","추천행동","신뢰도","계절성점수"]
        st.dataframe(view[cols],hide_index=True,use_container_width=True,height=650,column_config={"카테고리순위":st.column_config.NumberColumn("순위",format="%d"),"계절성점수":st.column_config.ProgressColumn("추천점수", min_value=0.0, max_value=100.0, format="%.1f")})
        if not view.empty:
            selected=st.selectbox("품목 상세",view["품목"].tolist())
            row=view[view["품목"]==selected].iloc[0]
            m1,m2,m3,m4,m5=st.columns(5)
            m1.metric("등록 시작",str(row["등록시작일"])); m2.metric("재고 확보",str(row["재고확보일"])); m3.metric("판매 진입",str(row["진입일"])); m4.metric("피크",str(row["피크일"])); m5.metric("종료",str(row["종료일"]))
            series=st.session_state.raw[selected].dropna().rename("검색지수")
            if not series.empty: st.line_chart(series,use_container_width=True)
        x1,x2,x3=st.columns(3)
        x1.download_button("현재 화면 Excel",to_excel(view,st.session_state.raw[[x for x in view['품목'] if x in st.session_state.raw.columns]]),f"MarketScout_{ay}_{am:02d}_{category}.xlsx",use_container_width=True)
        x2.download_button("현재 화면 CSV",view.to_csv(index=False).encode("utf-8-sig"),f"MarketScout_{ay}_{am:02d}_{category}.csv","text/csv",use_container_width=True)
        x3.download_button("전체 결과 Excel",to_excel(results,st.session_state.raw),f"MarketScout_{ay}_{am:02d}_전체.xlsx",use_container_width=True)

with tabs[0]:
    st.subheader("오늘 해야 할 일")
    results=st.session_state.results
    if results is None:
        st.info("분석 탭에서 먼저 월별 분석을 실행하세요.")
    else:
        today=date.today()
        groups=[("🔵 상품 등록(D-14)","등록시작일"),("🟡 재고 확보(D-7)","재고확보일"),("🟠 광고 준비(D-3)","광고준비일"),("🟢 판매 시작","진입일"),("🔥 피크 대응","피크일"),("🔴 종료 임박","종료임박일")]
        cards=st.columns(3)
        for i,(label,col) in enumerate(groups):
            due=results[results[col]==today]
            cards[i%3].metric(label,len(due))
            if len(due): cards[i%3].caption(", ".join(due["품목"].head(8)))
        st.divider()
        upcoming=[]
        for _,r in results.iterrows():
            for label,col in groups:
                dt=r[col]
                if today <= dt <= today+timedelta(days=14): upcoming.append({"날짜":dt,"업무":label.replace("🔵 ","").replace("🟡 ","").replace("🟠 ","").replace("🟢 ","").replace("🔥 ","").replace("🔴 ",""),"품목":r["품목"],"카테고리":r["카테고리"]})
        up=pd.DataFrame(upcoming)
        if up.empty: st.info("앞으로 14일 안에 잡힌 일정이 없습니다.")
        else: st.dataframe(up.sort_values(["날짜","업무","품목"]),hide_index=True,use_container_width=True)

with tabs[2]:
    st.subheader("소싱 캘린더")
    results=st.session_state.results
    if results is None:
        st.info("분석 탭에서 먼저 월별 분석을 실행하세요.")
    else:
        event_types={"등록 시작":"등록시작일","재고 확보":"재고확보일","광고 준비":"광고준비일","판매 시작":"진입일","피크":"피크일","종료 임박":"종료임박일","종료":"종료일"}
        selected_types=st.multiselect("표시 일정",list(event_types),default=list(event_types))
        selected_categories=st.multiselect("카테고리",list(products),default=list(products))
        events=[]
        for _,r in results[results["카테고리"].isin(selected_categories)].iterrows():
            for label in selected_types: events.append({"날짜":r[event_types[label]],"일정":label,"품목":r["품목"],"카테고리":r["카테고리"]})
        cal=pd.DataFrame(events).sort_values(["날짜","카테고리","품목"])
        st.dataframe(cal,hide_index=True,use_container_width=True,height=720)
        st.download_button("캘린더 CSV 다운로드",cal.to_csv(index=False).encode("utf-8-sig"),"MarketScout_calendar.csv","text/csv")
