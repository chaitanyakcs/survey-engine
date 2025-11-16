from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session
from src.database import get_db, RFQ, Survey
from src.api.dependencies import require_models_ready
from src.models.enhanced_rfq import (
    EnhancedRFQRequest,
    EnhancedRFQResponse,
    validate_enhanced_rfq,
    extract_legacy_fields,
    count_populated_fields,
    normalize_enum_values
)
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import uuid4, UUID
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rfq", tags=["RFQ"])


class RFQSubmissionRequest(BaseModel):
    title: Optional[str] = None
    description: str
    product_category: Optional[str] = None
    target_segment: Optional[str] = None
    research_goal: Optional[str] = None
    enhanced_rfq_data: Optional[dict] = None  # Optional structured Enhanced RFQ data
    custom_prompt: Optional[str] = None  # Custom edited prompt for survey generation
    rfq_id: Optional[str] = None  # Optional: Reuse existing draft RFQ (preserves concept files)


class RFQSubmissionResponse(BaseModel):
    workflow_id: str
    survey_id: str
    status: str
    rfq_id: Optional[str] = None  # Return RFQ ID (reused or newly created)


class DocumentAnalysisRequest(BaseModel):
    filename: str
    content_type: str


class DocumentAnalysisResponse(BaseModel):
    document_content: Dict[str, Any]
    rfq_analysis: Dict[str, Any]
    processing_status: str
    errors: list


class PromptPreviewRequest(BaseModel):
    rfq_id: Optional[str] = None  # RFQ identifier for tracking and caching
    title: Optional[str] = None
    description: str
    product_category: Optional[str] = None
    target_segment: Optional[str] = None
    research_goal: Optional[str] = None
    enhanced_rfq_data: Optional[dict] = None  # Optional structured Enhanced RFQ data


class PromptPreviewResponse(BaseModel):
    rfq_id: Optional[str] = None
    prompt: str
    prompt_length: int
    context_info: Dict[str, Any]
    methodology_tags: List[str]
    golden_examples_count: int
    methodology_blocks_count: int
    enhanced_rfq_used: bool
    reference_examples: Optional[Dict[str, Any]] = None  # Reference examples that will be used


@router.post("/", response_model=RFQSubmissionResponse)
async def submit_rfq(
    request: RFQSubmissionRequest,
    db: Session = Depends(get_db)
) -> RFQSubmissionResponse:
    """
    Submit new RFQ for survey generation
    Returns: workflow_id, survey_id, status (async processing)
    
    WARNING: This endpoint ALWAYS starts survey generation.
    Use /api/v1/rfq/enhanced/draft for saving without generation.
    """
    logger.info(f"🚀 [RFQ API] Received RFQ submission: title='{request.title}', description_length={len(request.description)}, product_category='{request.product_category}'")
    logger.info(f"🔍 [RFQ API] Request rfq_id: {request.rfq_id}")
    logger.warning(f"⚠️ [RFQ API] Starting survey generation workflow - this will generate a survey immediately")
    
    try:
        # Generate unique IDs
        workflow_id = f"survey-gen-{str(uuid4())}"
        survey_id = f"survey-{str(uuid4())}"
        
        logger.info(f"📋 [RFQ API] Generated workflow_id={workflow_id}, survey_id={survey_id}")
        
        # Check if we should reuse an existing draft RFQ (to preserve concept files)
        rfq = None
        if request.rfq_id:
            logger.info(f"🔍 [RFQ API] Attempting to reuse existing RFQ: {request.rfq_id}")
            try:
                rfq_uuid = UUID(request.rfq_id)
                rfq = db.query(RFQ).filter(RFQ.id == rfq_uuid).first()
                if rfq:
                    logger.info(f"♻️ [RFQ API] Reusing existing draft RFQ: {rfq.id} (preserves concept files)")
                    # Update the existing RFQ with new data
                    rfq.title = request.title or rfq.title
                    rfq.description = request.description
                    rfq.product_category = request.product_category or rfq.product_category
                    rfq.target_segment = request.target_segment or rfq.target_segment
                    rfq.research_goal = request.research_goal or rfq.research_goal
                    if request.enhanced_rfq_data:
                        # Merge enhanced_rfq_data if provided
                        existing_data = rfq.enhanced_rfq_data or {}
                        existing_data.update(request.enhanced_rfq_data)
                        rfq.enhanced_rfq_data = existing_data
                    db.commit()
                    db.refresh(rfq)
                    logger.info(f"✅ [RFQ API] Updated existing RFQ: {rfq.id}")
                else:
                    logger.warning(f"⚠️ [RFQ API] Requested RFQ ID {request.rfq_id} not found, creating new RFQ")
            except (ValueError, Exception) as e:
                logger.warning(f"⚠️ [RFQ API] Invalid RFQ ID {request.rfq_id}: {str(e)}, creating new RFQ")
        
        # Create new RFQ record if not reusing existing one
        if not rfq:
            logger.info("💾 [RFQ API] Creating new RFQ database record")

            # Check if this is an enhanced RFQ submission
            is_enhanced_rfq = request.enhanced_rfq_data is not None
            if is_enhanced_rfq:
                logger.info(f"🎯 [RFQ API] Enhanced RFQ detected with structured data: objectives={len(request.enhanced_rfq_data.get('objectives', []))}, constraints={len(request.enhanced_rfq_data.get('constraints', []))}")
                
                # Extract unmapped_context if present in enhanced_rfq_data
                unmapped_context = request.enhanced_rfq_data.get('unmapped_context', '')
                if unmapped_context:
                    logger.info(f"📝 [RFQ API] Found unmapped_context: {len(unmapped_context)} characters")
                    # Store unmapped_context in enhanced_rfq_data for survey generation
                    request.enhanced_rfq_data['unmapped_context'] = unmapped_context

            rfq = RFQ(
                title=request.title,
                description=request.description,
                product_category=request.product_category,
                target_segment=request.target_segment,
                research_goal=request.research_goal,
                enhanced_rfq_data=request.enhanced_rfq_data  # Store structured data for analytics
            )
            db.add(rfq)
            db.commit()
            db.refresh(rfq)
            logger.info(f"✅ [RFQ API] RFQ record created with ID: {rfq.id}")
        
        # Create initial survey record
        logger.info("💾 [RFQ API] Creating initial Survey database record")
        # Choose model version from evaluation settings (DB), fallback to app settings
        try:
            from src.services.settings_service import SettingsService
            settings_service = SettingsService(db)
            eval_settings = settings_service.get_evaluation_settings()
            model_version_value = eval_settings.get('generation_model')
        except Exception:
            model_version_value = None
        if not model_version_value:
            from src.config.settings import settings as app_settings
            model_version_value = app_settings.generation_model

        survey = Survey(
            rfq_id=rfq.id,
            status="draft",
            model_version=model_version_value
        )
        db.add(survey)
        db.commit()
        db.refresh(survey)
        logger.info(f"✅ [RFQ API] Survey record created with ID: {survey.id}")
        
        # Process RFQ directly through workflow (consolidated approach)
        logger.info(f"🔄 [RFQ API] Starting direct workflow processing: workflow_id={workflow_id}")
        
        try:
            from src.services.workflow_service import WorkflowService
            from src.main import manager  # Import the connection manager
            
            # Initialize workflow service with connection manager
            workflow_service = WorkflowService(db, manager)
            
            # Extract custom prompt if provided
            custom_prompt = request.custom_prompt if hasattr(request, 'custom_prompt') else None
            if custom_prompt:
                logger.info(f"🎨 [RFQ API] Custom prompt detected in basic RFQ: {len(custom_prompt)} chars")
            
            # Start workflow processing in background with a small delay to ensure WebSocket connection
            asyncio.create_task(process_rfq_workflow_async(
                workflow_service=workflow_service,
                title=request.title,
                description=request.description,
                product_category=request.product_category,
                target_segment=request.target_segment,
                research_goal=request.research_goal,
                workflow_id=workflow_id,
                survey_id=str(survey.id),
                custom_prompt=custom_prompt
            ))
            
            logger.info(f"✅ [RFQ API] Workflow processing started in background: workflow_id={workflow_id}")
            
        except Exception as e:
            logger.error(f"❌ [RFQ API] Failed to start workflow processing: {str(e)}")
            # Mark survey as pending if workflow fails to start
            survey.status = "draft"
            db.commit()
        
        # Return immediate response
        response = RFQSubmissionResponse(
            workflow_id=workflow_id,
            survey_id=str(survey.id),
            status="draft",
            rfq_id=str(rfq.id)  # Include RFQ ID (reused or newly created)
        )
        
        logger.info(f"🎉 [RFQ API] Returning async response: {response.model_dump()}")
        logger.info(f"🔍 [RFQ API] RFQ ID in response: {response.rfq_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ [RFQ API] Failed to process RFQ: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process RFQ: {str(e)}")


