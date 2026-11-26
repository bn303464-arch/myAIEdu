"""계층별 단위 테스트."""
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "back"))

import config  # noqa: E402
from models.enrollment import EnrollmentRequest  # noqa: E402
from models.errors import CourseFull, CourseNotFound, InvalidInput  # noqa: E402
from repositories.database import SqliteDatabase  # noqa: E402
from services.enrollment_service import EnrollmentService  # noqa: E402

VALID = {"course_id": 1, "name": " 홍길동 ", "phone": "010-1234-5678", "consent": True,
         "age_group": "", "occupation": "", "willing_price": ""}


class ModelTest(unittest.TestCase):
    def test_parse_normalizes_input(self):
        r = EnrollmentRequest.parse(VALID)
        self.assertEqual((r.name, r.phone), ("홍길동", "01012345678"))
        self.assertEqual((r.age_group, r.occupation, r.willing_price), (None, None, None))

    def test_parse_rejects_bool_as_number(self):
        for field in ("course_id", "willing_price"):
            with self.assertRaises(InvalidInput, msg=field):
                EnrollmentRequest.parse({**VALID, field: True})


class FakeDatabase:
    """SQLite 없이 서비스 규칙만 확인하기 위한 대역."""

    def __init__(self, capacity, taken):
        self.saved = []
        self.repos = SimpleNamespace(
            courses=SimpleNamespace(capacity_of=lambda course_id: capacity),
            students=SimpleNamespace(find_id_by_phone=lambda phone: None, add=lambda request: 7),
            enrollments=SimpleNamespace(count_active=lambda course_id: taken,
                                        add=lambda *row: self.saved.append(row)),
        )

    @contextmanager
    def transaction(self):
        yield self.repos


class ServiceTest(unittest.TestCase):
    def enroll(self, database):
        EnrollmentService(database).enroll(EnrollmentRequest.parse(VALID))

    def test_saves_when_seat_available(self):
        db = FakeDatabase(capacity=10, taken=9)
        self.enroll(db)
        self.assertEqual(db.saved, [(7, 1, None)])

    def test_full_course(self):
        db = FakeDatabase(capacity=10, taken=10)
        with self.assertRaises(CourseFull):
            self.enroll(db)
        self.assertEqual(db.saved, [])

    def test_unknown_course(self):
        with self.assertRaises(CourseNotFound):
            self.enroll(FakeDatabase(capacity=None, taken=0))


class RepositoryTest(unittest.TestCase):
    def test_transaction_rolls_back_on_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = SqliteDatabase(os.path.join(tmp, "test.db"))
            database.initialize()
            with self.assertRaises(RuntimeError):
                with database.transaction() as repos:
                    repos.students.add(EnrollmentRequest.parse(VALID))
                    raise RuntimeError("중간 실패")
            with database.read() as repos:
                self.assertIsNone(repos.students.find_id_by_phone("01012345678"))

    def test_initialize_twice_seeds_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = SqliteDatabase(os.path.join(tmp, "test.db"))
            database.initialize()
            database.initialize()
            with database.read() as repos:
                self.assertEqual(len(repos.courses.list_all()), 1)


class ConfigTest(unittest.TestCase):
    def test_default_db_is_in_project_root(self):
        # 경로만 확인하며 DB 파일을 열지 않는다.
        with mock.patch.dict(os.environ):
            os.environ.pop("AIEDU_DB", None)
            self.assertEqual(config.db_path(), os.path.join(ROOT, "app.db"))


if __name__ == "__main__":
    unittest.main()
