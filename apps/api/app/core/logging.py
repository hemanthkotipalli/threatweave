import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# Context variable to hold the Request ID contextually across async calls
request_id_context: ContextVar[str] = ContextVar("request_id", default="")


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as structured JSON strings.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Construct the basic structured log dictionary
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
        }

        # Dynamically inject the X-Request-ID from the current async context if set
        req_id = request_id_context.get()
        if req_id:
            log_record["request_id"] = req_id

        # Include traceback details if an exception is present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


        return json.dumps(log_record)

def setup_logging() -> None:
    """
    Configures the root logger to output structured JSON logs to stdout
    and configures key framework loggers to propagate to root.
    """
    root_logger = logging.getLogger()
    
    # Clean up pre-existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Set root logging level
    root_logger.setLevel(logging.INFO)

    # Output to standard output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(console_handler)

    # Redirect third-party loggers to propagate to our root JSON logger
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True
