# MarketScout Streamlit

네이버 Search Trend를 이용해 선택한 월의 제철 판매 후보를 카테고리별 TOP 50으로 보여주는 Streamlit 앱입니다.

## 화면
- 과일을 누르면 과일만 표시
- 채소를 누르면 채소만 표시
- 수산물을 누르면 수산물만 표시
- 진입일, 피크일, 종료일, 판매기간, 현재 상태, 추천 행동, 신뢰도 표시
- 품목별 검색지수 그래프와 엑셀 다운로드
- 쌀, 잡곡, 축산, 계란, 상시 가공식품 및 그래프상 상시형 품목 제외

## GitHub 업로드
이 폴더의 파일을 전부 GitHub 저장소 루트에 올립니다. 실제 `secrets.toml`은 올리지 마세요. `.gitignore`에 이미 제외되어 있습니다.

## Streamlit Community Cloud 배포
1. GitHub 저장소를 Streamlit Community Cloud에 연결합니다.
2. Main file path는 `app.py`로 지정합니다.
3. 앱 설정의 Secrets에 아래 내용을 저장합니다.

```toml
[naver]
auth_mode = "hub"
client_id = "발급받은 Client ID"
client_secret = "발급받은 Client Secret"
```

`auth_mode` 값:
- `hub`: NAVER API HUB 신규 키(권장)
- `legacy_ncp`: 이전 NCP Search Trend 키
- `developer`: 2026-07-31 이전 NAVER Developers에서 신청한 기존 키

## 로컬 실행
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

## 인증 오류 024
`Scope Status Invalid (024)`가 뜨면 Client ID/Secret 자체의 오타보다 해당 키에 Search Trend 권한이 연결되어 있는지 먼저 확인하세요.

## 주의
네이버 트렌드 값은 절대 검색량이 아닌 상대지수입니다. 실제 출하 시기, 물량, 마진은 별도로 확인해야 합니다.
