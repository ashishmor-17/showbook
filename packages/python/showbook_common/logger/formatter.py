import json
import logging
from datetime import datetime, UTC
from showbook_common.middleware.context import get_correlation_id

class JSONFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "trace_id": get_correlation_id() or "",
            "message": record.getMessage(),
            "logger": record.name,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include other attributes passed in extra
        for key, val in record.__dict__.items():
            if key not in [
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            ] and not key.startswith("_"):
                log_data[key] = val

        return json.dumps(log_data)
