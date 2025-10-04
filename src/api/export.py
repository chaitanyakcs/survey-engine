"""
Survey export API endpoints.
Handles export of surveys to various formats (DOCX, etc.).
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import logging

from src.services.export.base import export_registry
from src.services.export.docx_renderer import DocxSurveyRenderer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


class SurveyExportRequest(BaseModel):
    """Request model for survey export."""
    survey_data: Dict[str, Any]
    format: str = "docx"
    filename: str = None


class ExportFormatInfo(BaseModel):
    """Information about available export formats."""
    format: str
    description: str
    mime_type: str
    file_extension: str


@router.get("/formats", response_model=List[ExportFormatInfo])
async def get_export_formats():
    """Get list of available export formats."""
    formats = [
        ExportFormatInfo(
            format="docx",
            description="Microsoft Word Document",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_extension=".docx"
        )
    ]
    return formats


@router.post("/survey")
async def export_survey(request: SurveyExportRequest):
    """
    Export a survey to the specified format.

    Args:
        request: Survey export request containing survey data and format

    Returns:
        File response with the exported survey
    """
    try:
        # Validate format
        available_formats = export_registry.get_available_formats()
        if request.format not in available_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {request.format}. Available formats: {available_formats}"
            )

        # Get renderer
        renderer = export_registry.get_renderer(request.format)

        # Validate survey data
        if not request.survey_data:
            raise HTTPException(status_code=400, detail="Survey data is required")

        # Check if survey uses sections format or legacy questions format
        if "sections" in request.survey_data:
            # Sections format - validate sections
            sections = request.survey_data.get("sections", [])
            logger.info(f"Export validation: Found {len(sections)} sections")
            
            if not sections:
                raise HTTPException(status_code=400, detail="Survey must contain at least one section")
            
            # Validate sections have questions
            total_questions = 0
            for i, section in enumerate(sections):
                questions = section.get("questions", [])
                total_questions += len(questions)
                logger.info(f"Export validation: Section {i+1} has {len(questions)} questions")
            
            logger.info(f"Export validation: Total questions: {total_questions}")
            
            if total_questions == 0:
                raise HTTPException(status_code=400, detail="Survey must contain at least one question across all sections")
                
        else:
            # Legacy format - validate questions directly
            questions = request.survey_data.get("questions", [])
            if not questions:
                raise HTTPException(status_code=400, detail="Survey must contain at least one question")

            # Validate question types
            for i, question in enumerate(questions):
                if "type" not in question:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Question {i + 1} is missing 'type' field"
                    )
                if "text" not in question:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Question {i + 1} is missing 'text' field"
                    )

        # Generate export
        if "sections" in request.survey_data:
            total_questions = sum(len(section.get("questions", [])) for section in request.survey_data.get("sections", []))
            logger.info(f"Exporting survey with {len(request.survey_data.get('sections', []))} sections and {total_questions} questions to {request.format} format")
        else:
            questions = request.survey_data.get("questions", [])
            logger.info(f"Exporting survey with {len(questions)} questions to {request.format} format")

        exported_data = renderer.render_survey(request.survey_data)

        # Determine filename
        if request.filename:
            filename = request.filename
            if not filename.endswith(f".{request.format}"):
                filename += f".{request.format}"
        else:
            survey_title = request.survey_data.get("title", "survey")
            # Clean filename
            clean_title = "".join(c for c in survey_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{clean_title.replace(' ', '_')}.{request.format}"

        # Set appropriate content type
        content_type_map = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        content_type = content_type_map.get(request.format, "application/octet-stream")

        logger.info(f"Successfully exported survey as {filename} ({len(exported_data)} bytes)")

        return Response(
            content=exported_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(exported_data))
            }
        )

    except ValueError as e:
        logger.error(f"Validation error during export: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting survey: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/validate")
async def validate_survey_for_export(survey_data: Dict[str, Any]):
    """
    Validate that a survey can be exported.

    Args:
        survey_data: Survey data to validate

    Returns:
        Validation result with any issues found
    """
    try:
        issues = []

        # Check basic structure
        if not survey_data:
            issues.append("Survey data is empty")
            return {"valid": False, "issues": issues}

        questions = survey_data.get("questions", [])
        if not questions:
            issues.append("Survey must contain at least one question")

        # Validate each question
        for i, question in enumerate(questions):
            question_num = i + 1

            if "type" not in question:
                issues.append(f"Question {question_num}: Missing 'type' field")
            elif question["type"] not in [qt.value for qt in export_registry._renderers["docx"]()._registered_types]:
                issues.append(f"Question {question_num}: Unknown question type '{question['type']}'")

            if "text" not in question or not question["text"].strip():
                issues.append(f"Question {question_num}: Missing or empty 'text' field")

        # Try to create a renderer to validate type coverage
        try:
            renderer = export_registry.get_renderer("docx")
        except Exception as e:
            issues.append(f"Renderer validation failed: {str(e)}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "question_count": len(questions)
        }

    except Exception as e:
        logger.error(f"Error validating survey: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")