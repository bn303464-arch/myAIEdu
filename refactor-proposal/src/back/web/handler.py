"""HTTP 요청을 라우터에 전달하고, 도메인 예외를 상태 코드로 바꾼다."""
from http.server import BaseHTTPRequestHandler

from models.errors import Conflict, DomainError, InvalidInput, NotFound
from web.messages import Request, Response, error_response
from web.router import Router
from web.static_files import StaticFiles

ERROR_STATUS = ((InvalidInput, 400), (NotFound, 404), (Conflict, 409))


def status_of(error: DomainError) -> int:
    for error_type, status in ERROR_STATUS:
        if isinstance(error, error_type):
            return status
    raise LookupError(f"상태 코드가 정해지지 않은 예외: {type(error).__name__}")


class RequestHandler(BaseHTTPRequestHandler):
    # 기본 접근 로그는 요청 줄만 남긴다. 개인정보가 담긴 요청 본문은 기록하지 않는다.
    server_version = "myAIEdu"
    router: Router
    static_files: StaticFiles

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        self._send(self._respond(method, self.path.split("?", 1)[0]))

    def _respond(self, method: str, path: str) -> Response:
        matched = self.router.match(method, path)
        if matched:
            endpoint, params = matched
            try:
                return endpoint(Request(self.headers, self.rfile, params))
            except DomainError as e:
                return error_response(status_of(e), e.message)
        if method == "GET":
            page = self.static_files.serve(path)
            if page:
                return page
        return error_response(404, "찾을 수 없습니다.")

    def _send(self, response: Response) -> None:
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response.body)


def build_handler(router: Router, static_files: StaticFiles) -> type[RequestHandler]:
    """의존 객체를 주입한 핸들러 클래스를 만든다."""
    return type(
        "BoundRequestHandler",
        (RequestHandler,),
        {"router": router, "static_files": static_files},
    )
