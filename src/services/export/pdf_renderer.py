"""
PDF export renderer for surveys.
Implements the abstract base renderer with PDF generation using reportlab.
"""

import re
from io import BytesIO
from typing import Dict, List, Any

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import black, blue, darkblue, lightgrey
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.platypus.flowables import KeepTogether
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    # ReportLab not available - used for testing environments
    letter = None
    A4 = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    inch = None
    black = None
    blue = None
    darkblue = None
    lightgrey = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    Table = None
    TableStyle = None
    KeepTogether = None
    TA_LEFT = None
    TA_CENTER = None
    TA_JUSTIFY = None
    canvas = None
    REPORTLAB_AVAILABLE = False

from .base import SurveyExportRenderer, QuestionType, export_registry


class PdfSurveyRenderer(SurveyExportRenderer):
    """
    PDF export renderer for surveys using ReportLab.
    Generates professional PDF documents with proper formatting.
    """

    def __init__(self) -> None:
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF export. Install with: pip install reportlab")
        super().__init__()
        self.doc = None
        self.styles = None
        self.story = []
        self.question_number = 1

    def _register_question_types(self) -> None:
        """Register all implemented question types."""
        self._registered_types = {
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.SCALE,
            QuestionType.TEXT,
            QuestionType.NUMERIC,
            QuestionType.DATE,
            QuestionType.BOOLEAN,
            QuestionType.RANKING,
            QuestionType.MATRIX_LIKERT,
            QuestionType.CONSTANT_SUM,
            QuestionType.GABOR_GRANGER,
            QuestionType.NUMERIC_GRID,
            QuestionType.NUMERIC_OPEN,
            QuestionType.INSTRUCTION,
            QuestionType.SINGLE_CHOICE,
            QuestionType.MATRIX,
            QuestionType.OPEN_TEXT,
            QuestionType.MULTIPLE_SELECT,
            QuestionType.LIKERT,
            QuestionType.OPEN_END,
            QuestionType.DISPLAY_ONLY,
            QuestionType.SINGLE_OPEN,
            QuestionType.MULTIPLE_OPEN,
            QuestionType.OPEN_ENDED,
        }

    def _initialize_document(self, survey_data: Dict[str, Any]) -> None:
        """Initialize the PDF document."""
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        self.styles = getSampleStyleSheet()
        self.story = []
        self.question_number = 1

        # Define custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=darkblue
        )

        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=blue
        )

        self.question_style = ParagraphStyle(
            'QuestionStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            leftIndent=0,
            textColor=black
        )

        self.option_style = ParagraphStyle(
            'OptionStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            leftIndent=20,
            textColor=black
        )

        self.instruction_style = ParagraphStyle(
            'InstructionStyle',
            parent=self.styles['Italic'],
            fontSize=10,
            spaceAfter=10,
            leftIndent=0,
            textColor=blue
        )

    def _render_survey_header(self, title: str, description: str = "") -> None:
        """Render survey title and description."""
        # Add title
        self.story.append(Paragraph(title, self.title_style))
        
        # Add description if provided
        if description:
            self.story.append(Paragraph(description, self.subtitle_style))
        
        # Add some space
        self.story.append(Spacer(1, 20))

    def render_survey(self, survey_data: Dict[str, Any]) -> bytes:
        """
        Main entry point for rendering a complete survey with sections support.

        Args:
            survey_data: Dictionary containing survey metadata and sections/questions

        Returns:
            Rendered survey as bytes
        """
        self._initialize_document(survey_data)

        # Render survey header/metadata
        if "title" in survey_data:
            self._render_survey_header(survey_data["title"], survey_data.get("description", ""))

        # Check if survey uses sections format
        if "sections" in survey_data:
            # Render sections with text blocks and questions
            sections = survey_data.get("sections", [])
            global_question_number = 1
            for section in sections:
                self._render_section(section, global_question_number)
                # Update global question number after processing section
                questions = section.get("questions", [])
                for question in questions:
                    if question.get("type") != "instruction":
                        global_question_number += 1
        else:
            # Legacy format: render questions directly
            questions = survey_data.get("questions", [])
            for question in questions:
                self._render_question(question)

        return self._finalize_document()

    def _render_section(self, section: Dict[str, Any], global_question_number: int) -> None:
        """Render a survey section with text blocks and questions."""
        # Section title
        if section.get("title"):
            section_style = ParagraphStyle(
                'SectionStyle',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceAfter=15,
                spaceBefore=20,
                textColor=darkblue
            )
            self.story.append(Paragraph(section["title"], section_style))

        # Section description
        if section.get("description"):
            desc_style = ParagraphStyle(
                'SectionDescStyle',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=15,
                textColor=black
            )
            self.story.append(Paragraph(section["description"], desc_style))

        # Section text blocks
        if section.get("text_blocks"):
            for text_block in section["text_blocks"]:
                self._render_text_block(text_block)

        # Section questions
        questions = section.get("questions", [])
        for question in questions:
            # Set the question number before rendering
            self.question_number = global_question_number
            self._render_question(question)
            if question.get("type") != "instruction":
                global_question_number += 1

    def _render_text_block(self, text_block: Dict[str, Any]) -> None:
        """Render a text block within a section."""
        if text_block.get("content"):
            text_style = ParagraphStyle(
                'TextBlockStyle',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=10,
                leftIndent=10,
                textColor=black
            )
            self.story.append(Paragraph(text_block["content"], text_style))

    def _finalize_document(self) -> bytes:
        """Finalize and return the document as bytes."""
        self.doc.build(self.story)
        self.buffer.seek(0)
        return self.buffer.getvalue()

    def _add_question_header(self, question: Dict[str, Any], question_number: int | None = None) -> None:
        """Add question number and text header."""
        if question_number is None:
            question_number = self.question_number

        question_text = question.get("text", "")
        if question_text:
            # Add question number and text
            full_question = f"Q{question_number}. {question_text}"
            self.story.append(Paragraph(full_question, self.question_style))

    def _render_multiple_choice(self, question: Dict[str, Any]) -> None:
        """Render multiple choice question."""
        self._add_question_header(question)
        
        options = question.get("options", [])
        if options:
            for i, option in enumerate(options, 1):
                option_text = f"({chr(96 + i)}) {option}"  # a), b), c), etc.
                self.story.append(Paragraph(option_text, self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_scale(self, question: Dict[str, Any]) -> None:
        """Render scale question."""
        self._add_question_header(question)
        
        # Add scale description
        min_label = question.get("min_label", "Strongly Disagree")
        max_label = question.get("max_label", "Strongly Agree")
        scale_text = f"Scale: {min_label} (1) ————————————— (5) {max_label}"
        self.story.append(Paragraph(scale_text, self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_text(self, question: Dict[str, Any]) -> None:
        """Render text input question."""
        self._add_question_header(question)
        
        # Add placeholder text
        placeholder = question.get("placeholder", "Please enter your response here...")
        self.story.append(Paragraph(f"Response: {placeholder}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_numeric(self, question: Dict[str, Any]) -> None:
        """Render numeric input question."""
        self._add_question_header(question)
        
        # Add numeric constraints
        min_val = question.get("min_value")
        max_val = question.get("max_value")
        if min_val is not None or max_val is not None:
            constraints = []
            if min_val is not None:
                constraints.append(f"Minimum: {min_val}")
            if max_val is not None:
                constraints.append(f"Maximum: {max_val}")
            constraint_text = f"Constraints: {', '.join(constraints)}"
            self.story.append(Paragraph(constraint_text, self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_date(self, question: Dict[str, Any]) -> None:
        """Render date input question."""
        self._add_question_header(question)
        
        # Add date format info
        date_format = question.get("date_format", "MM/DD/YYYY")
        self.story.append(Paragraph(f"Format: {date_format}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1


    def _render_boolean(self, question: Dict[str, Any]) -> None:
        """Render boolean question."""
        self._add_question_header(question)
        
        # Add boolean options
        true_label = question.get("true_label", "Yes")
        false_label = question.get("false_label", "No")
        self.story.append(Paragraph(f"Options: {true_label} / {false_label}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_ranking(self, question: Dict[str, Any]) -> None:
        """Render ranking question."""
        self._add_question_header(question)
        
        options = question.get("options", [])
        if options:
            self.story.append(Paragraph("Please rank the following options (1 = highest priority):", self.option_style))
            for i, option in enumerate(options, 1):
                option_text = f"{i}. {option}"
                self.story.append(Paragraph(option_text, self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_matrix_likert(self, question: Dict[str, Any]) -> None:
        """Render matrix Likert question."""
        self._add_question_header(question)
        
        # Create matrix table
        statements = question.get("statements", [])
        scale_labels = question.get("scale_labels", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"])
        
        if statements and scale_labels:
            # Create table data
            table_data = [["Statement"] + scale_labels]
            for statement in statements:
                row = [statement] + [""] * len(scale_labels)
                table_data.append(row)
            
            # Create table
            table = Table(table_data, colWidths=[3*inch] + [0.8*inch] * len(scale_labels))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), 'white'),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            
            self.story.append(table)
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_constant_sum(self, question: Dict[str, Any]) -> None:
        """Render constant sum question."""
        self._add_question_header(question)
        
        options = question.get("options", [])
        total = question.get("total", 100)
        
        if options:
            self.story.append(Paragraph(f"Please distribute {total} points among the following options:", self.option_style))
            for option in options:
                self.story.append(Paragraph(f"• {option}: _____ points", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_gabor_granger(self, question: Dict[str, Any]) -> None:
        """Render Gabor-Granger pricing question."""
        self._add_question_header(question)
        
        # Add pricing context
        product = question.get("product", "this product")
        self.story.append(Paragraph(f"Product: {product}", self.option_style))
        
        # Add price range
        min_price = question.get("min_price", 0)
        max_price = question.get("max_price", 100)
        self.story.append(Paragraph(f"Price range: ${min_price} - ${max_price}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_numeric_grid(self, question: Dict[str, Any]) -> None:
        """Render numeric grid question."""
        self._add_question_header(question)
        
        # Create grid table
        rows = question.get("rows", [])
        columns = question.get("columns", [])
        
        if rows and columns:
            table_data = [[""] + columns]  # Header row
            for row in rows:
                table_row = [row] + [""] * len(columns)
                table_data.append(table_row)
            
            # Create table
            table = Table(table_data, colWidths=[1.5*inch] + [0.8*inch] * len(columns))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), 'white'),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            
            self.story.append(table)
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_numeric_open(self, question: Dict[str, Any]) -> None:
        """Render numeric open question."""
        self._add_question_header(question)
        
        # Add numeric constraints
        min_val = question.get("min_value")
        max_val = question.get("max_value")
        if min_val is not None or max_val is not None:
            constraints = []
            if min_val is not None:
                constraints.append(f"Minimum: {min_val}")
            if max_val is not None:
                constraints.append(f"Maximum: {max_val}")
            constraint_text = f"Constraints: {', '.join(constraints)}"
            self.story.append(Paragraph(constraint_text, self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_instruction(self, question: Dict[str, Any]) -> None:
        """Render instruction text."""
        instruction_text = question.get("text", "")
        if instruction_text:
            self.story.append(Paragraph(instruction_text, self.instruction_style))
            self.story.append(Spacer(1, 8))

    def _render_unsupported_question_type(self, question: Dict[str, Any]) -> None:
        """Render unsupported question types with a generic text area."""
        self._add_question_header(question)
        
        # Add generic response area
        self.story.append(Paragraph("Response: ________________________", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    # Additional abstract methods required by base class
    def _render_single_choice(self, question: Dict[str, Any]) -> None:
        """Render single choice question."""
        self._add_question_header(question)
        
        options = question.get("options", [])
        if options:
            for i, option in enumerate(options, 1):
                option_text = f"({i}) {option}"  # 1), 2), 3), etc.
                self.story.append(Paragraph(option_text, self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_matrix(self, question: Dict[str, Any]) -> None:
        """Render matrix question."""
        self._add_question_header(question)
        
        # Create matrix table
        rows = question.get("rows", [])
        columns = question.get("columns", [])
        
        if rows and columns:
            table_data = [[""] + columns]  # Header row
            for row in rows:
                table_row = [row] + [""] * len(columns)
                table_data.append(table_row)
            
            # Create table
            table = Table(table_data, colWidths=[1.5*inch] + [0.8*inch] * len(columns))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), 'white'),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            
            self.story.append(table)
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_open_text(self, question: Dict[str, Any]) -> None:
        """Render open text question."""
        self._add_question_header(question)
        
        # Add placeholder text
        placeholder = question.get("placeholder", "Please enter your response here...")
        self.story.append(Paragraph(f"Response: {placeholder}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_multiple_select(self, question: Dict[str, Any]) -> None:
        """Render multiple select question."""
        self._add_question_header(question)
        
        options = question.get("options", [])
        if options:
            for i, option in enumerate(options, 1):
                option_text = f"☐ {option}"  # Checkbox style
                self.story.append(Paragraph(option_text, self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_likert(self, question: Dict[str, Any]) -> None:
        """Render Likert scale question."""
        self._add_question_header(question)
        
        # Add scale description
        min_label = question.get("min_label", "Strongly Disagree")
        max_label = question.get("max_label", "Strongly Agree")
        scale_text = f"Scale: {min_label} (1) ————————————— (5) {max_label}"
        self.story.append(Paragraph(scale_text, self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_open_end(self, question: Dict[str, Any]) -> None:
        """Render open-ended question."""
        self._add_question_header(question)
        
        # Add placeholder text
        placeholder = question.get("placeholder", "Please provide your detailed response...")
        self.story.append(Paragraph(f"Response: {placeholder}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_display_only(self, question: Dict[str, Any]) -> None:
        """Render display-only question."""
        instruction_text = question.get("text", "")
        if instruction_text:
            self.story.append(Paragraph(instruction_text, self.instruction_style))
            self.story.append(Spacer(1, 8))

    def _render_single_open(self, question: Dict[str, Any]) -> None:
        """Render single open question."""
        self._add_question_header(question)
        
        # Add placeholder text
        placeholder = question.get("placeholder", "Please enter your response here...")
        self.story.append(Paragraph(f"Response: {placeholder}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_multiple_open(self, question: Dict[str, Any]) -> None:
        """Render multiple open question."""
        self._add_question_header(question)
        
        # Add placeholder text
        placeholder = question.get("placeholder", "Please enter your responses here...")
        self.story.append(Paragraph(f"Responses: {placeholder}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1

    def _render_open_ended(self, question: Dict[str, Any]) -> None:
        """Render open-ended question."""
        self._add_question_header(question)
        
        # Add placeholder text
        placeholder = question.get("placeholder", "Please provide your detailed response...")
        self.story.append(Paragraph(f"Response: {placeholder}", self.option_style))
        
        self.story.append(Spacer(1, 12))
        self.question_number += 1


# Register the PDF renderer
export_registry.register_renderer("pdf", PdfSurveyRenderer)
