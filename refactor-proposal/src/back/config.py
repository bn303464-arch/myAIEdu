"""경로와 실행 설정."""
import os

BACK_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(BACK_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)
FRONT_DIR = os.path.join(SRC_DIR, "front")

MAX_BODY = 10_000  # 요청 본문 최대 크기(바이트)


def db_path():
    """AIEDU_DB 환경변수가 없으면 프로젝트 루트의 app.db를 사용한다."""
    return os.environ.get("AIEDU_DB", os.path.join(ROOT_DIR, "app.db"))
