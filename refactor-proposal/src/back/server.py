"""myAIEdu 서버 진입점: 객체를 조립하고 실행한다.

실행: python src/back/server.py --port 8000
"""
import argparse
from http.server import ThreadingHTTPServer

import config
from repositories.database import SqliteDatabase
from routers import course_router, enrollment_router
from services.course_service import CourseService
from services.enrollment_service import EnrollmentService
from web.handler import build_handler
from web.router import Router
from web.static_files import StaticFiles


def make_server(host="127.0.0.1", port=8000):
    database = SqliteDatabase(config.db_path())
    database.initialize()

    router = Router()
    course_router.register(router, CourseService(database))
    enrollment_router.register(router, EnrollmentService(database))

    handler = build_handler(router, StaticFiles(config.FRONT_DIR))
    return ThreadingHTTPServer((host, port), handler)


def main():
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
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
