"""
Lightweight services package initializer.

Avoids importing heavy submodules at import time to prevent configuration side-effects
during tests and simple package imports. Submodules are loaded lazily on attribute access.
"""

from typing import Any
import importlib

__all__ = [
    "SurveyService",
    "GoldenService",
    "AnalyticsService",
    "EmbeddingService",
    "RetrievalService",
    "GenerationService",
    "ValidationService",
    "WebSocketNotificationService",
]


_ATTR_TO_MODULE = {
    "SurveyService": "src.services.survey_service",
    "GoldenService": "src.services.golden_service",
    "AnalyticsService": "src.services.analytics_service",
    "EmbeddingService": "src.services.embedding_service",
    "RetrievalService": "src.services.retrieval_service",
    "GenerationService": "src.services.generation_service",
    "ValidationService": "src.services.validation_service",
    "WebSocketNotificationService": "src.services.websocket_client",
}


def __getattr__(name: str) -> Any:  # PEP 562 lazy attribute access
    module_path = _ATTR_TO_MODULE.get(name)
    if module_path is None:
        raise AttributeError(f"module 'src.services' has no attribute '{name}'")
    module = importlib.import_module(module_path)
    return getattr(module, name)