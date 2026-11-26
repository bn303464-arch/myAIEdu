"""8주차 예시: 서비스 아이디어의 손익분기를 계산하고 비즈니스 캔버스 요청문을 만든다.

AI를 직접 호출하지 않는다. 숫자 계산은 코드가 정확히 하고, 문장 작업은 AI에게 맡기도록
역할을 나눴다. AI는 나눗셈과 올림을 틀리는 경우가 있어 돈 계산을 맡기지 않는다.

실행:
    python business_canvas.py                     # 같은 폴더의 sample_idea.json 사용
    python business_canvas.py --input my_idea.json
"""
import argparse
import json
import math
import pathlib
import sys
from dataclasses import dataclass, field

HERE = pathlib.Path(__file__).resolve().parent

# 강의록 2부에서 고른 일곱 칸. 요청문과 출력 순서가 이 목록을 따른다.
CANVAS_FIELDS = ("고객", "문제", "해결책", "차별점", "알리는 길", "가격", "비용")


@dataclass
class Idea:
    service_name: str
    idea: str
    customer: str
    price: int
    unit_cost: int = 0
    monthly_fixed_cost: int = 0
    target_monthly_profit: int = 0
    # 한 달에 혼자 감당할 수 있는 최대 건수. 0이면 현실성 점검을 건너뛴다.
    max_units_per_month: int = 0
    brand_sentence: str = ""
    channels: list = field(default_factory=list)

    @classmethod
    def parse(cls, data):
        """JSON에서 읽은 dict를 검증해 Idea로 만든다. 문제가 있으면 한국어 ValueError."""
        if not isinstance(data, dict):
            raise ValueError("아이디어는 { } 로 감싼 JSON 객체여야 합니다.")
        missing = [k for k in ("service_name", "idea", "customer") if not str(data.get(k, "")).strip()]
        if missing:
            raise ValueError("다음 항목을 채워 주세요: " + ", ".join(missing))
        money = {k: _won(data, k) for k in
                 ("price", "unit_cost", "monthly_fixed_cost", "target_monthly_profit", "max_units_per_month")}
        if money["price"] <= 0:
            raise ValueError("price(가격)는 0보다 커야 합니다.")
        channels = data.get("channels") or []
        if isinstance(channels, str):
            channels = channels.split(",")
        return cls(
            service_name=data["service_name"].strip(),
            idea=data["idea"].strip(),
            customer=data["customer"].strip(),
            brand_sentence=str(data.get("brand_sentence", "")).strip(),
            channels=[str(c).strip() for c in channels if str(c).strip()],
            **money,
        )


def _won(data, key):
    # "300,000"처럼 쉼표를 넣어 적어도 받아 준다. 음수는 계산을 왜곡하므로 거부한다.
    raw = data.get(key, 0)
    if isinstance(raw, str):
        raw = raw.replace(",", "").replace("원", "").strip() or "0"
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{key}는 숫자로 적어 주세요.") from None
    if value < 0:
        raise ValueError(f"{key}는 0 이상이어야 합니다.")
    return value


@dataclass
class Numbers:
    margin: int                 # 한 건 남는 돈
    break_even_units: int | None  # None이면 아무리 팔아도 고정비를 못 메운다
    target_units: int | None
    feasible: bool | None       # None이면 최대 건수를 몰라 판단하지 않음


def calculate(idea):
    """강의록 3부 공식. 건수는 소수점이 나오면 올림한다(0.8건은 실제로 1건을 해야 한다)."""
    margin = idea.price - idea.unit_cost
    if margin <= 0:
        return Numbers(margin, None, None, False if idea.max_units_per_month else None)
    break_even = math.ceil(idea.monthly_fixed_cost / margin)
    target = math.ceil((idea.monthly_fixed_cost + idea.target_monthly_profit) / margin)
    feasible = target <= idea.max_units_per_month if idea.max_units_per_month else None
    return Numbers(margin, break_even, target, feasible)


def won(n):
    return f"{n:,}원"


