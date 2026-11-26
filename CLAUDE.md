# CLAUDE.md

4050 AI 입문 8주 과정의 커리큘럼 조회와 수강 신청을 제공하는 웹 서비스 MVP. Python 표준 라이브러리만 사용한다.

## Commands
- 실행: `python server.py --port 8000` → http://127.0.0.1:8000
- 테스트: `python -m unittest discover -s tests -v` (임시 DB 사용)

## Structure
- `server.py`: HTTP 라우팅과 정적 파일 서빙. `db.py`: SQLite 접근과 신청 규칙(정원, 중복, 검증). `schema.sql`: 스키마.
- `static/`: 프론트엔드(index.html, style.css, app.js). 서버 렌더링 없이 `/api`를 호출한다.

## Notes
- `app.db`는 수강생 개인정보를 담으므로 실험·테스트에 쓰지 않는다. 테스트는 `AIEDU_DB` 환경변수로 임시 경로를 지정한다.
- 커리큘럼은 `db.py`의 `SEED_LESSONS` 가안이다. 확정되면 수정하고, 이미 만들어진 `app.db`는 삭제 후 재생성해야 반영된다.
- 사용자 대상 문구는 한국어로 유지한다.
