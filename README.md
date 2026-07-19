# MarketScout v3.0 제철판매판

과일·채소·수산물·버섯·견과/특용 품목의 NAVER DataLab 계절성을 분석하고, 등록·소싱·광고·판매 일정을 보여주는 Streamlit 앱입니다.

## 핵심 변경

- DB 행 수를 943개로 고정하던 검사를 완전히 제거했습니다.
- `data/detailed_products_master.csv` 한 파일을 마스터 DB로 사용합니다.
- 현재 포함 DB: 총 1,165개 품목
- 산지명, 별칭, 제철 월, 상품등록 권장월, 판매우선도 열을 포함합니다.
- 사용자 추가 품목은 `data/custom_products.csv`에 별도로 저장됩니다.

## Streamlit Cloud 배포

1. 압축을 풀고 폴더 안 파일 전체를 GitHub 저장소 최상단에 업로드합니다.
2. Streamlit Cloud에서 Main file path를 `app.py`로 지정합니다.
3. 앱의 `설정` 탭에서 NAVER API Client ID와 Client Secret을 입력합니다.

기존 저장소에 덮어쓸 때는 예전 `database.py`와 `data/detailed_products_943.csv`를 남겨두지 않는 것이 안전합니다.

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```
