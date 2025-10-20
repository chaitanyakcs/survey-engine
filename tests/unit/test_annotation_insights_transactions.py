import asyncio

from src.services.annotation_insights_service import AnnotationInsightsService
from src.services.retrieval_service import RetrievalService


class _StubDB:
    """A minimal stub for the SQLAlchemy Session used in early-return paths."""

    def execute(self, *_args, **_kwargs):
        # allow ensure_healthy_session to run without raising
        class _Res:
            def scalar(self):
                return 1

        return _Res()


async def _run(coro):
    return await coro


def test_annotation_insights_skips_non_uuid_survey_ids():
    service = AnnotationInsightsService(_StubDB())

    # Non-UUID should be skipped gracefully and return None
    question_text = asyncio.get_event_loop().run_until_complete(
        _run(service._get_question_text("q1", "test-survey-123"))
    )
    assert question_text is None

    section = asyncio.get_event_loop().run_until_complete(
        _run(service._get_section_structure(1, "not-a-uuid"))
    )
    assert section is None


def test_retrieval_annotation_score_defaults_for_non_uuid():
    service = RetrievalService(_StubDB())
    score = asyncio.get_event_loop().run_until_complete(
        _run(service._calculate_annotation_score("legacy-id-42"))
    )
    assert score == 3.0


