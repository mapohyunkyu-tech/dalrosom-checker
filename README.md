# 달로썸 원고 검수기 v10.0.17

## 변경 사항
- ⑧ 최종 원고 검수 결과를 txt로 내려받는 공유용 리포트 기능 추가
- 총점, 항목별 점수, 핵심 수치, 키워드 배치, 항목별 보완 사유, 납품 리스크, 사람화 수정 제안, 원고 전문을 한 파일에 포함
- 보완/재작성 판정이 뜰 때 이 txt 파일을 ChatGPT에 올리면 문제 원인을 바로 확인할 수 있도록 구성

## 검사
- python -m py_compile app.py 통과
- run_menu_fake_test.py 통과
- run_integration_harmony_check.py 통과
- run_v1016_target_tests.py 통과
