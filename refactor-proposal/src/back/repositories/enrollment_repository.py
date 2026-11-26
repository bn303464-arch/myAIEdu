import sqlite3

from models.enrollment import ACTIVE_STATUSES
from models.errors import DuplicateEnrollment

_ACTIVE_MARKS = ",".join("?" * len(ACTIVE_STATUSES))


class SqliteEnrollmentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def count_active(self, course_id: int) -> int:
        return self._conn.execute(
            f"SELECT COUNT(*) FROM enrollments WHERE course_id=? AND status IN ({_ACTIVE_MARKS})",
            (course_id, *ACTIVE_STATUSES),
        ).fetchone()[0]

    def add(self, student_id: int, course_id: int, willing_price: int | None) -> None:
        try:
            self._conn.execute(
                "INSERT INTO enrollments (student_id, course_id, willing_price) VALUES (?,?,?)",
                (student_id, course_id, willing_price),
            )
        except sqlite3.IntegrityError:
            raise DuplicateEnrollment() from None
