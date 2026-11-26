"""업무 규칙 위반을 나타내는 예외. HTTP 상태 코드는 알지 못한다."""


class DomainError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidInput(DomainError):
    """입력값이 규칙에 맞지 않는다."""


class NotFound(DomainError):
    """대상이 없다."""


class Conflict(DomainError):
    """현재 상태와 충돌한다."""


class CourseNotFound(NotFound):
    def __init__(self):
        super().__init__("과정을 찾을 수 없습니다.")


class CourseFull(Conflict):
    def __init__(self):
        super().__init__("죄송합니다. 정원이 마감되었습니다.")


class DuplicateEnrollment(Conflict):
    def __init__(self):
        super().__init__("이미 신청하신 과정입니다.")
