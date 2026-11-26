import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "back"))


class ApiTest(unittest.TestCase):
    def setUp(self):
        # 실제 app.db가 아닌 임시 DB만 사용한다.
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AIEDU_DB"] = os.path.join(self.tmp.name, "test.db")
        import server
        self.srv = server.make_server("127.0.0.1", 0)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        os.environ.pop("AIEDU_DB", None)
        self.tmp.cleanup()

    def call(self, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def form(self, **kw):
        base = {"course_id": 1, "name": "홍길동", "phone": "010-1234-5678",
                "age_group": "40s", "occupation": "직장인", "willing_price": 50000,
                "consent": True}
        base.update(kw)
        return base

    def test_curriculum_has_8_weeks(self):
        status, weeks = self.call("/api/courses/1/curriculum")
        self.assertEqual(status, 200)
        self.assertEqual([w["week_no"] for w in weeks], list(range(1, 9)))

    def test_index_served(self):
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertEqual(r.status, 200)

    def test_static_assets_served(self):
        for path, ctype in (("/style.css", "text/css"), ("/app.js", "text/javascript")):
            with urllib.request.urlopen(self.base + path) as r:
                self.assertEqual(r.status, 200)
                self.assertTrue(r.headers["Content-Type"].startswith(ctype))

    def test_backend_files_not_served(self):
        for path in ("/server.py", "/config.py", "/repositories/schema.sql", "/app.db"):
            self.assertEqual(self.call(path)[0], 404, path)

    def test_enroll_then_duplicate(self):
        self.assertEqual(self.call("/api/enroll", self.form())[0], 201)
        self.assertEqual(self.call("/api/enroll", self.form())[0], 409)

    def test_capacity(self):
        for i in range(10):
            s, _ = self.call("/api/enroll", self.form(phone=f"0101234{i:04d}"))
            self.assertEqual(s, 201)
        s, body = self.call("/api/enroll", self.form(phone="01099998888"))
        self.assertEqual(s, 409)
        self.assertIn("마감", body["error"])
        self.assertEqual(self.call("/api/courses")[1][0]["seats_left"], 0)

    def test_concurrent_requests_do_not_exceed_capacity(self):
        results = []

        def apply(i):
            results.append(self.call("/api/enroll", self.form(phone=f"0105555{i:04d}"))[0])

        threads = [threading.Thread(target=apply, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(results), [201] * 10 + [409] * 10)

    def test_validation(self):
        self.assertEqual(self.call("/api/enroll", self.form(name=""))[0], 400)
        self.assertEqual(self.call("/api/enroll", self.form(phone="123"))[0], 400)
        self.assertEqual(self.call("/api/enroll", self.form(consent=False))[0], 400)
        self.assertEqual(self.call("/api/enroll", self.form(course_id=999))[0], 404)


if __name__ == "__main__":
    unittest.main()