async def process_rfq_workflow_async(
    workflow_service,
    title: str,
    description: str,
    product_category: str,
    target_segment: str,
    research_goal: str,
    workflow_id: str,
    survey_id: str,
    custom_prompt: Optional[str] = None
):
    """
    Process RFQ workflow asynchronously with detailed logging
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🚀 [Async Workflow] Starting RFQ processing: title='{title}', workflow_id={workflow_id}")
        
        # Add a small delay to ensure WebSocket connection is established
        logger.info("⏳ [Async Workflow] Waiting 2 seconds for WebSocket connection to establish...")
        await asyncio.sleep(2)
        
        # Process through workflow with detailed logging
        result = await workflow_service.process_rfq(
            title=title,
            description=description,
            product_category=product_category,
            target_segment=target_segment,
            research_goal=research_goal,
            workflow_id=workflow_id,
            survey_id=survey_id,
            custom_prompt=custom_prompt
        )
        
        logger.info(f"✅ [Async Workflow] Workflow completed successfully: {result.status}")

    except Exception as e:
        logger.error(f"❌ [Async Workflow] Workflow failed: {str(e)}", exc_info=True)


@router.post("/upload-document", response_model=DocumentAnalysisResponse)
async def upload_and_analyze_document(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    db: Session = Depends(get_db)
) -> DocumentAnalysisResponse:
    """
    Upload and analyze a DOCX document for RFQ data extraction
    Returns: document content, RFQ analysis, and field mappings
    """
    logger.info(f"📄 [RFQ API] Received document upload: filename='{file.filename}', content_type='{file.content_type}'")

    # Create DocumentUpload record immediately to track processing status
    from src.database.models import DocumentUpload
    
    document_upload = DocumentUpload(
        filename=file.filename or "document.docx",
        original_filename=file.filename or "document.docx",
        file_size=0,  # Will update after reading
        content_type=file.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        session_id=session_id,
        processing_status="pending",
        uploaded_by=None  # Could add user tracking later
    )
    db.add(document_upload)
    db.commit()
    db.refresh(document_upload)
    
    logger.info(f"✅ [RFQ API] Created DocumentUpload record with ID: {document_upload.id}, session_id: {session_id}")

    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.docx'):
            # Update status to failed
            document_upload.processing_status = "failed"
            document_upload.error_message = "Only DOCX files are supported"
            db.commit()
            
            raise HTTPException(
                status_code=400,
                detail="Only DOCX files are supported. Please upload a Microsoft Word document."
            )

        if file.content_type and not file.content_type.startswith('application/'):
            logger.warning(f"⚠️ [RFQ API] Unexpected content type: {file.content_type}")

        # Read file content
        logger.info(f"📖 [RFQ API] Reading file content")
        file_content = await file.read()

        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            # Update status to failed
            document_upload.processing_status = "failed"
            document_upload.error_message = "File too large. Maximum size is 10MB"
            db.commit()
            
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

        logger.info(f"✅ [RFQ API] File read successfully, size: {len(file_content)} bytes")
        
        # Update file size and status to processing
        document_upload.file_size = len(file_content)
        document_upload.processing_status = "processing"
        db.commit()

        # Parse document using enhanced document parser
        logger.info(f"🤖 [RFQ API] Starting document analysis")
        from src.services.document_parser import DocumentParser
        from src.api.field_extraction import rfq_parsing_manager

        # Create document parser with database session and WebSocket manager for real-time progress
        document_parser = DocumentParser(db_session=db, rfq_parsing_manager=rfq_parsing_manager)

        analysis_result = await document_parser.parse_document_for_rfq(
            docx_content=file_content,
            filename=file.filename,
            session_id=session_id
        )

        logger.info(f"✅ [RFQ API] Document analysis completed")
        logger.info(f"📊 [RFQ API] Analysis confidence: {analysis_result.get('rfq_analysis', {}).get('confidence', 0)}")
        logger.info(f"📊 [RFQ API] Field mappings: {len(analysis_result.get('rfq_analysis', {}).get('field_mappings', []))}")

        # Update DocumentUpload record to completed
        document_upload.processing_status = "completed"
        document_upload.analysis_result = analysis_result
        db.commit()
        
        logger.info(f"✅ [RFQ API] Updated DocumentUpload record to completed status")

        # Create response
        response = DocumentAnalysisResponse(
            document_content=analysis_result.get("document_content", {}),
            rfq_analysis=analysis_result.get("rfq_analysis", {}),
            processing_status=analysis_result.get("processing_status", "completed"),
            errors=analysis_result.get("errors", [])
        )

        logger.info(f"🎉 [RFQ API] Document upload and analysis completed successfully")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [RFQ API] Failed to process document upload: {str(e)}", exc_info=True)

        # Determine specific error type for better user feedback
        error_message = "Document processing failed"
        if "REPLICATE_API_TOKEN" in str(e):
            error_message = "AI service not configured. Please contact support."
        elif "timeout" in str(e).lower():
            error_message = "Document processing timed out. Please try again or use a smaller document."
        elif "connection" in str(e).lower():
            error_message = "Network error. Please check your connection and try again."
        elif "json" in str(e).lower():
            error_message = "AI service returned invalid response. Please try again."
        else:
            error_message = f"Processing error: {str(e)}"
        
        # Update DocumentUpload record to failed
        document_upload.processing_status = "failed"
        document_upload.error_message = error_message
        db.commit()
        
        logger.info(f"✅ [RFQ API] Updated DocumentUpload record to failed status")

        # Return error response instead of throwing exception
        error_response = DocumentAnalysisResponse(
            document_content={
                "filename": file.filename or "unknown",
                "error": "Failed to process document",
                "word_count": 0,
                "extraction_timestamp": "2024-01-01T00:00:00Z"
            },
            rfq_analysis={
                "confidence": 0.0,
                "identified_sections": {},
                "extracted_entities": {
                    "stakeholders": [],
                    "industries": [],
                    "research_types": [],
                    "methodologies": []
                },
                "field_mappings": [],
                "processing_error": error_message
            },
            processing_status="error",
            errors=[error_message]
        )

        return error_response


@router.get("/status/{session_id}", response_model=Dict[str, Any])
async def get_document_processing_status(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the current processing status for a document upload session.
    Returns: current status, progress, and any results if completed.
    """
    logger.info(f"📊 [RFQ API] Checking processing status for session_id={session_id}")
    
    try:
        # Check if we have any active WebSocket connections for this session
        from src.api.field_extraction import rfq_parsing_manager
        
        has_active_connections = session_id in rfq_parsing_manager.active_connections
        logger.info(f"🔍 [RFQ API] Active WebSocket connections for session_id={session_id}: {has_active_connections}")
        
        # Query database for document upload record by session_id
        from src.database.models import DocumentUpload
        
        document_upload = db.query(DocumentUpload).filter(
            DocumentUpload.session_id == session_id
        ).order_by(DocumentUpload.created_at.desc()).first()
        
        if document_upload:
            logger.info(f"📄 [RFQ API] Found document upload record for session_id={session_id}: status={document_upload.processing_status}")
            
            # Return status based on database record
            if document_upload.processing_status == 'completed':
                return {
                    "status": "completed",
                    "session_id": session_id,
                    "processing_status": document_upload.processing_status,
                    "has_results": document_upload.analysis_result is not None,
                    "timestamp": document_upload.updated_at.isoformat() if document_upload.updated_at else None,
                    "message": "Document processing completed successfully"
                }
            elif document_upload.processing_status == 'cancelled':
                return {
                    "status": "cancelled",
                    "session_id": session_id,
                    "processing_status": document_upload.processing_status,
                    "error_message": document_upload.error_message,
                    "timestamp": document_upload.updated_at.isoformat() if document_upload.updated_at else None,
                    "message": "Document processing cancelled by user"
                }
            elif document_upload.processing_status == 'failed':
                return {
                    "status": "failed",
                    "session_id": session_id,
                    "processing_status": document_upload.processing_status,
                    "error_message": document_upload.error_message,
                    "timestamp": document_upload.updated_at.isoformat() if document_upload.updated_at else None,
                    "message": "Document processing failed"
                }
            elif document_upload.processing_status in ['pending', 'processing']:
                return {
                    "status": "in_progress",
                    "session_id": session_id,
                    "processing_status": document_upload.processing_status,
                    "has_active_connections": has_active_connections,
                    "timestamp": document_upload.updated_at.isoformat() if document_upload.updated_at else None,
                    "message": "Document processing in progress"
                }
        
        # If no database record found, check if there are active WebSocket connections
        if has_active_connections:
            logger.info(f"⏳ [RFQ API] No database record but active WebSocket connections found")
            return {
                "status": "in_progress",
                "session_id": session_id,
                "processing_status": "processing",
                "has_active_connections": True,
                "message": "Document processing in progress (WebSocket active)"
            }
        
        # No active processing found
        logger.info(f"❌ [RFQ API] No active processing found for session_id={session_id}")
        return {
            "status": "not_found",
            "session_id": session_id,
            "message": "No active document processing found for this session"
        }
        
    except Exception as e:
        logger.error(f"❌ [RFQ API] Error checking processing status for session_id={session_id}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "session_id": session_id,
            "error": str(e),
            "message": "Error checking processing status"
        }


