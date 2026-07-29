from showbook_common.errors.exceptions import AppException

class CityNotFoundException(AppException):
    def __init__(self, message: str = "City not found"):
        super().__init__(
            code="CITY_NOT_FOUND",
            message=message,
            status_code=404
        )

class VenueNotFoundException(AppException):
    def __init__(self, message: str = "Venue not found"):
        super().__init__(
            code="VENUE_NOT_FOUND",
            message=message,
            status_code=404
        )

class ShowtimeNotFoundException(AppException):
    def __init__(self, message: str = "Showtime not found"):
        super().__init__(
            code="SHOWTIME_NOT_FOUND",
            message=message,
            status_code=404
        )
