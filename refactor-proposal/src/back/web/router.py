"""(메서드, 경로 패턴) → 처리 함수."""
import re
from collections.abc import Callable

from web.messages import Request, Response

Endpoint = Callable[[Request], Response]


class Router:
    def __init__(self):
        self._routes: list[tuple[str, re.Pattern, Endpoint]] = []

    def add(self, method: str, pattern: str, endpoint: Endpoint) -> None:
        self._routes.append((method, re.compile(pattern), endpoint))

    def match(self, method: str, path: str) -> tuple[Endpoint, tuple[str, ...]] | None:
        for route_method, pattern, endpoint in self._routes:
            if route_method != method:
                continue
            found = pattern.fullmatch(path)
            if found:
                return endpoint, found.groups()
        return None
