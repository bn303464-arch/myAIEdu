import sqlite3

from models.course import Course, Lesson
from models.enrollment import ACTIVE_STATUSES

_ACTIVE_MARKS = ",".join("?" * len(ACTIVE_STATUSES))


class SqliteCourseRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def list_all(self) -> list[Course]:
        rows = self._conn.execute(
            f"""SELECT c.id, c.title, c.cohort, c.start_date, c.capacity, c.price,
                       c.capacity - (SELECT COUNT(*) FROM enrollments e
                                     WHERE e.course_id = c.id
                                       AND e.status IN ({_ACTIVE_MARKS})) AS seats_left
                FROM courses c ORDER BY c.id""",
            ACTIVE_STATUSES,
        ).fetchall()
        return [Course(**dict(r)) for r in rows]

    def lessons_of(self, course_id: int) -> list[Lesson]:
        rows = self._conn.execute(
            "SELECT week_no, topic, goal, is_core FROM lessons WHERE course_id=? ORDER BY week_no",
            (course_id,),
        ).fetchall()
        return [Lesson(**dict(r)) for r in rows]

    def capacity_of(self, course_id: int) -> int | None:
        row = self._conn.execute(
            "SELECT capacity FROM courses WHERE id=?", (course_id,)
        ).fetchone()
        return None if row is None else row["capacity"]
