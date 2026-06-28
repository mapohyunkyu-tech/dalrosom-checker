from pathlib import Path
s = Path('app.py').read_text(encoding='utf-8')
checks = []
checks.append(('version_label_1022', 'v10.0.22' in s))
checks.append(('no_post_widget_r_author_assignment', 'st.session_state["r_author_narration"] = r_author_narration' not in s))
checks.append(('applied_author_narration_saved', 'st.session_state["applied_author_narration"] = d_author_narration' in s))
checks.append(('r_author_widget_exists', 'key="r_author_narration"' in s))
failed = [name for name, ok in checks if not ok]
print({'total': len(checks), 'pass': len(checks)-len(failed), 'failed': failed})
raise SystemExit(1 if failed else 0)
