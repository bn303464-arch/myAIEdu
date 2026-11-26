"""SQLite 접근과 수강 신청 업무 규칙 (표준 라이브러리만 사용)."""
import os
import re
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))

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


class AppError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def db_path():
    return os.environ.get("AIEDU_DB", os.path.join(BASE, "app.db"))


def connect():
    # isolation_level=None: 트랜잭션을 BEGIN/COMMIT으로 직접 제어한다.
    conn = sqlite3.connect(db_path(), isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = connect()
    try:
        with open(os.path.join(BASE, "schema.sql"), encoding="utf-8") as f:
            conn.executescript(f.read())
        if conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
            cur = conn.execute(
                "INSERT INTO courses (title, cohort, capacity, price) VALUES (?,?,?,?)",
                ("4050 AI 입문 8주 과정", "파일럿 1기", 10, 0),
            )
            conn.executemany(
                "INSERT INTO lessons (course_id, week_no, topic, goal, is_core) VALUES (?,?,?,?,?)",
                [(cur.lastrowid, *row) for row in SEED_LESSONS],
            )
    finally:
        conn.close()


def list_courses():
    conn = connect()
    try:
        rows = conn.execute(
            """SELECT c.id, c.title, c.cohort, c.start_date, c.capacity, c.price,
                      c.capacity - (SELECT COUNT(*) FROM enrollments e
                                    WHERE e.course_id = c.id
                                      AND e.status IN ('applied','confirmed')) AS seats_left
               FROM courses c ORDER BY c.id"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def curriculum(course_id):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT week_no, topic, goal, is_core FROM lessons WHERE course_id=? ORDER BY week_no",
            (course_id,),
        ).fetchall()
        if not rows:
            raise AppError(404, "과정을 찾을 수 없습니다.")
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _clean(data):
    name = str(data.get("name", "")).strip()
    phone = re.sub(r"[\s-]", "", str(data.get("phone", "")))
    occupation = str(data.get("occupation", "")).strip()
    age_group = str(data.get("age_group", "")).strip() or None
    course_id = data.get("course_id")
    price = data.get("willing_price")

    if not 1 <= len(name) <= 50:
        raise AppError(400, "이름을 1~50자로 입력해 주세요.")
    if not re.fullmatch(r"01\d{8,9}", phone):
        raise AppError(400, "휴대폰 번호를 확인해 주세요. (예: 010-1234-5678)")
    if len(occupation) > 50:
        raise AppError(400, "직업은 50자 이내로 입력해 주세요.")
    if age_group not in (None, "40s", "50s"):
        raise AppError(400, "연령대를 확인해 주세요.")
    if not isinstance(course_id, int) or isinstance(course_id, bool):
        raise AppError(400, "과정을 선택해 주세요.")
    if price in ("", None):
        price = None
    else:
        if isinstance(price, bool) or not isinstance(price, int) or not 0 <= price <= 10_000_000:
            raise AppError(400, "희망 수강료를 숫자로 입력해 주세요.")
    if data.get("consent") is not True:
        raise AppError(400, "개인정보 수집·이용에 동의해 주세요.")
    return name, phone, occupation or None, age_group, course_id, price


def enroll(data):
    name, phone, occupation, age_group, course_id, price = _clean(data)
    conn = connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            course = conn.execute(
                "SELECT capacity FROM courses WHERE id=?", (course_id,)
            ).fetchone()
            if course is None:
                raise AppError(404, "과정을 찾을 수 없습니다.")
            taken = conn.execute(
                "SELECT COUNT(*) FROM enrollments WHERE course_id=? AND status IN ('applied','confirmed')",
                (course_id,),
            ).fetchone()[0]
            if taken >= course["capacity"]:
                raise AppError(409, "죄송합니다. 정원이 마감되었습니다.")

            row = conn.execute("SELECT id FROM students WHERE phone=?", (phone,)).fetchone()
            if row is None:
                student_id = conn.execute(
                    "INSERT INTO students (name, phone, age_group, occupation) VALUES (?,?,?,?)",
                    (name, phone, age_group, occupation),
                ).lastrowid
            else:
                student_id = row["id"]
            try:
                conn.execute(
                    "INSERT INTO enrollments (student_id, course_id, willing_price) VALUES (?,?,?)",
                    (student_id, course_id, price),
                )
            except sqlite3.IntegrityError:
                raise AppError(409, "이미 신청하신 과정입니다.")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return {"ok": True, "message": "수강 신청이 접수되었습니다."}
    finally:
        conn.close()
