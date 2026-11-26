"""요청과 응답 객체."""
import json
from dataclasses import dataclass

import config
from models.errors import InvalidInput


@dataclass(frozen=True)
class Response:
    status: int
    body: bytes
    content_type: str


def json_response(status: int, payload) -> Response:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return Response(status, body, "application/json; charset=utf-8")


def error_response(status: int, message: str) -> Response:
    return json_response(status, {"error": message})


class Request:
    def __init__(self, headers, stream, params: tuple[str, ...] = ()):
        self._headers = headers
        self._stream = stream
        self.params = params  # 경로 패턴에서 뽑은 값

    def json_object(self) -> dict:
        try:
            length = int(self._headers.get("Content-Length") or 0)
        except ValueError:
            raise InvalidInput("잘못된 요청입니다.") from None
        if length <= 0 or length > config.MAX_BODY:
            raise InvalidInput("요청 크기가 올바르지 않습니다.")
        try:
            data = json.loads(self._stream.read(length).decode("utf-8"))
        except ValueError:  # UnicodeDecodeError, JSONDecodeError 포함
            raise InvalidInput("JSON 형식이 올바르지 않습니다.") from None
        if not isinstance(data, dict):
            raise InvalidInput("JSON 형식이 올바르지 않습니다.")
        return data
