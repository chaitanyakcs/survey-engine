from fastapi import APIRouter, HTTPException, File, UploadFile
from src.services.document_parser import document_parser
from src.utils.error_messages import UserFriendlyError, create_error_response
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["Utilities"])


class TextExtractionResponse(BaseModel):
    extracted_text: str
    confidence_score: Optional[float] = 1.0


@router.post("/extract-text", response_model=TextExtractionResponse)
async def extract_text(
    file: UploadFile = File(...),
):
    """
    Extract plain text from a DOCX document.
    Returns the extracted text for use in any text field.
    """
    logger.info(f"📄 [Text Extract] Starting text extraction for file: {file.filename}")
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.docx'):
        logger.warning(f"❌ [Text Extract] Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400, 
            detail="Only DOCX files are supported"
        )
    
    try:
        logger.info(f"📖 [Text Extract] Reading file content for: {file.filename}")
        # Read file content
        file_content = await file.read()
        logger.info(f"✅ [Text Extract] File read successfully, size: {len(file_content)} bytes")
        
        logger.info(f"📝 [Text Extract] Extracting text from: {file.filename}")
        # Extract text only
        extracted_text = document_parser.extract_text_from_docx(file_content)
        logger.info(f"✅ [Text Extract] Text extraction completed, length: {len(extracted_text)} chars")
        
        response = TextExtractionResponse(
            extracted_text=extracted_text,
            confidence_score=1.0  # High confidence for simple text extraction
        )
        
        logger.info(f"🎉 [Text Extract] Successfully extracted text from: {file.filename}")
        return response
        
    except UserFriendlyError as e:
        logger.error(f"❌ [Text Extract] User-friendly error for {file.filename}: {str(e)}")
        error_response = create_error_response(e, f"text extraction from {file.filename}")
        raise HTTPException(status_code=422, detail=error_response)
    except Exception as e:
        logger.error(f"❌ [Text Extract] Unexpected error extracting text from {file.filename}: {str(e)}", exc_info=True)
        error_response = create_error_response(e, f"text extraction from {file.filename}")
        raise HTTPException(status_code=500, detail=error_response)
