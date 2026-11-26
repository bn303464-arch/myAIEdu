"""과정과 주차별 수업."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Course:
    # 필드 이름과 순서가 /api/courses 응답 형식이다.
    id: int
    title: str
    cohort: str
    start_date: str | None
    capacity: int
    price: int
    seats_left: int


@dataclass(frozen=True)
class Lesson:
    # 필드 이름과 순서가 커리큘럼 응답 형식이다.
    week_no: int
    topic: str
    goal: str | None
    is_core: int  # API 계약상 true/false가 아닌 0/1


def is_full(capacity: int, taken: int) -> bool:
    return taken >= capacity
