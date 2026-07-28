from showbook_common.errors import AppException

class MovieNotFoundException(AppException):
    def __init__(self, slug: str):
        super().__init__(
            code="MOVIE_NOT_FOUND",
            message=f"Movie with slug '{slug}' was not found",
            status_code=404,
            details={"slug": slug}
        )

class EventNotFoundException(AppException):
    def __init__(self, slug: str):
        super().__init__(
            code="EVENT_NOT_FOUND",
            message=f"Event with slug '{slug}' was not found",
            status_code=404,
            details={"slug": slug}
        )

class ServiceUnavailableException(AppException):
    def __init__(self, service_name: str):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=f"External service '{service_name}' is currently unavailable",
            status_code=503
        )
