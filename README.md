# 달로썸 원고 검수기 v10.0.22

## 핫픽스
- v10.0.21에서 `작성자 서술 강도` 위젯 생성 후 같은 key(`r_author_narration`)를 `st.session_state`에 다시 쓰면서 StreamlitAPIException이 발생하던 문제를 수정했습니다.
- ③/⑧ 자동 적용 흐름에서 사용할 수 있도록 `applied_author_narration` 저장을 별도 key로 분리했습니다.

## 확인
- `python -m py_compile app.py` 통과
- `run_menu_fake_test.py` 통과
- `run_integration_harmony_check.py` 통과
- `run_v1021_target_tests.py` 통과
- `run_v1022_target_tests.py` 통과
