"""수강 신청과 입력 검증 규칙."""
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from models.errors import InvalidInput

# 정원을 차지하는 신청 상태
ACTIVE_STATUSES = ("applied", "confirmed")
AGE_GROUPS = ("40s", "50s")
MAX_TEXT = 50
MAX_PRICE = 10_000_000


@dataclass(frozen=True)
class EnrollmentRequest:
    """검증을 통과한 신청 내용. 외부 입력은 반드시 parse()로 만든다."""

    course_id: int
    name: str
    phone: str
    age_group: str | None
    occupation: str | None
    willing_price: int | None

    @classmethod
    def parse(cls, data: Mapping[str, Any]) -> "EnrollmentRequest":
        # 검사 순서가 사용자에게 보이는 오류 메시지를 결정하므로 바꾸지 않는다.
        name = str(data.get("name", "")).strip()
        phone = re.sub(r"[\s-]", "", str(data.get("phone", "")))
        occupation = str(data.get("occupation", "")).strip()
        age_group = str(data.get("age_group", "")).strip() or None
        course_id = data.get("course_id")
        price = data.get("willing_price")

        if not 1 <= len(name) <= MAX_TEXT:
            raise InvalidInput("이름을 1~50자로 입력해 주세요.")
        if not re.fullmatch(r"01\d{8,9}", phone):
            raise InvalidInput("휴대폰 번호를 확인해 주세요. (예: 010-1234-5678)")
        if len(occupation) > MAX_TEXT:
            raise InvalidInput("직업은 50자 이내로 입력해 주세요.")
        if age_group not in (None, *AGE_GROUPS):
            raise InvalidInput("연령대를 확인해 주세요.")
        if not isinstance(course_id, int) or isinstance(course_id, bool):
            raise InvalidInput("과정을 선택해 주세요.")
        if price in ("", None):
            price = None
        elif isinstance(price, bool) or not isinstance(price, int) or not 0 <= price <= MAX_PRICE:
            raise InvalidInput("희망 수강료를 숫자로 입력해 주세요.")
        if data.get("consent") is not True:
            raise InvalidInput("개인정보 수집·이용에 동의해 주세요.")

        return cls(
            course_id=course_id,
            name=name,
            phone=phone,
            age_group=age_group,
            occupation=occupation or None,
            willing_price=price,
        )
