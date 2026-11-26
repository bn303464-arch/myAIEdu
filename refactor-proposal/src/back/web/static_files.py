"""허용 목록에 있는 프론트엔드 파일만 제공한다."""
import os

from web.messages import Response

STATIC_FILES = {
    "index.html": "text/html; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
}


class StaticFiles:
    def __init__(self, directory: str):
        self._directory = directory

    def serve(self, path: str) -> Response | None:
        name = "index.html" if path == "/" else path.lstrip("/")
        if name not in STATIC_FILES:
            return None
        with open(os.path.join(self._directory, name), "rb") as f:
            return Response(200, f.read(), STATIC_FILES[name])