def numbers_report(idea, nums):
    """수강생이 3단계 표에 옮겨 적을 숫자 점검 결과."""
    lines = [
        f"가격(한 건): {won(idea.price)}",
        f"한 건 비용: {won(idea.unit_cost)}",
        f"한 건 남는 돈: {won(nums.margin)}",
        f"월 고정비: {won(idea.monthly_fixed_cost)}",
    ]
    if nums.break_even_units is None:
        lines.append("손익분기: 한 건 남는 돈이 0원 이하라 팔수록 손해입니다. 가격을 올리거나 비용을 줄여 주세요.")
        return "\n".join(lines)
    lines.append(f"손익분기 건수: 한 달 {nums.break_even_units}건")
    if idea.target_monthly_profit:
        lines.append(f"목표 순수익 {won(idea.target_monthly_profit)}을 위한 건수: 한 달 {nums.target_units}건")
    if nums.feasible is True:
        lines.append(f"점검: 한 달 최대 {idea.max_units_per_month}건 안에서 해낼 수 있는 목표입니다.")
    elif nums.feasible is False:
        lines.append(f"점검: 한 달 최대 {idea.max_units_per_month}건을 넘습니다. 가격, 비용, 목표 중 하나를 조정해 보세요.")
    return "\n".join(lines)


def build_prompt(idea, nums):
    """AI 서비스에 붙여 넣을 캔버스 요청문. 계산 결과는 코드가 확정한 값으로 넘겨 AI가 바꾸지 않게 한다."""
    lines = ["너는 4050 직장인의 첫 1인 사업을 돕는 창업 코치야.", ""]
    if idea.brand_sentence:
        lines += ["[나에 대해]", idea.brand_sentence, ""]
    lines += [
        "[아이디어]",
        f"- 서비스 이름: {idea.service_name}",
        f"- 한 줄 설명: {idea.idea}",
        f"- 고객: {idea.customer}",
    ]
    if idea.channels:
        lines.append("- 고객을 만날 곳: " + ", ".join(idea.channels))
    lines += [
        f"- 가격: {won(idea.price)} / 한 건 비용: {won(idea.unit_cost)} / 월 고정비: {won(idea.monthly_fixed_cost)}",
    ]
    if nums.break_even_units is not None:
        lines.append(f"- 손익분기: 한 달 {nums.break_even_units}건 (이 숫자는 이미 계산했으니 다시 계산하지 마)")
    lines += [
        "",
        "[해 줄 일]",
        "1. 다음 일곱 칸으로 한 장 비즈니스 캔버스를 표로 채워 줘: " + ", ".join(CANVAS_FIELDS),
        "2. 이 아이디어의 가장 큰 위험 3가지와, 각각을 돈 들이지 않고 일주일 안에 확인하는 방법",
        "3. 소개 페이지에 쓸 한 줄 제목 3개 (고객의 문제로 시작)",
        "",
        "[조건]",
        "- 과장 표현 없이 담백하게, 존댓말로 써 줘.",
        # 시장 통계 환각을 막는 지시. 테스트에서 이 문구가 있는지 확인한다.
        "- 통계나 시장 규모를 쓸 때는 출처를 함께 적고, 확실하지 않으면 [확인 필요]로 표시해 줘.",
    ]
    return "\n".join(lines)


def load_idea(path):
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"파일을 찾을 수 없습니다: {path}") from None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 형식이 올바르지 않습니다({e.lineno}번째 줄 근처). 쉼표와 따옴표를 확인해 주세요.") from None
    return Idea.parse(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description="서비스 아이디어의 손익분기와 캔버스 요청문을 만듭니다.")
    parser.add_argument("--input", default=str(HERE / "sample_idea.json"), help="아이디어 JSON 파일 경로")
    args = parser.parse_args(argv)
    try:
        idea = load_idea(args.input)
    except ValueError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1
    nums = calculate(idea)
    print("=== 숫자 점검 ===")
    print(numbers_report(idea, nums))
    print()
    print("=== AI 요청문 (아래 전체를 복사해 AI에게 보내세요) ===")
    print(build_prompt(idea, nums))
    return 0


if __name__ == "__main__":
    sys.exit(main())
