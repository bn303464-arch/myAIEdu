"""점심 메뉴 추천 + 히스토리 저장 배달 앱 서버.

실행: python main.py  →  http://127.0.0.1:8000
외부 패키지 없이 파이썬 표준 라이브러리만 사용합니다.

데이터:
  data/menus.json    메뉴 목록 (직접 고쳐도 됩니다)
  data/history.json  주문(선택) 기록. 서버가 자동으로 씁니다.
"""

import json
import os
import random
import threading
import traceback
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MENUS_FILE = DATA_DIR / "menus.json"
HISTORY_FILE = DATA_DIR / "history.json"
INDEX_FILE = BASE_DIR / "index.html"

HOST = "127.0.0.1"
PORT = 8000
RECOMMEND_COUNT = 3   # 한 번에 추천하는 메뉴 수
RECENT_DAYS = 3       # 이 기간 안에 주문한 메뉴는 가능하면 제외
MAX_BODY = 16 * 1024  # 요청 본문 최대 크기(바이트)

_history_lock = threading.Lock()


# 연결이 이미 끊긴 뒤에는 응답을 쓰려다 예외가 한 번 더 나지 않게 한다.
_CLIENT_GONE = (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError)

# 프론트는 title 을 제목, detail 을 본문으로 그대로 보여 준다.
_STATUS_TITLE = {
    400: "요청을 확인해 주세요",
    404: "찾을 수 없어요",
    405: "요청을 확인해 주세요",
    413: "요청을 확인해 주세요",
    500: "서버에 문제가 있어요",
    501: "요청을 확인해 주세요",
}


class ApiError(Exception):
    def __init__(self, status, detail, title=None):
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.title = title or _STATUS_TITLE.get(status, "요청을 처리하지 못했어요")


def error_payload(status, detail, title=None):
    return {
        "title": title or _STATUS_TITLE.get(status, "요청을 처리하지 못했어요"),
        "detail": detail,
    }


# ---------- 파일 입출력 ----------

