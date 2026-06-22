# 달로썸 원고 검수기 v2 - 자동 자료수집 버전

키워드/주제를 입력하면 Tavily API로 자료를 자동 수집하고, 출처 등급 A/B/C/제외를 매긴 뒤, 사용자가 링크를 확인하고 체크할 수 있게 만든 Streamlit 앱입니다.

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

## 흐름

1. 원고 목적/분야/키워드/주제 입력
2. 자동 자료수집
3. 출처등급 A/B/C/제외 표시
4. 사용자가 링크 확인 후 사용 여부 체크
5. GPTs에 넣을 핵심자료 정리
6. GPTs 초안 붙여넣기
7. 제목/도입/SEO/AI티/위험표현/마무리 검수
