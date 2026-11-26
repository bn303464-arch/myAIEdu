"""빈 DB에 넣는 초기 데이터."""
import sqlite3

# (과정명, 기수, 정원, 수강료)
SEED_COURSE = ("4050 AI 입문 8주 과정", "파일럿 1기", 10, 0)

# [가안] 커리큘럼 확정 시 이 목록만 고치면 된다. (주차, 주제, 목표, 핵심실습 여부)
SEED_LESSONS = [
    (1, "AI와 친해지기", "개념 이해, 첫 대화 체험", 0),
    (2, "질문 잘하는 법", "요청문 기초", 0),
    (3, "글쓰기 도우미", "이메일, 공지, 메시지 작성", 0),
    (4, "정보 찾기와 정리", "검색, 요약, 비교", 0),
    (5, "핵심 실습 ①: 나만의 업무·생활 도우미", "오늘 할 일을 정하고 AI에게 부탁하기", 1),
    (6, "핵심 실습 ②: 다듬어 쓰기", "사실 확인, 내 말투로 손보고 실제로 사용하기", 1),
    (7, "내 직업에 맞춘 활용", "직무와 업종별 사례", 0),
    (8, "나만의 결과물 발표", "수료와 후속 활용 계획", 0),
]


def seed_if_empty(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]:
        return
    course_id = conn.execute(
        "INSERT INTO courses (title, cohort, capacity, price) VALUES (?,?,?,?)",
        SEED_COURSE,
    ).lastrowid
    conn.executemany(
        "INSERT INTO lessons (course_id, week_no, topic, goal, is_core) VALUES (?,?,?,?,?)",
        [(course_id, *row) for row in SEED_LESSONS],
    )
