from typing import Any, Dict, Optional

from showbook_common.errors.exceptions import AppException

class PaymentServiceException(AppException):
    pass

class PaymentTransactionNotFoundException(PaymentServiceException):
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="PAYMENT_NOT_FOUND",
            message="Payment transaction not found",
            status_code=404,
            details=details
        )

class InvalidGatewayException(PaymentServiceException):
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="INVALID_GATEWAY",
            message="Unsupported or invalid payment gateway provider",
            status_code=400,
            details=details
        )

class SignatureValidationFailedException(PaymentServiceException):
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="SIGNATURE_VALIDATION_FAILED",
            message="Gateway signature verification failed",
            status_code=400,
            details=details
        )

class TransactionAlreadyProcessedException(PaymentServiceException):
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="TRANSACTION_ALREADY_PROCESSED",
            message="This payment transaction has already been processed",
            status_code=400,
            details=details
        )
