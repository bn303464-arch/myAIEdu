# myAIEdu 클린 아키텍처 설계 (적용 대기)

대상은 루트 앱의 `server.py` + `db.py`다(`main.py`는 없음). 이 폴더는 단독으로 실행·테스트할 수 있다.

```powershell
cd refactor-proposal
python -m unittest discover -s tests -v
$env:AIEDU_DB = "$env:TEMP\aiedu-check.db"
python src/back/server.py --port 8000
Remove-Item Env:AIEDU_DB
```

## 구조도

```
브라우저 (src/front)
      │ HTTP
      ▼
 web/handler ──► web/static_files
      │ Router
      ▼
  routers ──► services ──► ports (Protocol)
                 │              ▲ 구현
                 ▼              │
               models ◄── repositories ──► SQLite

 server.py : 위 객체를 조립
```

화살표는 호출·의존 방향이다. `models`는 어디에도 의존하지 않고, `services`는 SQLite를 모른다.

## 요청 흐름: 수강 신청

1. `web/handler`: `POST /api/enroll`을 라우터에서 찾는다.
2. `routers/enrollment_router`: 본문을 읽고 `EnrollmentRequest.parse()`로 검증한다.
3. `services/enrollment_service`: 트랜잭션 안에서 과정 확인 → 정원 확인 → 수강생 조회·생성 → 신청 저장.
4. 실패하면 도메인 예외가 올라가고 롤백된다. `web/handler`가 400·404·409로 바꾼다.

## 이전 코드의 새 위치

| 이전 | 이후 |
|---|---|
| `db.SEED_LESSONS` | `repositories/seed.py` |
| `db.AppError(status, message)` | `models/errors.py` |
| `db._clean` | `models/enrollment.py` `EnrollmentRequest.parse` |
| `db.connect`, `db.init_db` | `repositories/database.py` |
| `db.list_courses`, `db.curriculum` | `services/course_service.py` + `repositories/course_repository.py` |
| `db.enroll` | `services/enrollment_service.py` + 저장소 |
| `db.db_path` | `config.py` |
| `server.Handler` | `web/` + `routers/` |
| `schema.sql` | `repositories/schema.sql` |
| `static/` | `src/front/` (내용 변경 없음) |

## 설계 결정

- 웹 프레임워크와 ORM을 넣지 않는다(표준 라이브러리 원칙).
- 저장소 인터페이스는 `typing.Protocol`이며, 서비스 테스트는 가짜 DB로 한다.
- 트랜잭션 경계는 서비스가 정하고, `BEGIN IMMEDIATE` 구현은 저장소가 맡는다.
- API, URL, 화면, DB 스키마, 기본 DB 위치(프로젝트 루트 `app.db`)는 바꾸지 않는다.

## 검증 (2026-11-25, Python 3.12.7)

- 이전 서버와 새 서버에 같은 요청 92건: 상태·헤더(`Date` 제외)·본문 차이 0건.
- 두 DB의 스키마와 저장 데이터(시각 컬럼 제외) 동일.
- 단위·API·구조 테스트 결과는 위 테스트 명령으로 확인한다.

## 기존 동작에서 발견한 문제 (이번에는 그대로 유지)

| 문제 | 확인 방법 | 제안 |
|---|---|---|
| `name`, `occupation`이 `null`이면 문자열 `"None"`으로 저장됨 | 요청 비교에서 재현 | `parse()`에서 `None`을 빈 문자열로 처리 |
| 아주 큰 정수의 `course_id`·경로는 응답 없이 연결이 끊김 | 요청 비교에서 재현 | 범위 검사와 500 JSON 처리 추가 |
| 같은 번호로 다시 신청하면 이름 등 수강생 정보가 갱신되지 않음 | 코드 확인 | 정책 결정 필요 |
| `dropped` 상태에서는 같은 과정에 재신청할 수 없음 | 코드 확인 | 정책 결정 필요 |

## 적용 순서

1. 서버를 끄고, 현재 소스를 백업한다(Git 저장소가 아님).
2. 제안 작성 이후 원본이 바뀌었으면 먼저 반영한다.
3. `src/`와 `tests/`의 파일을 프로젝트 루트로 복사한다(`tests/test_api.py`는 교체).
4. 루트의 `server.py`, `db.py`, `schema.sql`, `static/`을 삭제한다. 남아 있으면 구조 테스트가 실패한다.
5. `CLAUDE.md`의 실행 명령(`python src/back/server.py --port 8000`)과 Structure, `SEED_LESSONS` 위치를 고친다.
6. `.claude/rules/architecture.md`의 "현재 상태" 절을 삭제한다.
7. 테스트와 화면 확인 후 `refactor-proposal/`을 삭제한다.
