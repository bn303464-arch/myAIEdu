import sqlite3

from models.enrollment import EnrollmentRequest


class SqliteStudentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def find_id_by_phone(self, phone: str) -> int | None:
        row = self._conn.execute("SELECT id FROM students WHERE phone=?", (phone,)).fetchone()
        return None if row is None else row["id"]

    def add(self, request: EnrollmentRequest) -> int:
        return self._conn.execute(
            "INSERT INTO students (name, phone, age_group, occupation) VALUES (?,?,?,?)",
            (request.name, request.phone, request.age_group, request.occupation),
        ).lastrowid
