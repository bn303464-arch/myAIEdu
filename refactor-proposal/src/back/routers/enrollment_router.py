from models.enrollment import EnrollmentRequest
from services.enrollment_service import EnrollmentService
from web.messages import Request, Response, json_response
from web.router import Router


def register(router: Router, service: EnrollmentService) -> None:
    def enroll(request: Request) -> Response:
        service.enroll(EnrollmentRequest.parse(request.json_object()))
        return json_response(201, {"ok": True, "message": "수강 신청이 접수되었습니다."})

    router.add("POST", r"/api/enroll", enroll)
