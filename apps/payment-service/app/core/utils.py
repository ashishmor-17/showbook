import hmac
import hashlib
from typing import Any, Dict

def calculate_hmac(payload: Dict[str, Any], secret: str) -> str:
    # Sort keys alphabetically and construct key1=value1&key2=value2, ignoring the signature itself
    ordered_items = sorted((k, str(v)) for k, v in payload.items() if k != "signature")
    message = "&".join(f"{k}={v}" for k, v in ordered_items)
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

def verify_gateway_signature(payload: Dict[str, Any], signature: str, secret: str) -> bool:
    expected = calculate_hmac(payload, secret)
    return hmac.compare_digest(expected, signature)
