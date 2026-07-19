# MarketScout v2.0

943개 마스터 CSV를 단일 원본으로 사용하는 Streamlit 앱입니다.

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub 업로드
이 폴더 안의 내용물을 저장소 루트에 올립니다. `app.py`가 첫 화면에 바로 보여야 합니다.

## DB 구조
- `data/detailed_products_943.csv`: 고정 마스터 DB 943개
- `data/custom_products.csv`: 앱에서 사용자가 추가한 품목만 저장
- `products.py`, `products.json`은 존재하지도 사용하지도 않습니다.
