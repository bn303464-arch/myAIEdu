"""myAIEdu 서버: API + 정적 프론트엔드. 실행: python server.py --port 8000"""
import argparse
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import db

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
STATIC_FILES = {
    "index.html": "text/html; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
}
MAX_BODY = 10_000


class Handler(BaseHTTPRequestHandler):
    server_version = "myAIEdu"

    def _send(self, status, body, ctype):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        try:
            if path == "/api/courses":
                return self._json(200, db.list_courses())
            m = re.fullmatch(r"/api/courses/(\d+)/curriculum", path)
            if m:
                return self._json(200, db.curriculum(int(m.group(1))))
        except db.AppError as e:
            return self._json(e.status, {"error": e.message})

        name = "index.html" if path == "/" else path.lstrip("/")
        if name in STATIC_FILES:
            with open(os.path.join(STATIC, name), "rb") as f:
                return self._send(200, f.read(), STATIC_FILES[name])
        self._json(404, {"error": "찾을 수 없습니다."})

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/enroll":
            return self._json(404, {"error": "찾을 수 없습니다."})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._json(400, {"error": "잘못된 요청입니다."})
        if length <= 0 or length > MAX_BODY:
            return self._json(400, {"error": "요청 크기가 올바르지 않습니다."})
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._json(400, {"error": "JSON 형식이 올바르지 않습니다."})
        if not isinstance(data, dict):
            return self._json(400, {"error": "JSON 형식이 올바르지 않습니다."})
        try:
            self._json(201, db.enroll(data))
        except db.AppError as e:
            self._json(e.status, {"error": e.message})

    def log_message(self, fmt, *args):
        # 요청 본문은 기록하지 않는다. (개인정보 보호)
        super().log_message(fmt, *args)


def make_server(host="127.0.0.1", port=8000):
    db.init_db()
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    srv = make_server(args.host, args.port)
    print(f"myAIEdu running at http://{args.host}:{args.port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