@router.post("/cancel/{session_id}")
async def cancel_document_processing(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel document processing for a given session.
    This will stop any ongoing processing and clean up resources.
    """
    logger.info(f"🛑 [RFQ API] Cancelling document processing for session_id={session_id}")
    
    try:
        # Update database record to cancelled status
        from src.database.models import DocumentUpload
        
        document_upload = db.query(DocumentUpload).filter(
            DocumentUpload.session_id == session_id
        ).order_by(DocumentUpload.created_at.desc()).first()
        
        if document_upload:
            document_upload.processing_status = 'cancelled'
            document_upload.error_message = 'Processing cancelled by user'
            db.commit()
            logger.info(f"✅ [RFQ API] Marked document upload as cancelled for session_id={session_id}")
        
        # Disconnect any active WebSocket connections
        from src.api.field_extraction import rfq_parsing_manager
        
        if session_id in rfq_parsing_manager.active_connections:
            logger.info(f"🔌 [RFQ API] Disconnecting WebSocket for cancelled session_id={session_id}")
            # Close all WebSocket connections for this session
            connections = rfq_parsing_manager.active_connections[session_id].copy()
            for websocket in connections:
                try:
                    await websocket.close()
                except Exception as e:
                    logger.warning(f"⚠️ [RFQ API] Error closing WebSocket: {e}")
            rfq_parsing_manager.disconnect_all(session_id)
        
        return {
            "status": "cancelled",
            "session_id": session_id,
            "message": "Document processing cancelled successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ [RFQ API] Error cancelling processing for session_id={session_id}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "session_id": session_id,
            "error": str(e),
            "message": "Failed to cancel document processing"
        }


@router.get("/status/{session_id}/results", response_model=DocumentAnalysisResponse)
async def get_document_analysis_results(
    session_id: str,
    db: Session = Depends(get_db)
) -> DocumentAnalysisResponse:
    """
    Get the completed analysis results for a document upload session.
    Returns: document content, RFQ analysis, and field mappings if processing is completed.
    """
    logger.info(f"📊 [RFQ API] Getting analysis results for session_id={session_id}")
    
    try:
        # Query database for document upload record by session_id
        from src.database.models import DocumentUpload
        
        document_upload = db.query(DocumentUpload).filter(
            DocumentUpload.session_id == session_id
        ).order_by(DocumentUpload.created_at.desc()).first()
        
        if not document_upload:
            logger.warning(f"❌ [RFQ API] No document upload record found for session_id={session_id}")
            raise HTTPException(
                status_code=404,
                detail="No document processing found for this session"
            )
        
        if document_upload.processing_status != 'completed':
            logger.warning(f"⚠️ [RFQ API] Document processing not completed for session_id={session_id}, status={document_upload.processing_status}")
            raise HTTPException(
                status_code=400,
                detail=f"Document processing not completed. Current status: {document_upload.processing_status}"
            )
        
        if not document_upload.analysis_result:
            logger.warning(f"⚠️ [RFQ API] No analysis results available for session_id={session_id}")
            raise HTTPException(
                status_code=404,
                detail="Analysis results not available"
            )
        
        logger.info(f"✅ [RFQ API] Returning analysis results for session_id={session_id}")
        
        # Create response from stored analysis result
        response = DocumentAnalysisResponse(
            document_content=document_upload.analysis_result.get("document_content", {}),
            rfq_analysis=document_upload.analysis_result.get("rfq_analysis", {}),
            processing_status="completed",
            errors=document_upload.analysis_result.get("errors", [])
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [RFQ API] Error getting analysis results for session_id={session_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error retrieving analysis results"
        )


@router.post("/enhanced/draft", response_model=EnhancedRFQResponse)
async def save_enhanced_rfq_draft(
    request: Dict[str, Any] = Body(...),  # Accept raw JSON body
    db: Session = Depends(get_db)
) -> EnhancedRFQResponse:
    """
    Save Enhanced RFQ as draft without starting survey generation.
    This allows users to save their RFQ and upload concept files before generating the survey.
    Returns: rfq_id, survey_id, status (draft)
    
    CRITICAL: This endpoint does NOT start survey generation.
    Use /api/v1/rfq/ to start generation.
    """
    logger.info(f"💾 [Enhanced RFQ Draft API] Saving Enhanced RFQ as draft (NO generation will be started)")
    logger.info(f"💾 [Enhanced RFQ Draft API] Request data keys: {list(request.keys())}")
    logger.info(f"💾 [Enhanced RFQ Draft API] Request data: {request}")

    try:
        # Normalize enum values before validation
        normalized_request = normalize_enum_values(request)
        
        # Convert dict to EnhancedRFQRequest with extra fields allowed
        try:
            validated_rfq = EnhancedRFQRequest(**normalized_request)
        except Exception as validation_error:
            logger.error(f"❌ [Enhanced RFQ Draft API] Validation error: {str(validation_error)}")
            logger.error(f"❌ [Enhanced RFQ Draft API] Request keys: {list(request.keys())}")
            # For drafts, be more lenient - convert enum fields to strings
            normalized_request = request.copy()
            if 'advanced_classification' in normalized_request and normalized_request['advanced_classification']:
                ac = normalized_request['advanced_classification']
                if isinstance(ac, dict):
                    # Convert enum fields to strings if they're not valid enum values
                    if 'industry_classification' in ac and not isinstance(ac['industry_classification'], str):
                        ac['industry_classification'] = str(ac['industry_classification'])
                    if 'respondent_classification' in ac and not isinstance(ac['respondent_classification'], str):
                        ac['respondent_classification'] = str(ac['respondent_classification'])
            validated_rfq = EnhancedRFQRequest(**normalized_request)
        
        field_count = count_populated_fields(validated_rfq)

        logger.info(f"✅ [Enhanced RFQ Draft API] Validation successful, populated fields: {field_count}")

        # Extract legacy fields for backward compatibility
        legacy_fields = extract_legacy_fields(validated_rfq)

        # Extract unmapped_context if present (from normalized_request, not validated_rfq)
        normalized_request_dict = normalized_request if isinstance(normalized_request, dict) else normalized_request.model_dump()
        unmapped_context = normalized_request_dict.get('unmapped_context', '') or normalized_request_dict.get('additional_info', '')
        
        if unmapped_context:
            logger.info(f"📝 [Enhanced RFQ Draft API] Found unmapped_context: {len(unmapped_context)} characters")
        
        # Ensure unmapped_context is included in the stored enhanced_rfq_data
        validated_rfq_dict = validated_rfq.model_dump()
        if unmapped_context:
            validated_rfq_dict['unmapped_context'] = unmapped_context

        # Check if we should update an existing RFQ or create a new one
        # CRITICAL: Preserve RFQ ID to maintain concept file associations
        rfq_id_from_request = normalized_request_dict.get('rfq_id')
        existing_rfq = None
        
        if rfq_id_from_request:
            try:
                rfq_uuid = UUID(rfq_id_from_request)
                existing_rfq = db.query(RFQ).filter(RFQ.id == rfq_uuid).first()
                if existing_rfq:
                    logger.info(f"♻️ [Enhanced RFQ Draft API] Updating existing RFQ: {existing_rfq.id} (preserves concept files)")
                else:
                    logger.warning(f"⚠️ [Enhanced RFQ Draft API] Requested RFQ ID {rfq_id_from_request} not found, creating new RFQ")
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ [Enhanced RFQ Draft API] Invalid RFQ ID {rfq_id_from_request}: {str(e)}, creating new RFQ")

        # Create RFQ record with enhanced data
        if existing_rfq:
            logger.info("💾 [Enhanced RFQ Draft API] Updating existing Enhanced RFQ database record")
        else:
            logger.info("💾 [Enhanced RFQ Draft API] Creating new Enhanced RFQ database record")

        # Extract document_upload_id from document_source if present
        document_upload_id = None
        doc_source = validated_rfq_dict.get('document_source')
        if doc_source and doc_source.get('type') == 'upload':
            from src.database.models import DocumentUpload
            upload_id = doc_source.get('upload_id')
            filename = doc_source.get('filename')
            
            if upload_id:
                # Check if upload_id is a valid UUID
                try:
                    UUID(str(upload_id))
                    # It's a valid UUID, query by id only
                    document_upload = db.query(DocumentUpload).filter(
                        DocumentUpload.id == upload_id
                    ).first()
                    if document_upload:
                        document_upload_id = document_upload.id
                        logger.info(f"🔍 [Enhanced RFQ Draft API] Found document upload by UUID: {upload_id}")
                except (ValueError, TypeError):
                    # Not a valid UUID, treat as filename
                    document_upload = db.query(DocumentUpload).filter(
                        DocumentUpload.filename == str(upload_id)
                    ).order_by(DocumentUpload.created_at.desc()).first()
                    if document_upload:
                        document_upload_id = document_upload.id
                        logger.info(f"🔍 [Enhanced RFQ Draft API] Found document upload by filename (from upload_id): {upload_id}")
            elif filename:
                document_upload = db.query(DocumentUpload).filter(
                    DocumentUpload.filename == filename
                ).order_by(DocumentUpload.created_at.desc()).first()
                if document_upload:
                    document_upload_id = document_upload.id
                    logger.info(f"🔍 [Enhanced RFQ Draft API] Found document upload by filename: {filename}")
        
        if existing_rfq:
            # Update existing RFQ (preserves RFQ ID and concept files)
            existing_rfq.title = legacy_fields.get("title") or existing_rfq.title
            existing_rfq.description = legacy_fields.get("description") or existing_rfq.description
            existing_rfq.product_category = legacy_fields.get("product_category") or existing_rfq.product_category
            existing_rfq.target_segment = legacy_fields.get("target_segment") or existing_rfq.target_segment
            existing_rfq.research_goal = legacy_fields.get("research_goal") or existing_rfq.research_goal
            existing_rfq.enhanced_rfq_data = validated_rfq_dict
            if document_upload_id:
                existing_rfq.document_upload_id = document_upload_id
            db.commit()
            db.refresh(existing_rfq)
            rfq = existing_rfq
            logger.info(f"✅ [Enhanced RFQ Draft API] Enhanced RFQ record updated: {rfq.id} (concept files preserved)")
        else:
            # Create new RFQ
            rfq = RFQ(
                title=legacy_fields.get("title") or "",
                description=legacy_fields.get("description") or "",
                product_category=legacy_fields.get("product_category"),
                target_segment=legacy_fields.get("target_segment"),
                research_goal=legacy_fields.get("research_goal"),
                enhanced_rfq_data=validated_rfq_dict,
                document_upload_id=document_upload_id
            )
            db.add(rfq)
            db.commit()
            db.refresh(rfq)
            logger.info(f"✅ [Enhanced RFQ Draft API] Enhanced RFQ record created with ID: {rfq.id}")

        # CRITICAL: Do NOT create a Survey record for draft saves
        # Survey records should only be created when generation actually starts
        # This prevents empty draft surveys from appearing in the survey listing
        logger.info(f"🔒 [Enhanced RFQ Draft API] NOT creating Survey record - surveys only created when generation starts")
        
        # Return draft response (NO workflow, NO survey created)
        response = EnhancedRFQResponse(
            rfq_id=str(rfq.id),
            workflow_id=None,  # No workflow for draft - CRITICAL: Must be None
            survey_id=None,  # No survey created for draft - CRITICAL: Must be None
            status="draft",
            enhanced_data_processed=True,
            field_count=field_count
        )

        # Final verification that we're not starting generation or creating surveys
        if response.workflow_id is not None:
            logger.error(f"❌ [Enhanced RFQ Draft API] CRITICAL ERROR: Draft endpoint returned workflow_id={response.workflow_id} - this should NEVER happen!")
            raise ValueError("Draft endpoint must not return a workflow_id - generation should not be started")
        
        if response.survey_id is not None:
            logger.error(f"❌ [Enhanced RFQ Draft API] CRITICAL ERROR: Draft endpoint returned survey_id={response.survey_id} - this should NEVER happen!")
            raise ValueError("Draft endpoint must not return a survey_id - surveys should not be created for drafts")
        
        logger.info(f"🎉 [Enhanced RFQ Draft API] Draft saved successfully: rfq_id={rfq.id}, survey_id=None, workflow_id=None (no survey created, no generation)")
        return response

    except Exception as e:
        logger.error(f"❌ [Enhanced RFQ Draft API] Failed to save draft: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save RFQ draft: {str(e)}")


@router.post("/enhanced", response_model=EnhancedRFQResponse)
async def submit_enhanced_rfq(
    request: EnhancedRFQRequest,
    db: Session = Depends(get_db)
) -> EnhancedRFQResponse:
    """
    Submit Enhanced RFQ with structured data for survey generation
    Returns: rfq_id, workflow_id, survey_id, status, enhanced data metrics
    """
    logger.info(f"🚀 [Enhanced RFQ API] Received Enhanced RFQ submission: title='{request.title}', description_length={len(request.description)}")

    try:
        # Validate the enhanced RFQ data
        validated_rfq = validate_enhanced_rfq(request.model_dump())
        field_count = count_populated_fields(validated_rfq)

        logger.info(f"✅ [Enhanced RFQ API] Validation successful, populated fields: {field_count}")

            # Extract legacy fields for backward compatibility
        legacy_fields = extract_legacy_fields(validated_rfq)

        # Extract unmapped_context and custom_prompt if present in validated_rfq
        request_dict = request.model_dump()
        unmapped_context = request_dict.get('unmapped_context', '')
        custom_prompt = request_dict.get('custom_prompt')
        
        if unmapped_context:
            logger.info(f"📝 [Enhanced RFQ API] Found unmapped_context: {len(unmapped_context)} characters")
            
        if custom_prompt:
            logger.info(f"🎨 [Enhanced RFQ API] Custom prompt detected in request: {len(custom_prompt)} chars")
        
        # Ensure unmapped_context is included in the stored enhanced_rfq_data
        validated_rfq_dict = validated_rfq.model_dump()
        if unmapped_context:
            validated_rfq_dict['unmapped_context'] = unmapped_context

        # Generate unique IDs
        workflow_id = f"enhanced-survey-gen-{str(uuid4())}"
        survey_id = f"enhanced-survey-{str(uuid4())}"

        logger.info(f"📋 [Enhanced RFQ API] Generated workflow_id={workflow_id}, survey_id={survey_id}")

        # Check if we should update an existing RFQ or create a new one
        # CRITICAL: Preserve RFQ ID to maintain concept file associations
        rfq_id_from_request = validated_rfq_dict.get('rfq_id')
        existing_rfq = None
        
        if rfq_id_from_request:
            try:
                rfq_uuid = UUID(rfq_id_from_request)
                existing_rfq = db.query(RFQ).filter(RFQ.id == rfq_uuid).first()
                if existing_rfq:
                    logger.info(f"♻️ [Enhanced RFQ API] Updating existing RFQ: {existing_rfq.id} (preserves concept files)")
                else:
                    logger.warning(f"⚠️ [Enhanced RFQ API] Requested RFQ ID {rfq_id_from_request} not found, creating new RFQ")
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ [Enhanced RFQ API] Invalid RFQ ID {rfq_id_from_request}: {str(e)}, creating new RFQ")

        # Create RFQ record with enhanced data
        if existing_rfq:
            logger.info("💾 [Enhanced RFQ API] Updating existing Enhanced RFQ database record")
        else:
            logger.info("💾 [Enhanced RFQ API] Creating new Enhanced RFQ database record")

        # Extract document_upload_id from document_source if present
        document_upload_id = None
        doc_source = validated_rfq_dict.get('document_source')
        if doc_source and doc_source.get('type') == 'upload':
            # Try to find the document upload record by filename or upload_id
            from src.database.models import DocumentUpload
            upload_id = doc_source.get('upload_id')
            filename = doc_source.get('filename')
            
            if upload_id:
                # Try to find by upload_id (could be document_uploads.id UUID or filename)
                document_upload = db.query(DocumentUpload).filter(
                    (DocumentUpload.id == upload_id) | (DocumentUpload.filename == upload_id)
                ).first()
                if document_upload:
                    document_upload_id = document_upload.id
                    logger.info(f"🔍 [Enhanced RFQ API] Found document upload by upload_id: {upload_id}")
            elif filename:
                # Try to find by filename
                document_upload = db.query(DocumentUpload).filter(
                    DocumentUpload.filename == filename
                ).order_by(DocumentUpload.created_at.desc()).first()
                if document_upload:
                    document_upload_id = document_upload.id
                    logger.info(f"🔍 [Enhanced RFQ API] Found document upload by filename: {filename}")
        
        if existing_rfq:
            # Update existing RFQ (preserves RFQ ID and concept files)
            existing_rfq.title = legacy_fields["title"]
            existing_rfq.description = legacy_fields["description"]
            existing_rfq.product_category = legacy_fields["product_category"]
            existing_rfq.target_segment = legacy_fields["target_segment"]
            existing_rfq.research_goal = legacy_fields["research_goal"]
            existing_rfq.enhanced_rfq_data = validated_rfq_dict
            if document_upload_id:
                existing_rfq.document_upload_id = document_upload_id
            db.commit()
            db.refresh(existing_rfq)
            rfq = existing_rfq
            logger.info(f"✅ [Enhanced RFQ API] Enhanced RFQ record updated: {rfq.id} (concept files preserved)")
        else:
            # Create new RFQ
            rfq = RFQ(
                title=legacy_fields["title"],
                description=legacy_fields["description"],
                product_category=legacy_fields["product_category"],
                target_segment=legacy_fields["target_segment"],
                research_goal=legacy_fields["research_goal"],
                enhanced_rfq_data=validated_rfq_dict,  # Store complete enhanced data with unmapped_context
                document_upload_id=document_upload_id  # Link to source document if available
            )
            db.add(rfq)
            db.commit()
            db.refresh(rfq)
            logger.info(f"✅ [Enhanced RFQ API] Enhanced RFQ record created with ID: {rfq.id}, document_upload_id: {document_upload_id}")

        # Create initial survey record
        logger.info("💾 [Enhanced RFQ API] Creating initial Survey database record")
        try:
            from src.services.settings_service import SettingsService
            settings_service = SettingsService(db)
            eval_settings = settings_service.get_evaluation_settings()
            model_version_value = eval_settings.get('generation_model')
        except Exception:
            model_version_value = None
        if not model_version_value:
            from src.config.settings import settings as app_settings
            model_version_value = app_settings.generation_model

        survey = Survey(
            rfq_id=rfq.id,
            status="draft",
            model_version=model_version_value
        )
        db.add(survey)
        db.commit()
        db.refresh(survey)
        logger.info(f"✅ [Enhanced RFQ API] Survey record created with ID: {survey.id}")

        # Process Enhanced RFQ through workflow
        logger.info(f"🔄 [Enhanced RFQ API] Starting enhanced workflow processing: workflow_id={workflow_id}")

        try:
            from src.services.workflow_service import WorkflowService
            from src.main import manager  # Import the connection manager

            # Initialize workflow service with connection manager
            workflow_service = WorkflowService(db, manager)

            # custom_prompt already extracted above
            if custom_prompt:
                logger.info(f"🎨 [Enhanced RFQ API] Passing custom prompt to workflow: {len(custom_prompt)} chars")
            
            # Start enhanced workflow processing in background
            asyncio.create_task(process_enhanced_rfq_workflow_async(
                workflow_service=workflow_service,
                enhanced_rfq=validated_rfq,
                workflow_id=workflow_id,
                survey_id=str(survey.id),
                custom_prompt=custom_prompt
            ))

            logger.info(f"✅ [Enhanced RFQ API] Enhanced workflow processing started in background: workflow_id={workflow_id}")

        except Exception as e:
            logger.error(f"❌ [Enhanced RFQ API] Failed to start enhanced workflow processing: {str(e)}")
            # Mark survey as pending if workflow fails to start
            survey.status = "draft"
            db.commit()

        # Return enhanced response
        response = EnhancedRFQResponse(
            rfq_id=str(rfq.id),
            workflow_id=workflow_id,
            survey_id=str(survey.id),
            status="draft",
            enhanced_data_processed=True,
            field_count=field_count
        )

        logger.info(f"🎉 [Enhanced RFQ API] Returning enhanced response: {response.model_dump()}")
        return response

    except Exception as e:
        logger.error(f"❌ [Enhanced RFQ API] Failed to process Enhanced RFQ: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process Enhanced RFQ: {str(e)}")


async def process_enhanced_rfq_workflow_async(
    workflow_service,
    enhanced_rfq: EnhancedRFQRequest,
    workflow_id: str,
    survey_id: str,
    custom_prompt: Optional[str] = None
):
    """
    Process Enhanced RFQ workflow asynchronously with enhanced data context
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🚀 [Enhanced Async Workflow] Starting Enhanced RFQ processing: title='{enhanced_rfq.title}', workflow_id={workflow_id}")
        
        if custom_prompt:
            logger.info(f"🎨 [Enhanced Async Workflow] Custom prompt provided: {len(custom_prompt)} chars")

        # Add a small delay to ensure WebSocket connection is established
        logger.info("⏳ [Enhanced Async Workflow] Waiting 2 seconds for WebSocket connection to establish...")
        await asyncio.sleep(2)

        # Extract legacy fields for workflow compatibility
        legacy_fields = extract_legacy_fields(enhanced_rfq)

        # Process through enhanced workflow with enriched context
        result = await workflow_service.process_enhanced_rfq(
            enhanced_rfq=enhanced_rfq,
            legacy_title=legacy_fields["title"],
            legacy_description=legacy_fields["description"],
            legacy_product_category=legacy_fields["product_category"],
            legacy_target_segment=legacy_fields["target_segment"],
            legacy_research_goal=legacy_fields["research_goal"],
            workflow_id=workflow_id,
            survey_id=survey_id,
            custom_prompt=custom_prompt
        )

        logger.info(f"✅ [Enhanced Async Workflow] Enhanced workflow completed successfully: {result.status}")

    except Exception as e:
        logger.error(f"❌ [Enhanced Async Workflow] Enhanced workflow failed: {str(e)}", exc_info=True)


@router.post("/analyze-text", response_model=DocumentAnalysisResponse)
async def analyze_text_for_rfq(
    text: str,
    filename: str = "text_input.txt",
    db: Session = Depends(get_db)
) -> DocumentAnalysisResponse:
    """
    Analyze plain text for RFQ data extraction (alternative to document upload)
    Returns: RFQ analysis and field mappings from text
    """
    logger.info(f"📝 [RFQ API] Received text analysis request: length={len(text)} chars")

    try:
        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Text is too short. Please provide more detailed content.")

        if len(text) > 50000:  # 50k character limit
            raise HTTPException(status_code=400, detail="Text too long. Maximum length is 50,000 characters.")

        logger.info(f"✅ [RFQ API] Text validation passed")

        # Analyze text using document parser
        logger.info(f"🤖 [RFQ API] Starting text analysis")
        from src.services.document_parser import document_parser

        rfq_data = await document_parser.extract_rfq_data(text)

        # Structure response
        analysis_result = {
            "document_content": {
                "raw_text": text,
                "filename": filename,
                "word_count": len(text.split()),
                "extraction_timestamp": "2024-01-01T00:00:00Z"
            },
            "rfq_analysis": rfq_data,
            "processing_status": "completed",
            "errors": []
        }

        logger.info(f"✅ [RFQ API] Text analysis completed")
        logger.info(f"📊 [RFQ API] Analysis confidence: {rfq_data.get('confidence', 0)}")
        logger.info(f"📊 [RFQ API] Field mappings: {len(rfq_data.get('field_mappings', []))}")

        # Create response
        response = DocumentAnalysisResponse(
            document_content=analysis_result["document_content"],
            rfq_analysis=analysis_result["rfq_analysis"],
            processing_status=analysis_result["processing_status"],
            errors=analysis_result["errors"]
        )

        logger.info(f"🎉 [RFQ API] Text analysis completed successfully")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [RFQ API] Failed to analyze text: {str(e)}", exc_info=True)

        # Determine specific error type for better user feedback
        error_message = "Text analysis failed"
        if "REPLICATE_API_TOKEN" in str(e):
            error_message = "AI service not configured. Please contact support."
        elif "timeout" in str(e).lower():
            error_message = "Text analysis timed out. Please try with shorter text or try again."
        elif "connection" in str(e).lower():
            error_message = "Network error. Please check your connection and try again."
        elif "json" in str(e).lower():
            error_message = "AI service returned invalid response. Please try again."
        else:
            error_message = f"Analysis error: {str(e)}"

        # Return error response
        error_response = DocumentAnalysisResponse(
            document_content={
                "filename": filename,
                "error": "Failed to analyze text",
                "raw_text": text[:100] + "..." if len(text) > 100 else text,
                "word_count": len(text.split()),
                "extraction_timestamp": "2024-01-01T00:00:00Z"
            },
            rfq_analysis={
                "confidence": 0.0,
                "identified_sections": {},
                "extracted_entities": {
                    "stakeholders": [],
                    "industries": [],
                    "research_types": [],
                    "methodologies": []
                },
                "field_mappings": [],
                "processing_error": error_message
            },
            processing_status="error",
            errors=[error_message]
        )

        return error_response


@router.post("/preview-prompt", response_model=PromptPreviewResponse)
async def preview_survey_generation_prompt(
    request: PromptPreviewRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_models_ready)
) -> PromptPreviewResponse:
    """
    Preview the survey generation prompt that would be used for the given RFQ data.
    This uses the same prompt generation logic as the actual survey generation workflow.
    """
    logger.info(f"🔍 [RFQ API] Received prompt preview request: rfq_id='{request.rfq_id}', title='{request.title}', description_length={len(request.description)}")
    
    try:
        # Import required services
        from src.services.prompt_service import PromptService
        from src.services.retrieval_service import RetrievalService
        from src.services.embedding_service import EmbeddingService
        from src.models.enhanced_rfq import validate_enhanced_rfq, extract_legacy_fields
        from uuid import uuid4
        
        # Generate RFQ ID if not provided
        rfq_id = request.rfq_id or f"preview-{str(uuid4())}"
        logger.info(f"📋 [RFQ API] Using RFQ ID: {rfq_id}")
        
        # Extract generation_config from enhanced_rfq_data if available
        generation_config = {}
        if request.enhanced_rfq_data and isinstance(request.enhanced_rfq_data, dict):
            generation_config = request.enhanced_rfq_data.get("generation_config", {})
        
        # Build context similar to what the workflow would create
        context = {
            "rfq_id": rfq_id,
            "rfq_details": {
                "text": request.description,
                "title": request.title,
                "category": request.product_category,
                "segment": request.target_segment,
                "goal": request.research_goal
            },
            "enhanced_rfq_data": request.enhanced_rfq_data,
            "generation_config": generation_config
        }
        
        # Extract unmapped_context from enhanced RFQ data if available
        unmapped_context = ""
        if request.enhanced_rfq_data and isinstance(request.enhanced_rfq_data, dict):
            unmapped_context = request.enhanced_rfq_data.get('unmapped_context', '')
            if unmapped_context:
                logger.info(f"📝 [RFQ API] Found unmapped_context in preview: {len(unmapped_context)} characters")
                context["unmapped_context"] = unmapped_context
        
        # If enhanced RFQ data is provided, validate and extract methodology tags
        methodology_tags = []
        enhanced_rfq_used = False
        
        if request.enhanced_rfq_data:
            try:
                # Validate enhanced RFQ data
                validated_rfq = validate_enhanced_rfq(request.enhanced_rfq_data)
                enhanced_rfq_used = True
                
                # Extract methodology tags from enhanced RFQ (convert to dict first)
                validated_rfq_dict = validated_rfq.model_dump()
                methodology_dict = validated_rfq_dict.get('methodology', {})
                
                # Use selected_methodologies (new approach)
                if methodology_dict.get('selected_methodologies'):
                    methodology_tags = methodology_dict['selected_methodologies']
                    logger.info(f"📊 [RFQ API] Extracted methodology tags from selected_methodologies: {methodology_tags}")
                # Legacy: fallback to methodology_tags field
                elif methodology_dict.get('methodology_tags'):
                    methodology_tags = methodology_dict['methodology_tags']
                    logger.info(f"📊 [RFQ API] Extracted methodology tags from enhanced RFQ: {methodology_tags}")
                # Legacy: fallback to primary_method
                elif methodology_dict.get('primary_method'):
                    methodology_tags = [methodology_dict['primary_method']]
                    logger.info(f"📊 [RFQ API] Extracted methodology from primary_method: {methodology_tags}")
            except Exception as e:
                logger.warning(f"⚠️ [RFQ API] Failed to validate enhanced RFQ data: {str(e)}")
                enhanced_rfq_used = False
        
        # Generate embedding for retrieval (similar to RFQNode)
        logger.info("🔄 [RFQ API] Generating embedding for retrieval...")
        embedding_service = EmbeddingService()
        embedding = await embedding_service.get_embedding(request.description)
        
        # Retrieve golden examples, sections, and methodology blocks (similar to GoldenRetrieverNode)
        logger.info("🔍 [RFQ API] Retrieving golden examples, sections, and methodology blocks...")
        retrieval_service = RetrievalService(db)
        
        golden_examples = []
        golden_sections = []
        methodology_blocks = []
        
        try:
            # Retrieve golden examples
            golden_examples = await retrieval_service.retrieve_golden_pairs(
                embedding=embedding,
                methodology_tags=methodology_tags if methodology_tags else None,
                limit=3
            )
            logger.info(f"📊 [RFQ API] Retrieved {len(golden_examples)} golden examples")
            
            # Retrieve golden sections
            from src.services.rule_based_multi_level_rag_service import RuleBasedMultiLevelRAGService
            rag_service = RuleBasedMultiLevelRAGService(db)
            industry = None
            if request.enhanced_rfq_data and isinstance(request.enhanced_rfq_data, dict):
                industry = request.enhanced_rfq_data.get('advanced_classification', {}).get('industry_classification')
            
            golden_sections = await rag_service.retrieve_golden_sections(
                rfq_text=request.description,
                methodology_tags=methodology_tags if methodology_tags else None,
                industry=industry,
                limit=5
            )
            logger.info(f"📊 [RFQ API] Retrieved {len(golden_sections)} golden sections")
            
            # Retrieve methodology blocks
            methodology_blocks = await retrieval_service.retrieve_methodology_blocks(
                research_goal=request.research_goal or "General market research",
                limit=5
            )
            logger.info(f"📊 [RFQ API] Retrieved {len(methodology_blocks)} methodology blocks")
            
        except Exception as e:
            logger.warning(f"⚠️ [RFQ API] Failed to retrieve examples/sections/blocks: {str(e)}")
            # Continue without retrieval data
        
        # Add retrieved data to context
        context.update({
            "golden_examples": golden_examples,
            "golden_sections": golden_sections,
            "methodology_guidance": methodology_blocks
        })
        
        # Generate the prompt using the same logic as the workflow
        logger.info("🔨 [RFQ API] Generating survey generation prompt...")
        prompt_service = PromptService(db_session=db)
        
        # Use the same method that the workflow uses
        prompt = await prompt_service.create_survey_generation_prompt(
            rfq_text=request.description,
            context=context,
            golden_examples=golden_examples,
            methodology_blocks=methodology_blocks
        )
        
        logger.info(f"✅ [RFQ API] Generated prompt preview: {len(prompt)} characters")
        
        # Retrieve reference examples (golden questions, feedback digest) for preview
        reference_examples = None
        try:
            from src.database.models import GoldenQuestion, QuestionAnnotation
            from src.services.rule_based_multi_level_rag_service import RuleBasedMultiLevelRAGService
            from src.utils.database_session_manager import DatabaseSessionManager
            from src.utils.prompt_formatters import format_golden_questions_for_prompt
            
            logger.info("📊 [RFQ API] Retrieving reference examples for preview...")
            
            # Retrieve golden questions (similar to GoldenRetrieverNode)
            industry = None
            if request.enhanced_rfq_data and isinstance(request.enhanced_rfq_data, dict):
                industry = request.enhanced_rfq_data.get('advanced_classification', {}).get('industry_classification')
            
            golden_questions = await retrieval_service.retrieve_golden_questions(
                embedding=embedding,
                methodology_tags=methodology_tags if methodology_tags else None,
                industry=industry,
                limit=8
            )
            
            # Format 8 questions for prompt
            eight_questions = []
            eight_questions_prompt_text = ""
            if golden_questions:
                question_data_for_formatting = []
                for question in golden_questions[:8]:
                    annotation_comment = None
                    if question.get('annotation_id'):
                        annotation = DatabaseSessionManager.safe_query(
                            db,
                            lambda: db.query(QuestionAnnotation)
                            .filter(QuestionAnnotation.id == question['annotation_id'])
                            .first(),
                            fallback_value=None,
                            operation_name="fetch annotation comment for preview"
                        )
                        if annotation and annotation.comment:
                            annotation_comment = annotation.comment
                    
                    question_dict = {
                        "id": question.get('id', ''),
                        "question_text": question.get('question_text', ''),
                        "question_type": question.get('question_type', 'unknown'),
                        "annotation_comment": annotation_comment,
                        "quality_score": question.get('quality_score', 0.5),
                        "human_verified": question.get('human_verified', False)
                    }
                    eight_questions.append(question_dict)
                    question_data_for_formatting.append(question_dict)
                
                formatted_lines = format_golden_questions_for_prompt(question_data_for_formatting)
                eight_questions_prompt_text = "\n".join(formatted_lines)
            
            # Retrieve feedback digest
            rag_service = RuleBasedMultiLevelRAGService(db)
            feedback_digest_data = await rag_service.get_feedback_digest(
                methodology_tags=methodology_tags if methodology_tags else None,
                industry=industry,
                limit=50
            )
            
            manual_comment_digest_questions = []
            manual_comment_digest_prompt_text = ""
            if feedback_digest_data:
                questions_with_feedback = feedback_digest_data.get('questions_with_feedback', [])
                for feedback_item in questions_with_feedback[:50]:
                    manual_comment_digest_questions.append({
                        "id": feedback_item.get('id', ''),
                        "question_text": feedback_item.get('question_text', ''),
                        "question_type": feedback_item.get('question_type', 'unknown'),
                        "annotation_comment": feedback_item.get('comment', ''),
                        "quality_score": feedback_item.get('quality_score', 0.5),
                        "human_verified": feedback_item.get('human_verified', False)
                    })
                manual_comment_digest_prompt_text = feedback_digest_data.get("feedback_digest", "No manual comment digest available.")
            
            # Format golden examples
            golden_examples_formatted = []
            golden_examples_prompt_text = ""
            if golden_examples:
                prompt_lines = [
                    "## 📋 GOLDEN RFQ-SURVEY PAIRS:",
                    "",
                    "Complete examples of high-quality RFQ-to-survey transformations. Use these as reference for structure, flow, and quality standards.",
                    ""
                ]
                
                for i, example in enumerate(golden_examples, 1):
                    example_title = example.get('title', 'Untitled Golden Example')
                    rfq_text = example.get('rfq_text', '')
                    survey_title = example.get('survey_title', example_title)
                    
                    golden_examples_formatted.append({
                        "id": example.get('id', ''),
                        "title": example_title,
                        "rfq_text": rfq_text[:500] + "..." if len(rfq_text) > 500 else rfq_text,
                        "survey_title": survey_title,
                        "methodology_tags": example.get('methodology_tags', []),
                        "industry_category": example.get('industry_category'),
                        "research_goal": example.get('research_goal'),
                        "quality_score": example.get('quality_score', 0.5),
                        "human_verified": example.get('human_verified', False),
                        "usage_count": example.get('usage_count', 0)
                    })
                    
                    prompt_lines.extend([
                        f"### Example {i}: {example_title}",
                        "",
                        f"**RFQ:**",
                        f"{rfq_text[:300]}..." if len(rfq_text) > 300 else rfq_text,
                        "",
                        f"**Survey Title:** {survey_title}",
                        f"**Methodology:** {', '.join(example.get('methodology_tags', [])) if example.get('methodology_tags') else 'N/A'}",
                        f"**Industry:** {example.get('industry_category') or 'N/A'}",
                        f"**Quality Score:** {example.get('quality_score', 0.5):.2f}/1.0",
                        ""
                    ])
                
                golden_examples_prompt_text = "\n".join(prompt_lines)
            
            # Format golden sections
            golden_sections_formatted = []
            golden_sections_prompt_text = ""
            if golden_sections:
                prompt_lines = [
                    "# 4.2.5 EXPERT SECTION EXAMPLES",
                    "",
                    "High-quality sections from verified surveys - use as templates for section structure and flow:",
                    ""
                ]
                
                for i, section in enumerate(golden_sections, 1):
                    section_title = section.get('section_title', 'Untitled Section')
                    section_text = section.get('section_text', '')
                    
                    golden_sections_formatted.append({
                        "id": section.get('id', ''),
                        "section_id": section.get('section_id', ''),
                        "section_title": section_title,
                        "section_text": section_text[:500] + "..." if len(section_text) > 500 else section_text,
                        "section_type": section.get('section_type', 'unknown'),
                        "methodology_tags": section.get('methodology_tags', []),
                        "industry_keywords": section.get('industry_keywords', []),
                        "quality_score": section.get('quality_score', 0.5),
                        "human_verified": section.get('human_verified', False)
                    })
                    
                    truncated_text = section_text[:300] + "..." if len(section_text) > 300 else section_text
                    prompt_lines.extend([
                        f"**Section Example {i}:** {section_title}",
                        f"**Type:** {section.get('section_type', 'unknown')} | **Quality:** {section.get('quality_score', 0.5):.2f}/1.0 | {'✅ Verified' if section.get('human_verified') else '🤖 AI'}",
                    ])
                    
                    if section.get('methodology_tags'):
                        prompt_lines.append(f"**Methodology:** {', '.join(section.get('methodology_tags', []))}")
                    
                    prompt_lines.extend([
                        f"**Section Text:** {truncated_text}",
                        ""
                    ])
                
                prompt_lines.extend([
                    "**USAGE INSTRUCTIONS:**",
                    "- Use these sections as templates for structure, flow, and question organization",
                    "- Pay attention to how questions are grouped and sequenced within sections",
                    "- Adapt section titles and intro text to match your RFQ context",
                    ""
                ])
                
                golden_sections_prompt_text = "\n".join(prompt_lines)
            
            reference_examples = {
                "eight_questions_tab": {
                    "prompt_text": eight_questions_prompt_text,
                    "questions": eight_questions
                },
                "manual_comment_digest_tab": {
                    "prompt_text": manual_comment_digest_prompt_text,
                    "questions": manual_comment_digest_questions,
                    "is_reconstructed": False,  # Not reconstructed in preview
                    "total_feedback_count": feedback_digest_data.get("total_feedback_count", 0) if feedback_digest_data else 0
                },
                "golden_examples_tab": {
                    "prompt_text": golden_examples_prompt_text,
                    "examples": golden_examples_formatted
                },
                "golden_sections_tab": {
                    "prompt_text": golden_sections_prompt_text,
                    "sections": golden_sections_formatted
                }
            }
            
            logger.info(f"✅ [RFQ API] Reference examples prepared: {len(eight_questions)} questions, {len(manual_comment_digest_questions)} feedback questions, {len(golden_examples_formatted)} golden examples, {len(golden_sections_formatted)} golden sections")
        except Exception as e:
            logger.warning(f"⚠️ [RFQ API] Failed to retrieve reference examples for preview: {str(e)}")
            # Continue without reference examples - preview will still work
        
        # Prepare response
        response = PromptPreviewResponse(
            rfq_id=rfq_id,
            prompt=prompt,
            prompt_length=len(prompt),
            context_info={
                "rfq_title": request.title,
                "rfq_description_length": len(request.description),
                "product_category": request.product_category,
                "target_segment": request.target_segment,
                "research_goal": request.research_goal,
                "enhanced_rfq_fields": len(request.enhanced_rfq_data) if request.enhanced_rfq_data else 0
            },
            methodology_tags=methodology_tags,
            golden_examples_count=len(golden_examples),
            methodology_blocks_count=len(methodology_blocks),
            enhanced_rfq_used=enhanced_rfq_used,
            reference_examples=reference_examples
        )
        
        logger.info(f"🎉 [RFQ API] Prompt preview completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"❌ [RFQ API] Failed to generate prompt preview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate prompt preview: {str(e)}"
        )


