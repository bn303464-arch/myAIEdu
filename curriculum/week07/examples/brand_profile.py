"""7주차 예시: 경력 재료로 브랜드 한 문장 초안과 AI 요청문을 만든다.

AI를 직접 호출하지 않는다. 수강생이 쓰는 AI 서비스에 붙여 넣을 요청문을 출력한다.
API 키 없이 강의실 어디서나 실행되게 하려는 의도다.

실행:
    python brand_profile.py                       # 같은 폴더의 sample_profile.json 사용
    python brand_profile.py --input my_profile.json
"""
import argparse
import json
import pathlib
import sys
from dataclasses import dataclass, field

HERE = pathlib.Path(__file__).resolve().parent

# 비어 있으면 요청문의 품질이 크게 떨어지는 항목. 강의록 2부의 공식 네 칸에 해당한다.
REQUIRED_FIELDS = ("job", "audience", "problem", "method", "role")

# 수강생이 금지어를 따로 적지 않아도 기본으로 막는 과장 표현.
# 확인할 수 없는 최상급 표현은 신뢰를 깎는다는 강의 내용을 반영했다.
DEFAULT_BANNED = ("최고", "최초", "혁신적인", "독보적인", "업계 1위")


@dataclass
class Profile:
    job: str
    audience: str
    problem: str
    method: str
    role: str
    years: int = 0
    strengths: list = field(default_factory=list)
    achievements: list = field(default_factory=list)
    tone: str = "존댓말, 담백하게"
    banned_words: list = field(default_factory=list)

    @classmethod
    def parse(cls, data):
        """JSON에서 읽은 dict를 검증해 Profile로 만든다. 문제가 있으면 한국어 ValueError."""
        if not isinstance(data, dict):
            raise ValueError("프로필은 { } 로 감싼 JSON 객체여야 합니다.")
        missing = [k for k in REQUIRED_FIELDS if not str(data.get(k, "")).strip()]
        if missing:
            raise ValueError("다음 항목을 채워 주세요: " + ", ".join(missing))
        years = data.get("years", 0)
        # JSON에 "25"처럼 문자열로 적는 실수가 잦아 숫자로 바꿔 준다.
        try:
            years = int(years)
        except (TypeError, ValueError):
            raise ValueError("years(경력 기간)는 숫자로 적어 주세요.") from None
        if years < 0:
            raise ValueError("years(경력 기간)는 0 이상이어야 합니다.")
        return cls(
            job=data["job"].strip(),
            audience=data["audience"].strip(),
            problem=data["problem"].strip(),
            method=data["method"].strip(),
            role=data["role"].strip(),
            years=years,
            strengths=_as_list(data.get("strengths")),
            achievements=_as_list(data.get("achievements")),
            tone=str(data.get("tone") or "존댓말, 담백하게").strip(),
            banned_words=_as_list(data.get("banned_words")),
        )


def _as_list(value):
    # 쉼표로 이어 쓴 문자열도 목록으로 받아 준다. 초보자가 JSON 배열 문법을 틀리는 경우가 많다.
    if value is None:
        return []
    if isinstance(value, str):
        value = value.split(",")
    return [str(v).strip() for v in value if str(v).strip()]


def has_final_consonant(word):
    """마지막 글자에 받침이 있으면 True. 한글이 아니면 받침 없음으로 본다."""
    if not word:
        return False
    code = ord(word[-1]) - 0xAC00
    return 0 <= code < 11172 and code % 28 != 0


def josa(word, with_final, without_final):
    # 사용자 입력 뒤에 붙는 조사를 받침에 맞춰 고른다. "반장를"처럼 어색한 초안을 막기 위함이다.
    return word + (with_final if has_final_consonant(word) else without_final)


