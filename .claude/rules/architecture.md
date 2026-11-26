# myAIEdu 아키텍처 규칙

이 프로젝트에서 작성·수정하는 모든 코드는 아래 규칙을 따른다. 규칙과 충돌하는 요청을 받으면 먼저 알리고 확인을 받는다.

## 현재 상태 (2026-11-25, 마이그레이션 적용 후 이 절 삭제)

- 루트의 `server.py`, `db.py`, `schema.sql`, `static/`은 이전 구조다. 적용 대기 중인 새 구조는 `refactor-proposal/`에 있다.
- 이전 구조 파일에는 버그 수정만 한다. 새 기능은 마이그레이션을 먼저 적용한 뒤 `src/`에 작성한다.
- `myFoodSelector/`는 별도 앱이며 이 규칙의 대상이 아니다.

## 디렉터리

```
src/back/
  server.py      # 진입점. 객체 조립만 한다
  config.py      # 경로, 환경변수, 상수
  routers/       # 요청 → 모델 → 서비스 → 응답
  services/      # 유스케이스, 트랜잭션 경계. ports.py에 저장소 인터페이스
  models/        # 도메인 데이터, 검증, 업무 규칙, 도메인 예외
  repositories/  # SQLite 구현, schema.sql, 초기 데이터
  web/           # HTTP 핸들러, 라우팅, 정적 파일
src/front/       # HTML, CSS, JavaScript
tests/
```

- 소스 코드는 `src/back`, `src/front`, 테스트는 `tests/`에만 둔다. 루트에 코드 파일을 만들지 않는다.
- 새 계층이나 최상위 폴더가 필요하면 먼저 확인을 받고, 이 문서와 `tests/test_architecture.py`를 함께 고친다.

## 의존 방향

| 계층 | import 가능 | import 금지 |
|---|---|---|
| `models` | 없음(표준 라이브러리) | 다른 계층, `config`, `sqlite3`, `http`, `json` |
| `services` | `models` | `repositories`, `routers`, `web`, `config`, `sqlite3`, `http`, `json` |
| `repositories` | `models` | `services`, `routers`, `web`, `http` |
| `routers` | `models`, `services`, `web` | `repositories`, `sqlite3`, `http` |
| `web` | `models`, `config` | `services`, `repositories`, `routers`, `sqlite3` |

- 구현 객체를 만들고 연결하는 곳은 `server.py` 하나다.
- 서비스는 저장소를 `services/ports.py`의 Protocol로만 사용한다.

## 백엔드 규칙

- Python 3.10 이상, 표준 라이브러리만 사용한다.
- SQL은 `repositories/`에만 쓰고, 값은 반드시 `?` 파라미터로 전달한다.
- 읽고 나서 쓰는 작업(정원 확인 후 신청 등)은 `database.transaction()` 하나 안에서 한다.
- 서비스와 모델은 HTTP 상태 코드를 쓰지 않고 `models/errors.py`의 예외를 던진다. 상태 코드 변환은 `web/handler.py`에서만 한다.
- 외부 입력은 모델의 `parse()`에서 검증한다.
- 설정값과 경로는 `config.py`에 둔다. 비밀 값은 코드에 쓰지 않는다.

## 프론트엔드 규칙

- 서버와는 `/api`로만 통신한다. 서버 렌더링을 하지 않는다.
- 데이터를 화면에 넣을 때는 `textContent`를 쓴다. 데이터가 섞인 `innerHTML`은 금지한다.
- 정적 파일을 추가하면 `web/static_files.py`의 허용 목록에 등록한다.

## API 규칙

- 경로는 `/api/...`, 응답은 JSON, 오류 형식은 `{"error": "한국어 메시지"}`다.
- 기존 응답의 필드 이름과 타입을 바꾸려면 프론트엔드와 테스트를 함께 고친다.

## 공통

- 사용자 대상 문구는 한국어로 쓴다.
- 개인정보(이름, 연락처 등)와 요청 본문을 로그에 남기지 않는다.
- `app.db`는 실험·테스트에 쓰지 않는다. `AIEDU_DB`로 임시 경로를 지정한다.
- 기능을 추가하거나 고치면 테스트를 함께 작성하고 `python -m unittest discover -s tests -v`가 통과해야 완료다.
