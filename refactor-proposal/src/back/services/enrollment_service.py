"""수강 신청."""
from models.course import is_full
from models.enrollment import EnrollmentRequest
from models.errors import CourseFull, CourseNotFound
from services.ports import Database


class EnrollmentService:
    def __init__(self, database: Database):
        self._database = database

    def enroll(self, request: EnrollmentRequest) -> None:
        # 정원 확인부터 저장까지 하나의 트랜잭션이어야 초과 접수가 없다.
        with self._database.transaction() as repos:
            capacity = repos.courses.capacity_of(request.course_id)
            if capacity is None:
                raise CourseNotFound()
            if is_full(capacity, repos.enrollments.count_active(request.course_id)):
                raise CourseFull()

            student_id = repos.students.find_id_by_phone(request.phone)
            if student_id is None:
                student_id = repos.students.add(request)
            repos.enrollments.add(student_id, request.course_id, request.willing_price)
