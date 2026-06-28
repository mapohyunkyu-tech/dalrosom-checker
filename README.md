# 달로썸 원고 검수기 v10.0.10

v10.0.10은 기능 추가가 아니라, 실제 GPTs 프롬프트 내부의 충돌·찌꺼기·분량 누락 위험을 항목별로 점검하고 보정한 버전입니다.

## 수정 내용

- B등급 고민 라벨이 첫문장 후보에 섞이는 문제 보정
- 긴 B등급 고민 한 줄을 실제 고민 단위로 분리
- `[3] B등급 잠재고객 고민패턴 때문에...` 같은 문장 생성 위험 제거
- `21500자`, `10003곳`처럼 숫자와 단위가 붙어 깨지는 지시문 생성 위험 점검
- `짧으면 압축` 계열의 분량 충돌 문구 제거
- 조사 프롬프트의 `압축하거나 확장` 표현을 `보강하거나 정리`로 변경
- 초안 프롬프트에 출력 전 자체 점검 블록 추가
- ③은 GPTs 초안 설계 단계, ⑧은 Claude 패키지/검수 단계로 역할 분리 유지

## 검사 결과

- `python -m py_compile app.py` 통과
- `run_menu_fake_test.py` 통과
- `run_integration_harmony_check.py` 통과
- `run_100_sample_backtest.py` 통과
- `run_prompt_audit.py` 통과

## 포함 리포트

- `prompt_audit_generated_prompt.txt`
- `prompt_audit_report.json`
- `v1010_prompt_consistency_audit.csv`
- `v1010_prompt_consistency_audit.json`