# Concept File Upload Models
class ConceptFileUploadResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    concept_stimulus_id: Optional[str] = None
    display_order: int
    upload_timestamp: str


class ConceptFileListResponse(BaseModel):
    concept_files: List[ConceptFileUploadResponse]


# Allowed file types for concept uploads
ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
ALLOWED_CONTENT_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_DOCUMENT_TYPES
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/concept/upload", response_model=ConceptFileUploadResponse)
async def upload_concept_file(
    file: UploadFile = File(...),
    rfq_id: str = Form(...),
    concept_stimulus_id: Optional[str] = Form(None),
    display_order: int = Form(0),
    db: Session = Depends(get_db)
) -> ConceptFileUploadResponse:
    """
    Upload a concept file (image or document) for an RFQ
    Supports: PNG, JPG, GIF, WebP (images) and PDF, DOCX (documents)
    Max file size: 10MB
    """
    logger.info(f"📎 [Concept API] Received concept file upload: filename='{file.filename}', rfq_id='{rfq_id}'")
    
    try:
        # Validate RFQ exists
        try:
            rfq_uuid = UUID(rfq_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid RFQ ID format")
        
        rfq = db.query(RFQ).filter(RFQ.id == rfq_uuid).first()
        if not rfq:
            raise HTTPException(status_code=404, detail="RFQ not found")
        
        # Validate file type
        if not file.content_type or file.content_type not in ALLOWED_CONTENT_TYPES:
            allowed_str = ', '.join(ALLOWED_IMAGE_TYPES + ALLOWED_DOCUMENT_TYPES)
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: Images (PNG, JPG, GIF, WebP) and Documents (PDF, DOCX)"
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        logger.info(f"✅ [Concept API] File validated: size={len(file_content)} bytes, type={file.content_type}")
        
        # Create ConceptFile record
        from src.database.models import ConceptFile
        
        concept_file = ConceptFile(
            rfq_id=rfq_uuid,
            filename=file.filename or f"concept_{uuid4().hex[:8]}",
            original_filename=file.filename,
            file_size=len(file_content),
            content_type=file.content_type,
            file_data=file_content,
            concept_stimulus_id=concept_stimulus_id,
            display_order=display_order
        )
        
        db.add(concept_file)
        db.commit()
        db.refresh(concept_file)
        
        logger.info(f"✅ [Concept API] Concept file uploaded successfully: id={concept_file.id}")
        
        return ConceptFileUploadResponse(
            id=str(concept_file.id),
            filename=concept_file.filename,
            original_filename=concept_file.original_filename or concept_file.filename,
            file_size=concept_file.file_size,
            content_type=concept_file.content_type,
            concept_stimulus_id=concept_file.concept_stimulus_id,
            display_order=concept_file.display_order,
            upload_timestamp=concept_file.upload_timestamp.isoformat() if concept_file.upload_timestamp else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Concept API] Failed to upload concept file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload concept file: {str(e)}"
        )


