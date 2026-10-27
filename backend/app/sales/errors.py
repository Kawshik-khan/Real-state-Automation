"""Business-rule errors raised by sales services, mapped to HTTP responses and tool refusals."""


class SalesError(Exception):
    """A refused action with a stable code (shown to tools and API clients) and a human message."""

    status_code = 400

    def __init__(self, code: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


class NotFound(SalesError):
    status_code = 404


class Conflict(SalesError):
    status_code = 409
