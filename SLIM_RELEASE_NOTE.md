# 달로썸 v10.0.29 Slim Release

이 배포본은 실행에 필요한 파일만 포함한 슬림 버전입니다.

포함 파일:
- app.py
- requirements.txt
- README.md
- client_presets.json
- custom_weird_sentence_db.json
- custom_weird_pattern_db.json
- dalrosom_settings.json
- retainer_clients.json
- quote_history.json
- portfolio_samples.json
- work_log.json

제외 파일:
- __pycache__
- run_* 테스트 파일
- patch_* 작업 파일
- target_*.out / integration_*.out / menu_*.out
- *_target_tests.json
- backtest/audit 리포트 파일

실행:
```bash
pip install -r requirements.txt
streamlit run app.py
```