@router.get("/{rfq_id}/concepts", response_model=ConceptFileListResponse)
async def get_concept_files(
    rfq_id: str,
    db: Session = Depends(get_db)
) -> ConceptFileListResponse:
    """
    Get all concept files for an RFQ
    """
    logger.info(f"📎 [Concept API] Fetching concept files for rfq_id='{rfq_id}'")
    
    try:
        try:
            rfq_uuid = UUID(rfq_id)
            logger.info(f"🔍 [Concept API] Parsed UUID: {rfq_uuid}")
        except ValueError as e:
            logger.error(f"❌ [Concept API] Invalid RFQ ID format: {rfq_id}, error: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid RFQ ID format")
        
        rfq = db.query(RFQ).filter(RFQ.id == rfq_uuid).first()
        if not rfq:
            logger.warning(f"⚠️ [Concept API] RFQ not found: {rfq_uuid}")
            raise HTTPException(status_code=404, detail="RFQ not found")
        
        logger.info(f"✅ [Concept API] RFQ found: id={rfq.id}, title='{rfq.title}'")
        
        from src.database.models import ConceptFile
        
        # Diagnostic: Check total concept files in database
        total_files = db.query(ConceptFile).count()
        logger.info(f"🔍 [Concept API] Total concept files in database: {total_files}")
        
        # Query concept files for this RFQ
        concept_files = db.query(ConceptFile).filter(
            ConceptFile.rfq_id == rfq_uuid
        ).order_by(ConceptFile.display_order, ConceptFile.created_at).all()
        
        logger.info(f"🔍 [Concept API] Found {len(concept_files)} concept files in database for rfq_id={rfq_uuid}")
        
        # Diagnostic: Check if there are files for other RFQs (debug level only)
        if len(concept_files) == 0 and total_files > 0:
            logger.debug(f"🔍 [Concept API] No files found for this RFQ, but {total_files} total files exist in database")
            
            # Check for orphaned files: files uploaded around the same time as this RFQ was created
            from datetime import timedelta
            time_window = timedelta(hours=24)  # 24 hour window
            rfq_created_at = rfq.created_at if hasattr(rfq, 'created_at') and rfq.created_at else None
            
            if rfq_created_at:
                potential_orphaned = db.query(ConceptFile).filter(
                    ConceptFile.created_at >= rfq_created_at - time_window,
                    ConceptFile.created_at <= rfq_created_at + time_window,
                    ConceptFile.rfq_id != rfq_uuid
                ).all()
                
                if potential_orphaned:
                    logger.warning(f"⚠️ [Concept API] Found {len(potential_orphaned)} concept files uploaded within 24 hours of RFQ creation but associated with different RFQ IDs:")
                    for po in potential_orphaned:
                        other_rfq = db.query(RFQ).filter(RFQ.id == po.rfq_id).first()
                        other_rfq_title = other_rfq.title if other_rfq else "Unknown"
                        logger.warning(f"  📄 Orphaned candidate: rfq_id={po.rfq_id} (title: '{other_rfq_title}'), filename='{po.filename}', created_at={po.created_at}")
        
        # Log each file found
        for cf in concept_files:
            logger.info(f"  📄 File: id={cf.id}, filename='{cf.filename}', size={cf.file_size}, type={cf.content_type}")
        
        files_response = [
            ConceptFileUploadResponse(
                id=str(cf.id),
                filename=cf.filename,
                original_filename=cf.original_filename or cf.filename,
                file_size=cf.file_size,
                content_type=cf.content_type,
                concept_stimulus_id=cf.concept_stimulus_id,
                display_order=cf.display_order,
                upload_timestamp=cf.upload_timestamp.isoformat() if cf.upload_timestamp else ""
            )
            for cf in concept_files
        ]
        
        logger.info(f"✅ [Concept API] Retrieved {len(files_response)} concept files, returning response")
        
        # Ensure we always return a valid response, even if empty
        response = ConceptFileListResponse(concept_files=files_response)
        logger.info(f"📤 [Concept API] Response object created: {len(response.concept_files)} files")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Concept API] Failed to fetch concept files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch concept files: {str(e)}"
        )


