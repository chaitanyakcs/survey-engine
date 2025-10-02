"""
DOCX export renderer for surveys.
Implements the abstract base renderer with Word document generation.
"""

import re
from io import BytesIO
from typing import Dict, List, Any
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn

from .base import SurveyExportRenderer, QuestionType, export_registry


class DocxSurveyRenderer(SurveyExportRenderer):
    """
    DOCX renderer for surveys using python-docx.
    Implements all question types with appropriate Word formatting.
    """

    def __init__(self):
        self.document = None
        super().__init__()

    def _register_question_types(self) -> None:
        """Register all implemented question types."""
        self._registered_types = set(QuestionType)

    def _initialize_document(self, survey_data: Dict[str, Any]) -> None:
        """Initialize the Word document."""
        self.document = Document()

        # Set document margins
        sections = self.document.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

    def _render_survey_header(self, title: str, description: str = "") -> None:
        """Render survey title and description."""
        # Title
        title_paragraph = self.document.add_heading(title, level=1)
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Description
        if description:
            desc_paragraph = self.document.add_paragraph(description)
            desc_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add some space
        self.document.add_paragraph("")

    def _finalize_document(self) -> bytes:
        """Finalize and return the document as bytes."""
        buffer = BytesIO()
        self.document.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _add_question_header(self, question: Dict[str, Any], question_number: int = None) -> None:
        """Add question header with numbering and text."""
        question_text = question.get("text", "")

        if question_number:
            header_text = f"Q{question_number}: {question_text}"
        else:
            header_text = question_text

        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(header_text)
        run.bold = True
        run.font.size = Pt(11)

    def _add_required_indicator(self, question: Dict[str, Any]) -> None:
        """Add required field indicator if applicable."""
        if question.get("required", False):
            paragraph = self.document.add_paragraph()
            run = paragraph.add_run("* Required")
            run.italic = True
            run.font.size = Pt(9)

    # Question type implementations

    def _render_instruction(self, question: Dict[str, Any]) -> None:
        """Render instruction question as an information box."""
        # Add instruction header
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run("📋 Instructions")
        run.bold = True
        run.font.size = Pt(12)

        # Add instruction content in a bordered paragraph
        instruction_paragraph = self.document.add_paragraph()
        instruction_paragraph.style = 'Quote'
        instruction_run = instruction_paragraph.add_run(question.get("text", ""))
        instruction_run.font.size = Pt(10)

        self.document.add_paragraph("")

    def _render_multiple_choice(self, question: Dict[str, Any]) -> None:
        """Render multiple choice question with checkboxes."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        paragraph = self.document.add_paragraph()
        paragraph.add_run("Select one or more options:").italic = True

        options = question.get("options", [])
        for option in options:
            option_paragraph = self.document.add_paragraph()
            option_paragraph.add_run("☐ " + option)

        self.document.add_paragraph("")

    def _render_single_choice(self, question: Dict[str, Any]) -> None:
        """Render single choice question with radio buttons."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        paragraph = self.document.add_paragraph()
        paragraph.add_run("Select one option:").italic = True

        options = question.get("options", [])
        for option in options:
            option_paragraph = self.document.add_paragraph()
            option_paragraph.add_run("○ " + option)

        self.document.add_paragraph("")

    def _render_scale(self, question: Dict[str, Any]) -> None:
        """Render scale question with numbered options."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        scale_labels = question.get("scale_labels", {})
        options = question.get("options", [])

        if scale_labels:
            # Show scale with labels
            paragraph = self.document.add_paragraph()
            paragraph.add_run("Rate on the following scale:").italic = True

            for i, option in enumerate(options, 1):
                label = scale_labels.get(str(i), "")
                scale_paragraph = self.document.add_paragraph()
                scale_paragraph.add_run(f"○ {i} - {option}" + (f" ({label})" if label else ""))
        else:
            # Simple numeric scale
            paragraph = self.document.add_paragraph()
            paragraph.add_run("Rate from 1 to " + str(len(options)) + ":").italic = True

            scale_paragraph = self.document.add_paragraph()
            scale_text = " | ".join([f"○ {i}" for i in range(1, len(options) + 1)])
            scale_paragraph.add_run(scale_text)

        self.document.add_paragraph("")

    def _render_ranking(self, question: Dict[str, Any]) -> None:
        """Render ranking question with numbered lines."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        paragraph = self.document.add_paragraph()
        paragraph.add_run("Rank the following items in order of preference (1 = most preferred):").italic = True

        options = question.get("options", [])
        for option in options:
            rank_paragraph = self.document.add_paragraph()
            rank_paragraph.add_run(f"___ {option}")

        self.document.add_paragraph("")

    def _render_text(self, question: Dict[str, Any]) -> None:
        """Render text input question."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        # Add response area
        for _ in range(3):
            self.document.add_paragraph("_" * 80)

        self.document.add_paragraph("")

    def _render_open_text(self, question: Dict[str, Any]) -> None:
        """Render open text question (alias for text)."""
        self._render_text(question)

    def _render_numeric(self, question: Dict[str, Any]) -> None:
        """Render numeric input question."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        paragraph = self.document.add_paragraph()
        paragraph.add_run("Enter a numeric value: _______________")

        self.document.add_paragraph("")

    def _render_date(self, question: Dict[str, Any]) -> None:
        """Render date input question."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        paragraph = self.document.add_paragraph()
        paragraph.add_run("Enter date (MM/DD/YYYY): _______________")

        self.document.add_paragraph("")

    def _render_boolean(self, question: Dict[str, Any]) -> None:
        """Render yes/no question."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        paragraph = self.document.add_paragraph()
        paragraph.add_run("○ Yes    ○ No")

        self.document.add_paragraph("")

    def _render_multiple_select(self, question: Dict[str, Any]) -> None:
        """Render multiple select question (alias for multiple choice)."""
        self._render_multiple_choice(question)

    def _render_matrix(self, question: Dict[str, Any]) -> None:
        """Render basic matrix question."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        # This is a simplified matrix - for complex matrices use matrix_likert
        options = question.get("options", [])
        if len(options) < 2:
            self.document.add_paragraph("Matrix format: Please specify rows and columns in question options.")
            return

        # Create simple table
        table = self.document.add_table(rows=len(options), cols=2)
        table.style = 'Table Grid'

        for i, option in enumerate(options):
            table.cell(i, 0).text = option
            table.cell(i, 1).text = "☐"

        self.document.add_paragraph("")

    def _extract_attributes_from_text(self, text: str) -> List[str]:
        """Extract attributes from question text (used by specialized components)."""
        # Look for comma-separated attributes after question mark or colon
        search_text = text

        question_mark_index = text.find('?')
        if question_mark_index != -1:
            search_text = text[question_mark_index + 1:].strip()
        else:
            colon_index = text.find(':')
            if colon_index != -1:
                search_text = text[colon_index + 1:].strip()

        # Remove trailing period if present
        clean_text = search_text.rstrip('.')

        # Split by comma and clean up
        attributes = [attr.strip() for attr in clean_text.split(',') if attr.strip()]
        return attributes

    def _render_matrix_likert(self, question: Dict[str, Any]) -> None:
        """Render matrix likert question with proper table formatting."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        # Extract attributes from question text
        attributes = self._extract_attributes_from_text(question.get("text", ""))
        options = question.get("options", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"])

        if not attributes:
            self.document.add_paragraph("Matrix Likert: Unable to parse attributes from question text.")
            return

        # Create table with headers
        table = self.document.add_table(rows=len(attributes) + 1, cols=len(options) + 1)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Header row
        table.cell(0, 0).text = "Items"
        for j, option in enumerate(options):
            table.cell(0, j + 1).text = option

        # Data rows
        for i, attribute in enumerate(attributes):
            table.cell(i + 1, 0).text = attribute
            for j in range(len(options)):
                table.cell(i + 1, j + 1).text = "○"

        self.document.add_paragraph("")

    def _render_constant_sum(self, question: Dict[str, Any]) -> None:
        """Render constant sum allocation question."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        # Parse total points from question text
        text = question.get("text", "")
        points_match = re.search(r'(\d+)\s+points?', text, re.IGNORECASE)
        total_points = int(points_match.group(1)) if points_match else 100

        # Extract attributes
        attributes = self._extract_attributes_from_text(text)

        if not attributes:
            self.document.add_paragraph("Constant Sum: Unable to parse attributes from question text.")
            return

        paragraph = self.document.add_paragraph()
        paragraph.add_run(f"Allocate {total_points} points across the following items:").italic = True

        # Create allocation table
        table = self.document.add_table(rows=len(attributes) + 1, cols=2)
        table.style = 'Table Grid'

        table.cell(0, 0).text = "Item"
        table.cell(0, 1).text = "Points"

        for i, attribute in enumerate(attributes):
            table.cell(i + 1, 0).text = attribute
            table.cell(i + 1, 1).text = "____"

        # Add total row
        total_paragraph = self.document.add_paragraph()
        total_paragraph.add_run(f"Total: _____ / {total_points} points").bold = True

        self.document.add_paragraph("")

    def _render_numeric_grid(self, question: Dict[str, Any]) -> None:
        """Render numeric grid question."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        # Extract attributes
        attributes = self._extract_attributes_from_text(question.get("text", ""))
        options = question.get("options", [])

        if not attributes:
            self.document.add_paragraph("Numeric Grid: Unable to parse attributes from question text.")
            return

        paragraph = self.document.add_paragraph()
        paragraph.add_run("Provide numeric values for each item:").italic = True

        # Create grid table
        table = self.document.add_table(rows=len(attributes) + 1, cols=len(options) + 1)
        table.style = 'Table Grid'

        # Header row
        table.cell(0, 0).text = "Items"
        for j, option in enumerate(options):
            table.cell(0, j + 1).text = option

        # Data rows
        for i, attribute in enumerate(attributes):
            table.cell(i + 1, 0).text = attribute
            for j in range(len(options)):
                table.cell(i + 1, j + 1).text = "____"

        self.document.add_paragraph("")

    def _render_numeric_open(self, question: Dict[str, Any]) -> None:
        """Render numeric open question with currency detection."""
        self._add_question_header(question)
        self._add_required_indicator(question)

        text = question.get("text", "")
        methodology = question.get("methodology", "")

        # Detect currency
        currency_match = re.search(r'[£$€¥₹]', text)
        currency = currency_match.group(0) if currency_match else "$"

        # Detect unit
        unit_match = re.search(r'per\s+([^,.?]+)', text, re.IGNORECASE)
        unit = unit_match.group(1).strip() if unit_match else ""

        # Check for Van Westendorp
        is_van_westendorp = 'van_westendorp' in methodology.lower() or 'van westendorp' in text.lower()

        if is_van_westendorp:
            paragraph = self.document.add_paragraph()
            paragraph.add_run("Van Westendorp Price Sensitivity Question").bold = True

            guidance_paragraph = self.document.add_paragraph()
            guidance_paragraph.add_run("Please think about the price point where you would have the described reaction to the product. Consider your local market conditions and personal budget.").italic = True

        # Currency and amount input
        input_paragraph = self.document.add_paragraph()
        currency_text = f"Currency: {currency}    Amount: {currency}_________"
        if unit:
            currency_text += f" per {unit}"
        input_paragraph.add_run(currency_text)

        self.document.add_paragraph("")


# Register the DOCX renderer
export_registry.register_renderer("docx", DocxSurveyRenderer)