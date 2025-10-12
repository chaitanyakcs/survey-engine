import logging
from typing import Any, Dict


def log_service_configuration(
    logger: logging.Logger,
    service_name: str,
    *,
    event: str,
    details: Dict[str, Any],
) -> None:
    """Log structured configuration details for service lifecycle events."""
    logger.debug(
        "%s configuration",
        service_name,
        extra={
            "event": event,
            "service": service_name,
            "details": details,
        },
    )