def instrumental(word):
    # '(으)로'는 받침이 없거나 'ㄹ' 받침이면 '로', 그 밖의 받침이면 '으로'를 쓴다.
    code = ord(word[-1]) - 0xAC00 if word else -1
    if 0 <= code < 11172 and code % 28 not in (0, 8):
        return word + "으로"
    return word + "로"


def brand_sentence(p):
    """강의록 2부 공식으로 브랜드 한 문장 초안을 만든다. AI 결과와 비교할 기준점이다."""
    # 문제를 "~어렵다"처럼 문장으로 적으면 "~어렵다는 문제", "업무 분배"처럼 명사로 적으면 "업무 분배 문제"로 잇는다.
    problem = f"{p.problem}는 문제" if p.problem.endswith("다") else f"{p.problem} 문제"
    return (f"나는 {josa(p.audience, '을', '를')} 위해 {problem}를 "
            f"{instrumental(p.method)} 해결하는 {josa(p.role, '이다', '다')}.")


def banned_words(p):
    # 기본 금지어 뒤에 수강생 금지어를 붙이되 중복은 뺀다. 순서는 출력 안정성을 위해 유지한다.
    return list(dict.fromkeys([*DEFAULT_BANNED, *p.banned_words]))


def build_prompt(p):
    """AI 서비스에 붙여 넣을 요청문. 강의록 3부의 5요소(역할·재료·과제·조건·확인 요청) 순서를 따른다."""
    lines = [
        "너는 4050 경력자의 전직과 1인 사업을 돕는 커리어 코치야.",
        "",
        "[내 재료]",
        f"- 하는 일: {p.job}",
    ]
    if p.years:
        lines.append(f"- 경력: {p.years}년")
    if p.strengths:
        lines.append("- 강점: " + ", ".join(p.strengths))
    if p.achievements:
        lines.append("- 성과: " + "; ".join(p.achievements))
    lines += [
        f"- 도움을 줄 대상: {p.audience}",
        f"- 그 대상의 문제: {p.problem}",
        f"- 나만의 방식: {p.method}",
        f"- 불리고 싶은 이름: {p.role}",
        f"- 참고할 브랜드 한 문장 초안: {brand_sentence(p)}",
        "",
        "[만들어 줄 것]",
        "1. 브랜드 한 문장 (나는 ~를 위해 ~를 ~로 해결하는 ~이다)",
        "2. 키워드 3개",
        "3. 30초 자기소개 (말로 하기 좋게, 150자 안팎)",
        "4. 온라인 프로필 소개 (300자 이내)",
        "5. 명함 한 줄 (25자 이내)",
        "",
        "[조건]",
        f"- 말투: {p.tone}",
        "- 다음 표현은 쓰지 마: " + ", ".join(banned_words(p)),
        "- 세 가지 소개문은 같은 키워드를 써서 같은 사람으로 읽히게 해 줘.",
        # 환각 방지 지시는 빠뜨리면 안 된다. 테스트에서도 이 문구가 있는지 확인한다.
        "- 내가 준 정보에 없는 사실은 만들지 말고, 추측한 부분은 [확인 필요]로 표시해 줘.",
    ]
    return "\n".join(lines)


def load_profile(path):
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"파일을 찾을 수 없습니다: {path}") from None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 형식이 올바르지 않습니다({e.lineno}번째 줄 근처). 쉼표와 따옴표를 확인해 주세요.") from None
    return Profile.parse(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description="경력 재료로 퍼스널 브랜딩 요청문을 만듭니다.")
    parser.add_argument("--input", default=str(HERE / "sample_profile.json"), help="프로필 JSON 파일 경로")
    args = parser.parse_args(argv)
    try:
        profile = load_profile(args.input)
    except ValueError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1
    print("=== 브랜드 한 문장 초안 ===")
    print(brand_sentence(profile))
    print()
    print("=== AI 요청문 (아래 전체를 복사해 AI에게 보내세요) ===")
    print(build_prompt(profile))
    return 0


if __name__ == "__main__":
    sys.exit(main())
