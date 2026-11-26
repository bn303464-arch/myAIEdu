# 강의 자료 (curriculum)

4050 직장인을 위한 생성형 AI 8주 과정의 주차별 강의록, 실습 가이드, 예시 코드를 둔다.
수강 신청 웹 서비스(`server.py`, `db.py`, `static/`, 마이그레이션 후 `src/`)와는 **독립된 교육 자료**다.

| 주차 | 주제 | 강의록 | 실습 가이드 | 예시 코드 |
|---|---|---|---|---|
| 7주차 | 퍼스널 브랜딩 완성형 | [lecture.md](week07/lecture.md) | [practice-guide.md](week07/practice-guide.md) | [brand_profile.py](week07/examples/brand_profile.py), [profile_card.html](week07/examples/profile_card.html) |
| 8주차 | 나의 경험, AI를 만나 비즈니스가 되다 | [lecture.md](week08/lecture.md) | [practice-guide.md](week08/practice-guide.md) | [business_canvas.py](week08/examples/business_canvas.py), [landing_page.html](week08/examples/landing_page.html) |

> 앱에 표시되는 커리큘럼 가안(`db.py`의 `SEED_LESSONS`)의 7·8주차 제목은 아직 바뀌지 않았다.
> 이 자료를 확정하면 `SEED_LESSONS`도 맞춰 고치고 `app.db`를 재생성한다.

## 예시 코드 규칙

- Python 3.10 이상, 표준 라이브러리만 쓴다. API 키나 인터넷 연결 없이 실행된다.
- AI를 직접 호출하지 않는다. 수강생이 ChatGPT, Claude, Gemini 등에 **복사해 붙여 넣을 요청문(프롬프트)**을 만들어 준다.
- 앱 코드(`db.py`, `server.py`, `src/`)를 import하지 않는다. `tests/test_curriculum.py`가 이를 검사한다.
- HTML 예시는 파일 하나로 끝나며 브라우저에서 바로 연다. 입력값은 `textContent`로만 화면에 넣는다.

## 실행

```bash
python curriculum/week07/examples/brand_profile.py            # 예시 데이터로 요청문 출력
python curriculum/week07/examples/brand_profile.py --input my_profile.json
python curriculum/week08/examples/business_canvas.py
python curriculum/week08/examples/business_canvas.py --input my_idea.json
```

HTML 파일은 탐색기에서 더블클릭해 브라우저로 연다.
