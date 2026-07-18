# MarketScout v1.0

네이버 Search Trend를 이용해 제철 상품 후보를 찾고, **진입 14일 전 상품 등록부터 피크·종료까지** 소싱 일정을 관리하는 Streamlit 앱입니다. 쿠팡 API 연동은 없습니다.

## 주요 기능
- 과일·채소·수산물·버섯 카테고리별 TOP 20/30/50/100
- 등록 시작(D-14), 재고 확보(D-7), 광고 준비(D-3), 판매 진입, 피크, 종료 임박, 종료일 자동 계산
- 오늘 해야 할 일 대시보드와 14일 일정
- 품목별 최근 3년 검색 트렌드 그래프
- 품목 DB 및 상시 제외 품목 직접 편집
- Excel/CSV 다운로드
- 앱 안에서 NAVER Client ID/Secret 저장 및 연결 테스트

## 실행
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## API 키 저장
로컬 실행 시 설정 탭에서 저장한 키는 사용자 홈의 `.marketscout/settings.json`에 저장됩니다. 암호화 저장이 아니므로 공용 PC에서는 사용하지 마세요.

Streamlit Community Cloud에서는 앱의 **Secrets**에 아래 형식으로 넣는 것을 권장합니다.
```toml
[naver]
auth_mode = "hub"
client_id = "YOUR_ID"
client_secret = "YOUR_SECRET"
```

## GitHub 업로드
이 폴더의 파일을 저장소 루트에 올리고 Main file path를 `app.py`로 설정하세요. 실제 `.streamlit/secrets.toml`은 올리지 마세요.
