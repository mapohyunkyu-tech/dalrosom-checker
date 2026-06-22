# 달로썸 원고 검수기 v2.1 - 자동 자료수집 + 관련도 필터 버전

키워드/주제를 입력하면 Tavily API로 자료를 자동 수집하고, 출처 등급 A/B/C/제외와 주제 관련도 높음/보통/낮음을 함께 표시합니다.

## v2.1 개선점

- A등급이어도 주제와 멀면 A-보조 또는 제외로 낮춤
- 복합성 피부 주제 검색어를 T존/U존/유수분/피지/속건조 중심으로 조정
- 중복 URL 자동 제거
- 자료표에 관련도/관련도점수/리체크 사유 표시

## GitHub에 올릴 파일

- app.py
- requirements.txt
- README.md

## Streamlit Secrets 설정

Streamlit Cloud 앱 설정에서 Secrets에 아래처럼 입력하세요.

```toml
TAVILY_API_KEY = "tvly-본인키"
```

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```
