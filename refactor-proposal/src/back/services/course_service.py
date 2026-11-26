"""과정·커리큘럼 조회."""
from models.course import Course, Lesson
from models.errors import CourseNotFound
from services.ports import Database


class CourseService:
    def __init__(self, database: Database):
        self._database = database

    def list_courses(self) -> list[Course]:
        with self._database.read() as repos:
            return repos.courses.list_all()

    def curriculum(self, course_id: int) -> list[Lesson]:
        with self._database.read() as repos:
            lessons = repos.courses.lessons_of(course_id)
        if not lessons:
            raise CourseNotFound()
        return lessons
