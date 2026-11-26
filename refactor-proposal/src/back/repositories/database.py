"""SQLite 연결, 트랜잭션, 초기화."""
import os
import sqlite3
from contextlib import contextmanager

from repositories.course_repository import SqliteCourseRepository
from repositories.enrollment_repository import SqliteEnrollmentRepository
from repositories.seed import seed_if_empty
from repositories.student_repository import SqliteStudentRepository

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


class SqliteRepositories:
    """하나의 연결을 공유하는 저장소 묶음."""

    def __init__(self, conn: sqlite3.Connection):
        self.courses = SqliteCourseRepository(conn)
        self.students = SqliteStudentRepository(conn)
        self.enrollments = SqliteEnrollmentRepository(conn)


class SqliteDatabase:
    def __init__(self, path: str):
        self.path = path

    @contextmanager
    def _connect(self):
        # isolation_level=None: 트랜잭션을 BEGIN/COMMIT으로 직접 제어한다.
        conn = sqlite3.connect(self.path, isolation_level=None)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self._connect() as conn:
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                conn.executescript(f.read())
            seed_if_empty(conn)

    @contextmanager
    def read(self):
        with self._connect() as conn:
            yield SqliteRepositories(conn)

    @contextmanager
    def transaction(self):
        with self._connect() as conn:
            # IMMEDIATE: 시작할 때 쓰기 잠금을 잡아 동시 신청을 직렬화한다.
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield SqliteRepositories(conn)
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
