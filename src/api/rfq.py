from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from src.database import get_db, RFQ, Survey
from src.models.enhanced_rfq import (
    EnhancedRFQRequest,
    EnhancedRFQResponse,
    validate_enhanced_rfq,
    extract_legacy_fields,
    count_populated_fields
)
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import uuid4
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


class RFQSubmissionResponse(BaseModel):
    workflow_id: str
    survey_id: str
    status: str


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


@router.post("/", response_model=RFQSubmissionResponse)
async def submit_rfq(
    request: RFQSubmissionRequest,
    db: Session = Depends(get_db)
) -> RFQSubmissionResponse:
    """
    Submit new RFQ for survey generation
    Returns: workflow_id, survey_id, status (async processing)
    """
    logger.info(f"🚀 [RFQ API] Received RFQ submission: title='{request.title}', description_length={len(request.description)}, product_category='{request.product_category}'")
    
    try:
        # Generate unique IDs
        workflow_id = f"survey-gen-{str(uuid4())}"
        survey_id = f"survey-{str(uuid4())}"
        
        logger.info(f"📋 [RFQ API] Generated workflow_id={workflow_id}, survey_id={survey_id}")
        
        # Create RFQ record
        logger.info("💾 [RFQ API] Creating RFQ database record")

        # Check if this is an enhanced RFQ submission
        is_enhanced_rfq = request.enhanced_rfq_data is not None
        if is_enhanced_rfq:
            logger.info(f"🎯 [RFQ API] Enhanced RFQ detected with structured data: objectives={len(request.enhanced_rfq_data.get('objectives', []))}, constraints={len(request.enhanced_rfq_data.get('constraints', []))}")

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
            status="started",
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
            
            # Start workflow processing in background with a small delay to ensure WebSocket connection
            asyncio.create_task(process_rfq_workflow_async(
                workflow_service=workflow_service,
                title=request.title,
                description=request.description,
                product_category=request.product_category,
                target_segment=request.target_segment,
                research_goal=request.research_goal,
                workflow_id=workflow_id,
                survey_id=str(survey.id)
            ))
            
            logger.info(f"✅ [RFQ API] Workflow processing started in background: workflow_id={workflow_id}")
            
        except Exception as e:
            logger.error(f"❌ [RFQ API] Failed to start workflow processing: {str(e)}")
            # Mark survey as pending if workflow fails to start
            survey.status = "pending"
            db.commit()
        
        # Return immediate response
        response = RFQSubmissionResponse(
            workflow_id=workflow_id,
            survey_id=str(survey.id),
            status="started"
        )
        
        logger.info(f"🎉 [RFQ API] Returning async response: {response.model_dump()}")
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
    survey_id: str
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
            survey_id=survey_id
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

        # Generate unique IDs
        workflow_id = f"enhanced-survey-gen-{str(uuid4())}"
        survey_id = f"enhanced-survey-{str(uuid4())}"

        logger.info(f"📋 [Enhanced RFQ API] Generated workflow_id={workflow_id}, survey_id={survey_id}")

        # Create RFQ record with enhanced data
        logger.info("💾 [Enhanced RFQ API] Creating Enhanced RFQ database record")

        rfq = RFQ(
            title=legacy_fields["title"],
            description=legacy_fields["description"],
            product_category=legacy_fields["product_category"],
            target_segment=legacy_fields["target_segment"],
            research_goal=legacy_fields["research_goal"],
            enhanced_rfq_data=validated_rfq.model_dump()  # Store complete enhanced data
        )
        db.add(rfq)
        db.commit()
        db.refresh(rfq)
        logger.info(f"✅ [Enhanced RFQ API] Enhanced RFQ record created with ID: {rfq.id}")

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
            status="started",
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

            # Start enhanced workflow processing in background
            asyncio.create_task(process_enhanced_rfq_workflow_async(
                workflow_service=workflow_service,
                enhanced_rfq=validated_rfq,
                workflow_id=workflow_id,
                survey_id=str(survey.id)
            ))

            logger.info(f"✅ [Enhanced RFQ API] Enhanced workflow processing started in background: workflow_id={workflow_id}")

        except Exception as e:
            logger.error(f"❌ [Enhanced RFQ API] Failed to start enhanced workflow processing: {str(e)}")
            # Mark survey as pending if workflow fails to start
            survey.status = "pending"
            db.commit()

        # Return enhanced response
        response = EnhancedRFQResponse(
            rfq_id=str(rfq.id),
            workflow_id=workflow_id,
            survey_id=str(survey.id),
            status="started",
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
    survey_id: str
):
    """
    Process Enhanced RFQ workflow asynchronously with enhanced data context
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🚀 [Enhanced Async Workflow] Starting Enhanced RFQ processing: title='{enhanced_rfq.title}', workflow_id={workflow_id}")

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
            survey_id=survey_id
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
    db: Session = Depends(get_db)
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
            "enhanced_rfq_data": request.enhanced_rfq_data
        }
        
        # If enhanced RFQ data is provided, validate and extract methodology tags
        methodology_tags = []
        enhanced_rfq_used = False
        
        if request.enhanced_rfq_data:
            try:
                # Validate enhanced RFQ data
                validated_rfq = validate_enhanced_rfq(request.enhanced_rfq_data)
                enhanced_rfq_used = True
                
                # Extract methodology tags from enhanced RFQ
                if validated_rfq.get('methodology') and validated_rfq['methodology'].get('methodology_tags'):
                    methodology_tags = validated_rfq['methodology']['methodology_tags']
                    logger.info(f"📊 [RFQ API] Extracted methodology tags from enhanced RFQ: {methodology_tags}")
            except Exception as e:
                logger.warning(f"⚠️ [RFQ API] Failed to validate enhanced RFQ data: {str(e)}")
                enhanced_rfq_used = False
        
        # Generate embedding for retrieval (similar to RFQNode)
        logger.info("🔄 [RFQ API] Generating embedding for retrieval...")
        embedding_service = EmbeddingService()
        embedding = await embedding_service.get_embedding(request.description)
        
        # Retrieve golden examples and methodology blocks (similar to GoldenRetrieverNode)
        logger.info("🔍 [RFQ API] Retrieving golden examples and methodology blocks...")
        retrieval_service = RetrievalService(db)
        
        golden_examples = []
        methodology_blocks = []
        
        try:
            # Retrieve golden examples
            golden_examples = await retrieval_service.retrieve_golden_pairs(
                embedding=embedding,
                methodology_tags=methodology_tags if methodology_tags else None,
                limit=3
            )
            logger.info(f"📊 [RFQ API] Retrieved {len(golden_examples)} golden examples")
            
            # Retrieve methodology blocks
            methodology_blocks = await retrieval_service.retrieve_methodology_blocks(
                research_goal=request.research_goal or "General market research",
                limit=5
            )
            logger.info(f"📊 [RFQ API] Retrieved {len(methodology_blocks)} methodology blocks")
            
        except Exception as e:
            logger.warning(f"⚠️ [RFQ API] Failed to retrieve examples/blocks: {str(e)}")
            # Continue without retrieval data
        
        # Add retrieved data to context
        context.update({
            "golden_examples": golden_examples,
            "methodology_guidance": methodology_blocks
        })
        
        # Generate the prompt using the same logic as the workflow
        logger.info("🔨 [RFQ API] Generating survey generation prompt...")
        prompt_service = PromptService(db_session=db)
        
        # Use the same method that the workflow uses
        prompt = prompt_service.create_survey_generation_prompt(
            rfq_text=request.description,
            context=context,
            golden_examples=golden_examples,
            methodology_blocks=methodology_blocks
        )
        
        logger.info(f"✅ [RFQ API] Generated prompt preview: {len(prompt)} characters")
        
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
            enhanced_rfq_used=enhanced_rfq_used
        )
        
        logger.info(f"🎉 [RFQ API] Prompt preview completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"❌ [RFQ API] Failed to generate prompt preview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate prompt preview: {str(e)}"
        )
