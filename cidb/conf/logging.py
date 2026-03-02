from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from typing import Any

import orjson
import structlog
from structlog.types import EventDict, Processor

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def _is_json_output() -> bool:
    return os.environ.get("DEBUG", "0") != "0"


def _add_request_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    if request_id := request_id_var.get():
        event_dict["request_id"] = request_id
    return event_dict


def _orjson_serializer(obj: Any, **kwargs: Any) -> str:
    return orjson.dumps(
        obj,
        default=str,
        option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SORT_KEYS,
    ).decode()


def _get_shared_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        _add_request_id,
    ]


def _get_renderer() -> Processor:
    if _is_json_output():
        return structlog.processors.JSONRenderer(serializer=_orjson_serializer)
    return structlog.dev.ConsoleRenderer(colors=True)


def configure_logging() -> None:
    shared_processors = _get_shared_processors()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _get_renderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    logging.getLogger("cidb").setLevel(logging.DEBUG if not _is_json_output() else logging.INFO)

    noisy_loggers = [
        "django.security.DisallowedHost",
        "django.request",
        "httpcore",
        "httpx",
        "openai",
        "pydantic_ai",
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    if os.environ.get("LOG_SQL"):
        logging.getLogger("django.db.backends").setLevel(logging.DEBUG)
    else:
        logging.getLogger("django.db.backends").setLevel(logging.WARNING)
