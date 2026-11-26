from dataclasses import asdict

from services.course_service import CourseService
from web.messages import Request, Response, json_response
from web.router import Router


def register(router: Router, service: CourseService) -> None:
    def list_courses(request: Request) -> Response:
        return json_response(200, [asdict(c) for c in service.list_courses()])

    def curriculum(request: Request) -> Response:
        lessons = service.curriculum(int(request.params[0]))
        return json_response(200, [asdict(lesson) for lesson in lessons])

    router.add("GET", r"/api/courses", list_courses)
    router.add("GET", r"/api/courses/(\d+)/curriculum", curriculum)
