"""서비스가 저장소에 요구하는 인터페이스(포트). 구현은 repositories에 있다."""
from contextlib import AbstractContextManager
from typing import Protocol

from models.course import Course, Lesson
from models.enrollment import EnrollmentRequest


class CourseRepository(Protocol):
    def list_all(self) -> list[Course]: ...

    def lessons_of(self, course_id: int) -> list[Lesson]: ...

    def capacity_of(self, course_id: int) -> int | None:
        """과정이 없으면 None."""


class StudentRepository(Protocol):
    def find_id_by_phone(self, phone: str) -> int | None: ...

    def add(self, request: EnrollmentRequest) -> int:
        """새 수강생을 저장하고 id를 돌려준다."""


class EnrollmentRepository(Protocol):
    def count_active(self, course_id: int) -> int: ...

    def add(self, student_id: int, course_id: int, willing_price: int | None) -> None:
        """이미 신청한 과정이면 DuplicateEnrollment를 발생시킨다."""


class Repositories(Protocol):
    courses: CourseRepository
    students: StudentRepository
    enrollments: EnrollmentRepository


class Database(Protocol):
    def read(self) -> AbstractContextManager[Repositories]:
        """조회용."""

    def transaction(self) -> AbstractContextManager[Repositories]:
        """쓰기용. 블록이 정상 종료하면 커밋, 예외가 나면 롤백한다.
        블록 안에서는 다른 쓰기가 끼어들 수 없어야 한다(정원 검사)."""
