import logging
import sys
import structlog

def setup_logging(service_name: str, level: str = "INFO") -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors for both structlog and standard library logs
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.dict_tracebacks,
    ]

    # Configure structlog
    structlog.configure(
        processors=processors + [
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging formatter (for Uvicorn, etc.)
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_processors=processors,
        processor=structlog.processors.JSONRenderer(),
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Reset existing handlers to avoid duplicate logs
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)

    # Bind the service name context globally
    structlog.contextvars.bind_contextvars(service=service_name)

    # Propagate standard library logs (like uvicorn) to the root logger
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn.error").propagate = True
