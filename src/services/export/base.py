"""
Abstract base classes for survey export functionality.
Ensures type safety and enforces implementation of all question types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Set
from enum import Enum


class QuestionType(Enum):
    """Enumeration of all supported question types."""
    # Basic question types
    MULTIPLE_CHOICE = "multiple_choice"
    SINGLE_CHOICE = "single_choice"
    TEXT = "text"
    SCALE = "scale"
    RATING = "rating"
    YES_NO = "yes_no"
    DROPDOWN = "dropdown"
    MATRIX = "matrix"
    RANKING = "ranking"
    NUMERIC = "numeric"
    DATE = "date"
    BOOLEAN = "boolean"
    FILE_UPLOAD = "file_upload"
    
    # Open-ended variants
    OPEN_TEXT = "open_text"
    OPEN_END = "open_end"
    OPEN_ENDED = "open_ended"
    SINGLE_OPEN = "single_open"
    MULTIPLE_OPEN = "multiple_open"
    
    # Numeric variants
    NUMERIC_OPEN = "numeric_open"
    NUMERIC_GRID = "numeric_grid"
    
    # Matrix/Grid variants
    MATRIX_LIKERT = "matrix_likert"
    CONSTANT_SUM = "constant_sum"
    
    # Specialized types
    LIKERT = "likert"
    MULTIPLE_SELECT = "multiple_select"
    
    # Display types
    INSTRUCTION = "instruction"
    DISPLAY_ONLY = "display_only"
    
    # Methodology-specific types
    VAN_WESTENDORP = "van_westendorp"
    GABOR_GRANGER = "gabor_granger"
    CONJOINT = "conjoint"
    MAXDIFF = "maxdiff"
    
    # Fallback
    UNKNOWN = "unknown"


class SurveyExportRenderer(ABC):
    """
    Abstract base class for survey export renderers.
    Enforces implementation of all question types to ensure complete coverage.
    """

    def __init__(self) -> None:
        self._registered_types: Set[QuestionType] = set()
        self._register_question_types()
        self._validate_complete_implementation()

    @abstractmethod
    def _register_question_types(self) -> None:
        """
        Register all implemented question types.
        Must be implemented by subclasses to declare which types they handle.
        """
        pass

    def _validate_complete_implementation(self) -> None:
        """
        Validates that all question types are implemented.
        Raises ValueError if any question type is missing.
        """
        all_types = {t.value for t in QuestionType}
        missing_types = all_types - self._registered_types

        if missing_types:
            missing_names = list(missing_types)
            raise ValueError(
                f"Incomplete implementation: Missing renderers for question types: {missing_names}. "
                f"All question types must be implemented to ensure export completeness."
            )

    def render_survey(self, survey_data: Dict[str, Any]) -> bytes:
        """
        Main entry point for rendering a complete survey.

        Args:
            survey_data: Dictionary containing survey metadata and questions

        Returns:
            Rendered survey as bytes
        """
        self._initialize_document(survey_data)

        # Render survey header/metadata
        if "title" in survey_data:
            self._render_survey_header(survey_data["title"], survey_data.get("description", ""))

        # Render questions
        questions = survey_data.get("questions", [])
        for question in questions:
            self._render_question(question)

        return self._finalize_document()

    @abstractmethod
    def _initialize_document(self, survey_data: Dict[str, Any]) -> None:
        """Initialize the document for rendering."""
        pass

    @abstractmethod
    def _render_survey_header(self, title: str, description: str = "") -> None:
        """Render survey title and description."""
        pass

    def _render_question(self, question: Dict[str, Any]) -> None:
        """
        Route question to appropriate renderer based on type.

        Args:
            question: Question data dictionary
        """
        question_type = question.get("type")
        if not question_type:
            raise ValueError(f"Question missing 'type' field: {question}")

        try:
            q_type = QuestionType(question_type)
        except ValueError:
            # Handle unknown question types gracefully
            self._render_unsupported_question_type(question)
            return

        # Route to specific renderer
        method_name = f"_render_{question_type}"
        renderer_method = getattr(self, method_name, None)

        if not renderer_method:
            # Handle missing renderer methods gracefully
            self._render_unsupported_question_type(question)
            return

        renderer_method(question)

    def _render_unsupported_question_type(self, question: Dict[str, Any]) -> None:
        """
        Render unsupported question types with a generic text area.
        This ensures DOCX generation doesn't fail for unknown question types.
        Must be implemented by subclasses.
        
        Args:
            question: Question data dictionary
        """
        raise NotImplementedError("Subclasses must implement _render_unsupported_question_type")

    @abstractmethod
    def _finalize_document(self) -> bytes:
        """Finalize and return the document as bytes."""
        pass

    # Abstract methods for each question type - enforces implementation
    @abstractmethod
    def _render_multiple_choice(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_scale(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_text(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_ranking(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_instruction(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_single_choice(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_matrix(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_numeric(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_date(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_boolean(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_open_text(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_multiple_select(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_matrix_likert(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_constant_sum(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_numeric_grid(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_numeric_open(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_likert(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_open_end(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_display_only(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_single_open(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_multiple_open(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_open_ended(self, question: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def _render_gabor_granger(self, question: Dict[str, Any]) -> None:
        pass


class ExportRegistry:
    """Registry for managing available export formats."""

    def __init__(self) -> None:
        self._renderers: Dict[str, type] = {}

    def register_renderer(self, format_name: str, renderer_class: type) -> None:
        """Register a renderer for a specific format."""
        if not issubclass(renderer_class, SurveyExportRenderer):
            raise ValueError(f"Renderer must inherit from SurveyExportRenderer")

        self._renderers[format_name] = renderer_class

    def get_renderer(self, format_name: str) -> SurveyExportRenderer:
        """Get an instance of the renderer for the specified format."""
        if format_name not in self._renderers:
            raise ValueError(f"No renderer registered for format: {format_name}")

        renderer_class = self._renderers[format_name]
        return renderer_class()  # type: ignore[no-any-return]

    def get_available_formats(self) -> List[str]:
        """Get list of available export formats."""
        return list(self._renderers.keys())


# Global export registry instance
export_registry = ExportRegistry()