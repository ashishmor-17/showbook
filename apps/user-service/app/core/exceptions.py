from showbook_common.errors.exceptions import AppException

class UserAlreadyExistsException(AppException):
    def __init__(self, message: str = "A user with this email already exists"):
        super().__init__(
            code="USER_ALREADY_EXISTS",
            message=message,
            status_code=409
        )

class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Incorrect email or password"):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message=message,
            status_code=401
        )

class TokenReusedException(AppException):
    def __init__(self, message: str = "Refresh token reuse detected"):
        super().__init__(
            code="TOKEN_REUSED",
            message=message,
            status_code=401
        )

class InvalidTokenException(AppException):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(
            code="INVALID_TOKEN",
            message=message,
            status_code=401
        )

class RateLimitExceededException(AppException):
    def __init__(self, message: str = "Too many login attempts. Please try again in 1 minute"):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=429
        )

class InvalidOTPException(AppException):
    def __init__(self, message: str = "Invalid or expired OTP"):
        super().__init__(
            code="INVALID_OTP",
            message=message,
            status_code=400
        )

class UserNotFoundException(AppException):
    def __init__(self, message: str = "User not found"):
        super().__init__(
            code="USER_NOT_FOUND",
            message=message,
            status_code=404
        )

class EmailNotVerifiedException(AppException):
    def __init__(self, message: str = "Email not verified. Please verify your OTP first."):
        super().__init__(
            code="EMAIL_NOT_VERIFIED",
            message=message,
            status_code=403
        )