@router.get("/concept/{concept_file_id}")
async def download_concept_file(
    concept_file_id: str,
    db: Session = Depends(get_db)
) -> Response:
    """
    Download/view a concept file by ID
    """
    logger.info(f"📎 [Concept API] Downloading concept file: id='{concept_file_id}'")
    
    try:
        try:
            file_uuid = UUID(concept_file_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid concept file ID format")
        
        from src.database.models import ConceptFile
        
        concept_file = db.query(ConceptFile).filter(ConceptFile.id == file_uuid).first()
        if not concept_file:
            raise HTTPException(status_code=404, detail="Concept file not found")
        
        logger.info(f"✅ [Concept API] Serving concept file: {concept_file.filename}")
        
        return Response(
            content=bytes(concept_file.file_data),
            media_type=concept_file.content_type,
            headers={
                "Content-Disposition": f'inline; filename="{concept_file.original_filename or concept_file.filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Concept API] Failed to download concept file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download concept file: {str(e)}"
        )


@router.delete("/concept/{concept_file_id}")
async def delete_concept_file(
    concept_file_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a concept file by ID
    """
    logger.info(f"📎 [Concept API] Deleting concept file: id='{concept_file_id}'")
    
    try:
        try:
            file_uuid = UUID(concept_file_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid concept file ID format")
        
        from src.database.models import ConceptFile
        
        concept_file = db.query(ConceptFile).filter(ConceptFile.id == file_uuid).first()
        if not concept_file:
            raise HTTPException(status_code=404, detail="Concept file not found")
        
        db.delete(concept_file)
        db.commit()
        
        logger.info(f"✅ [Concept API] Concept file deleted: {concept_file.filename}")
        
        return {"message": "Concept file deleted successfully", "id": concept_file_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Concept API] Failed to delete concept file: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete concept file: {str(e)}"
        )