def read_json(path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # 깨진 파일은 지우지 않고 .bak 로 옮긴 뒤 빈 상태로 시작합니다.
        os.replace(path, path.parent / (path.name + ".bak"))
        return default
    except OSError:
        raise ApiError(500, "데이터를 읽지 못했어요. 잠시 후 다시 시도해 주세요.")


def write_json(path, data):
    tmp = path.parent / (path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # 쓰는 도중 꺼져도 원본이 깨지지 않도록 교체


def load_menus():
    data = read_json(MENUS_FILE, [])
    return data if isinstance(data, list) else []


def load_history():
    data = read_json(HISTORY_FILE, [])
    return data if isinstance(data, list) else []


# ---------- 비즈니스 로직 ----------

def recommend(budget=None, category=None):
    """예산·카테고리로 거른 뒤, 최근에 먹지 않은 메뉴를 우선해 무작위로 고른다."""
    menus = load_menus()
    cutoff = (date.today() - timedelta(days=RECENT_DAYS)).isoformat()
    recent_ids = {h.get("menu_id") for h in load_history() if h.get("date", "") >= cutoff}

    pool = [
        m for m in menus
        if (budget is None or m["price"] <= budget)
        and (not category or m["category"] == category)
    ]
    fresh = [m for m in pool if m["id"] not in recent_ids]
    picks = random.sample(fresh, min(RECOMMEND_COUNT, len(fresh)))

    if len(picks) < RECOMMEND_COUNT:
        # 후보가 부족하면 최근에 먹은 메뉴도 채운다.
        picked_ids = {m["id"] for m in picks}
        rest = [m for m in pool if m["id"] not in picked_ids]
        picks += random.sample(rest, min(RECOMMEND_COUNT - len(picks), len(rest)))

    return [dict(m, recent=m["id"] in recent_ids) for m in picks]


def add_history(menu_id):
    menu = next((m for m in load_menus() if m["id"] == menu_id), None)
    if menu is None:
        raise ApiError(404, "해당 메뉴를 찾을 수 없습니다.")
    with _history_lock:
        history = load_history()
        next_id = max((h.get("id", 0) for h in history), default=0) + 1
        record = {
            "id": next_id,
            "menu_id": menu["id"],
            "menu_name": menu["name"],
            "category": menu["category"],
            "price": menu["price"],
            "date": date.today().isoformat(),
        }
        history.append(record)
        write_json(HISTORY_FILE, history)
    return record


def delete_history(record_id):
    with _history_lock:
        history = load_history()
        remaining = [h for h in history if h.get("id") != record_id]
        if len(remaining) == len(history):
            raise ApiError(404, "해당 기록을 찾을 수 없습니다.")
        write_json(HISTORY_FILE, remaining)


def parse_budget(raw):
    if raw in (None, ""):
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(400, "예산은 숫자(원)로 입력해 주세요.")
    if value <= 0:
        raise ApiError(400, "예산은 0원보다 커야 합니다.")
    return value


# ---------- HTTP ----------

class Handler(BaseHTTPRequestHandler):
    server_version = "LunchPick/1.0"

    def log_message(self, fmt, *args):
        pass  # 콘솔을 조용하게 유지

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _content_length(self):
        raw = self.headers.get("Content-Length")
        if raw in (None, ""):
            return 0
        try:
            length = int(raw)
        except ValueError:
            raise ApiError(400, "요청 크기를 확인하지 못했어요.")
        if length < 0:
            raise ApiError(400, "요청 크기를 확인하지 못했어요.")
        return length

    def _read_body(self):
        length = self._content_length()
        if length > MAX_BODY:
            raise ApiError(413, "요청이 너무 큽니다. 내용을 줄여 다시 보내 주세요.")
        if length == 0:
            return {}
        try:
            data = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            raise ApiError(400, "JSON 형식이 올바르지 않습니다.")
        except _CLIENT_GONE:
            raise
        if not isinstance(data, dict):
            raise ApiError(400, "JSON 객체를 보내 주세요.")
        return data

    def _fail(self, status, detail, title=None):
        """클라이언트 연결이 살아 있을 때만 한국어 오류 JSON 을 보낸다."""
        try:
            self._send_json(status, error_payload(status, detail, title))
        except _CLIENT_GONE:
            self.close_connection = True

    def send_error(self, code, message=None, explain=None):
        # 기본 구현은 HTML 오류 페이지를 보낸다. 화면은 JSON 의 title·detail 만 읽는다.
        details = {
            400: "요청 형식을 이해하지 못했어요.",
            404: "페이지를 찾을 수 없습니다.",
            405: "지원하지 않는 요청입니다.",
            501: "지원하지 않는 요청입니다.",
        }
        self._fail(code, details.get(code, "요청을 처리하지 못했어요."))

    def _route(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if method == "GET" and path == "/":
            try:
                page = INDEX_FILE.read_bytes()
            except OSError:
                raise ApiError(500, "화면을 열지 못했어요. 잠시 후 다시 시도해 주세요.")
            return self._send(200, page, "text/html; charset=utf-8")

        if method == "GET" and path == "/api/menus":
            return self._send_json(200, load_menus())

        if method == "GET" and path == "/api/recommend":
            budget = parse_budget(query.get("budget", [None])[0])
            category = query.get("category", [None])[0] or None
            try:
                picks = recommend(budget, category)
            except (KeyError, TypeError):
                raise ApiError(500, "메뉴 정보를 읽지 못했어요. 잠시 후 다시 시도해 주세요.")
            return self._send_json(200, {
                "picks": picks,
                "recent_days": RECENT_DAYS,
            })

        if method == "GET" and path == "/api/history":
            history = sorted(load_history(), key=lambda h: h["id"], reverse=True)
            return self._send_json(200, history)

        if method == "POST" and path == "/api/history":
            body = self._read_body()
            menu_id = body.get("menu_id")
            if not isinstance(menu_id, int) or isinstance(menu_id, bool):
                raise ApiError(400, "menu_id 는 정수여야 합니다.")
            return self._send_json(201, add_history(menu_id))

        if method == "DELETE" and path.startswith("/api/history/"):
            try:
                record_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                raise ApiError(400, "기록 번호가 올바르지 않습니다.")
            delete_history(record_id)
            return self._send_json(200, {"deleted": record_id})

        raise ApiError(404, "페이지를 찾을 수 없습니다.")

    def _handle(self, method):
        try:
            self._route(method)
        except ApiError as e:
            self._fail(e.status, e.detail, e.title)
        except _CLIENT_GONE:
            # 응답을 쓰기 전에 브라우저가 연결을 끊은 경우. 다시 쓰지 않는다.
            self.close_connection = True
        except Exception:
            traceback.print_exc()
            self._fail(500, "잠시 후 다시 시도해 주세요.")

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_DELETE(self):
        self._handle("DELETE")


def main():
    DATA_DIR.mkdir(exist_ok=True)
    if not MENUS_FILE.exists():
        print(f"[경고] {MENUS_FILE} 이 없습니다. 메뉴 목록을 먼저 만들어 주세요.")
    if not HISTORY_FILE.exists():
        write_json(HISTORY_FILE, [])

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print(f"점심 메뉴 추천 서버 실행 중: http://{HOST}:{PORT}")
    print("종료하려면 Ctrl+C 를 누르세요.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
