from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.api.dependencies import require_models_ready
from src.services.annotation_insights_service import AnnotationInsightsService
from src.utils.database_session_manager import DatabaseSessionManager
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["annotation-insights"])


@router.get("/annotation-insights")
async def get_annotation_insights(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get annotation insights for the dashboard
    """
    try:
        logger.info("🔍 [API] Fetching annotation insights for dashboard")
        
        # Get insights service
        insights_service = AnnotationInsightsService(db)
        
        # Extract quality patterns
        patterns = await insights_service.extract_quality_patterns()
        
        # Get quality guidelines for dashboard
        guidelines = await insights_service.get_quality_guidelines()
        
        # Calculate REAL summary statistics from database
        from src.database.models import QuestionAnnotation, SectionAnnotation, SurveyAnnotation
        
        # Count total annotations with proper session management
        qa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).count(),
            fallback_value=0,
            operation_name="question annotations count"
        )
        
        sa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).count(),
            fallback_value=0,
            operation_name="section annotations count"
        )
        
        sva_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SurveyAnnotation).count(),
            fallback_value=0,
            operation_name="survey annotations count"
        )
        
        total_annotations = qa_count + sa_count + sva_count
        
        # Calculate Human vs AI annotation statistics
        ai_qa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(QuestionAnnotation.ai_generated == True).count(),
            fallback_value=0,
            operation_name="AI question annotations count"
        )
        
        human_qa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(QuestionAnnotation.annotator_id == "current-user").count(),
            fallback_value=0,
            operation_name="human question annotations count"
        )
        
        ai_sa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(SectionAnnotation.ai_generated == True).count(),
            fallback_value=0,
            operation_name="AI section annotations count"
        )
        
        human_sa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(SectionAnnotation.annotator_id == "current-user").count(),
            fallback_value=0,
            operation_name="human section annotations count"
        )
        
        # Calculate override statistics
        overridden_qa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(QuestionAnnotation.human_overridden == True).count(),
            fallback_value=0,
            operation_name="overridden question annotations count"
        )
        
        overridden_sa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(SectionAnnotation.human_overridden == True).count(),
            fallback_value=0,
            operation_name="overridden section annotations count"
        )
        
        # Calculate verification statistics
        verified_qa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(QuestionAnnotation.human_verified == True).count(),
            fallback_value=0,
            operation_name="verified question annotations count"
        )
        
        verified_sa_count = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(SectionAnnotation.human_verified == True).count(),
            fallback_value=0,
            operation_name="verified section annotations count"
        )
        
        # Calculate AI confidence statistics
        ai_qa_with_confidence = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(QuestionAnnotation).filter(
                QuestionAnnotation.ai_generated == True,
                QuestionAnnotation.ai_confidence.isnot(None)
            ).count(),
            fallback_value=0,
            operation_name="AI QA with confidence count"
        )
        
        ai_sa_with_confidence = DatabaseSessionManager.safe_query(
            db,
            lambda: db.query(SectionAnnotation).filter(
                SectionAnnotation.ai_generated == True,
                SectionAnnotation.ai_confidence.isnot(None)
            ).count(),
            fallback_value=0,
            operation_name="AI SA with confidence count"
        )
        
        # Calculate average AI confidence
        avg_confidence = 0.0
        if ai_qa_with_confidence > 0 or ai_sa_with_confidence > 0:
            try:
                qa_confidences = [float(qa.ai_confidence) for qa in db.query(QuestionAnnotation).filter(
                    QuestionAnnotation.ai_generated == True,
                    QuestionAnnotation.ai_confidence.isnot(None)
                ).all() if qa.ai_confidence is not None]
                
                sa_confidences = [float(sa.ai_confidence) for sa in db.query(SectionAnnotation).filter(
                    SectionAnnotation.ai_generated == True,
                    SectionAnnotation.ai_confidence.isnot(None)
                ).all() if sa.ai_confidence is not None]
                
                all_confidences = qa_confidences + sa_confidences
                if all_confidences:
                    avg_confidence = sum(all_confidences) / len(all_confidences)
            except Exception as e:
                logger.error(f"❌ [API] Failed to calculate average AI confidence: {e}")
                avg_confidence = 0.0
        
        # Calculate high quality count (score >= 4.0) with error handling
        try:
            high_quality_qa = db.query(QuestionAnnotation).filter(
                (QuestionAnnotation.methodological_rigor + 
                 QuestionAnnotation.content_validity + 
                 QuestionAnnotation.respondent_experience + 
                 QuestionAnnotation.analytical_value + 
                 QuestionAnnotation.business_impact) >= 20  # 4.0 * 5 pillars
            ).count()
        except Exception as e:
            logger.error(f"❌ [API] Failed to calculate high quality QA count: {e}")
            db.rollback()
            high_quality_qa = 0
        
        try:
            high_quality_sa = db.query(SectionAnnotation).filter(
                (SectionAnnotation.methodological_rigor + 
                 SectionAnnotation.content_validity + 
                 SectionAnnotation.respondent_experience + 
                 SectionAnnotation.analytical_value + 
                 SectionAnnotation.business_impact) >= 20
            ).count()
        except Exception as e:
            logger.error(f"❌ [API] Failed to calculate high quality SA count: {e}")
            db.rollback()
            high_quality_sa = 0
        
        high_quality_count = high_quality_qa + high_quality_sa
        
        # Calculate low quality count (score < 3.0) with error handling
        try:
            low_quality_qa = db.query(QuestionAnnotation).filter(
                (QuestionAnnotation.methodological_rigor + 
                 QuestionAnnotation.content_validity + 
                 QuestionAnnotation.respondent_experience + 
                 QuestionAnnotation.analytical_value + 
                 QuestionAnnotation.business_impact) < 15  # 3.0 * 5 pillars
            ).count()
        except Exception as e:
            logger.error(f"❌ [API] Failed to calculate low quality QA count: {e}")
            db.rollback()
            low_quality_qa = 0
        
        try:
            low_quality_sa = db.query(SectionAnnotation).filter(
                (SectionAnnotation.methodological_rigor + 
                 SectionAnnotation.content_validity + 
                 SectionAnnotation.respondent_experience + 
                 SectionAnnotation.analytical_value + 
                 SectionAnnotation.business_impact) < 15
            ).count()
        except Exception as e:
            logger.error(f"❌ [API] Failed to calculate low quality SA count: {e}")
            db.rollback()
            low_quality_sa = 0
        
        low_quality_count = low_quality_qa + low_quality_sa
        
        # Calculate REAL average score with error handling
        all_qa_scores = []
        try:
            for qa in db.query(QuestionAnnotation).all():
                avg_score = (qa.methodological_rigor + qa.content_validity + 
                            qa.respondent_experience + qa.analytical_value + 
                            qa.business_impact) / 5.0
                all_qa_scores.append(avg_score)
        except Exception as e:
            logger.error(f"❌ [API] Failed to calculate QA scores: {e}")
            db.rollback()
            all_qa_scores = []
        
        all_sa_scores = []
        try:
            for sa in db.query(SectionAnnotation).all():
                avg_score = (sa.methodological_rigor + sa.content_validity + 
                            sa.respondent_experience + sa.analytical_value + 
                            sa.business_impact) / 5.0
                all_sa_scores.append(avg_score)
        except Exception as e:
            logger.error(f"❌ [API] Failed to calculate SA scores: {e}")
            db.rollback()
            all_sa_scores = []
        
        all_scores = all_qa_scores + all_sa_scores
        average_score = sum(all_scores) / len(all_scores) if all_scores else 3.0
        
        # Calculate improvement trend using time-based analysis
        improvement_trend_data = await insights_service.calculate_improvement_trend()
        improvement_trend = improvement_trend_data.get("improvement_trend", 0.0)
        
        # If no annotations found, return empty state
        if total_annotations == 0:
            logger.info("📊 [API] No annotations found in database, returning empty state")
            response = {
                "summary": {
                    "total_annotations": 0,
                    "high_quality_count": 0,
                    "low_quality_count": 0,
                    "average_score": 0.0,
                    "improvement_trend": improvement_trend,
                    "improvement_trend_metadata": improvement_trend_data
                },
                "human_vs_ai_stats": {
                    "total_ai_annotations": 0,
                    "total_human_annotations": 0,
                    "ai_question_annotations": 0,
                    "ai_section_annotations": 0,
                    "human_question_annotations": 0,
                    "human_section_annotations": 0,
                    "overridden_annotations": 0,
                    "verified_annotations": 0,
                    "average_ai_confidence": 0.0,
                    "ai_annotations_with_confidence": 0
                },
                "high_quality_patterns": [],
                "common_issues": [],
                "low_quality_patterns": {},
                "metadata": {
                    "last_updated": "2024-01-15T10:30:00Z",
                    "data_source": "annotation_database",
                    "status": "no_data"
                }
            }
        else:
            # Format response with actual data
            response = {
                "summary": {
                    "total_annotations": total_annotations,
                    "high_quality_count": high_quality_count,
                    "low_quality_count": low_quality_count,
                    "average_score": average_score,
                    "improvement_trend": improvement_trend,
                    "improvement_trend_metadata": improvement_trend_data
                },
                "human_vs_ai_stats": {
                    "total_ai_annotations": ai_qa_count + ai_sa_count,
                    "total_human_annotations": human_qa_count + human_sa_count,
                    "ai_question_annotations": ai_qa_count,
                    "ai_section_annotations": ai_sa_count,
                    "human_question_annotations": human_qa_count,
                    "human_section_annotations": human_sa_count,
                    "overridden_annotations": overridden_qa_count + overridden_sa_count,
                    "verified_annotations": verified_qa_count + verified_sa_count,
                    "average_ai_confidence": round(avg_confidence, 3),
                    "ai_annotations_with_confidence": ai_qa_with_confidence + ai_sa_with_confidence
                },
                "high_quality_patterns": guidelines.get("high_quality_examples", []),
                "common_issues": guidelines.get("common_issues", []),
                "low_quality_patterns": patterns.get("low_quality_patterns", {}),
                "metadata": {
                    "last_updated": "2024-01-15T10:30:00Z",
                    "data_source": "annotation_database"
                }
            }
        
        logger.info(f"✅ [API] Successfully fetched annotation insights: {total_annotations} total annotations")
        return response
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to fetch annotation insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch annotation insights: {str(e)}"
        )


@router.get("/annotation-insights/retrieval-test")
async def test_annotation_weighted_retrieval(
    rfq_text: str = Query(..., description="RFQ text to test retrieval"),
    limit: int = Query(5, description="Number of examples to retrieve"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_models_ready)
) -> Dict[str, Any]:
    """
    Test annotation-weighted golden example retrieval
    """
    try:
        logger.info(f"🔍 [API] Testing annotation-weighted retrieval for RFQ")
        
        from src.services.retrieval_service import RetrievalService
        retrieval_service = RetrievalService(db)
        
        # Test retrieval with annotation weighting
        golden_examples = await retrieval_service.retrieve_golden_pairs(rfq_text, limit)
        
        return {
            "rfq_text": rfq_text,
            "retrieved_examples": len(golden_examples),
            "examples": [
                {
                    "survey_id": ex.get("survey_id"),
                    "similarity": ex.get("similarity"),
                    "weighted_similarity": ex.get("weighted_similarity"),
                    "annotation_score": ex.get("annotation_score"),
                    "title": ex.get("title", "Untitled")
                }
                for ex in golden_examples
            ],
            "message": "Annotation-weighted retrieval test completed"
        }
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to test annotation-weighted retrieval: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test annotation-weighted retrieval: {str(e)}"
        )

@router.get("/annotation-insights/prompt-test")
async def test_enhanced_prompt(
    rfq_text: str = Query(..., description="RFQ text to test prompt enhancement"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test enhanced prompt with annotation insights
    """
    try:
        logger.info(f"🔍 [API] Testing enhanced prompt with annotation insights")
        
        from src.services.prompt_service import PromptService
        prompt_service = PromptService()
        
        # Test enhanced prompt generation
        enhanced_prompt = await prompt_service.create_survey_generation_prompt(
            rfq_text=rfq_text,
            methodology="mixed_methods",  # Default for testing
            industry="technology"  # Default for testing
        )
        
        return {
            "rfq_text": rfq_text,
            "enhanced_prompt_length": len(enhanced_prompt),
            "prompt_preview": enhanced_prompt[:500] + "..." if len(enhanced_prompt) > 500 else enhanced_prompt,
            "contains_annotation_insights": "annotation" in enhanced_prompt.lower() or "quality" in enhanced_prompt.lower(),
            "message": "Enhanced prompt test completed"
        }
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to test enhanced prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test enhanced prompt: {str(e)}"
        )

@router.get("/annotation-insights/patterns")
async def get_quality_patterns(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get detailed quality patterns for analysis
    """
    try:
        logger.info("🔍 [API] Fetching detailed quality patterns")
        
        insights_service = AnnotationInsightsService(db)
        patterns = await insights_service.extract_quality_patterns()
        
        return patterns
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to fetch quality patterns: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch quality patterns: {str(e)}"
        )


@router.get("/annotation-insights/guidelines")
async def get_quality_guidelines(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get quality guidelines for prompt injection
    """
    try:
        logger.info("🔍 [API] Fetching quality guidelines")
        
        insights_service = AnnotationInsightsService(db)
        guidelines = await insights_service.get_quality_guidelines()
        
        return guidelines
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to fetch quality guidelines: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch quality guidelines: {str(e)}"
        )


@router.get("/annotation-insights/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check for annotation insights database connection
    """
    try:
        logger.info("🔍 [API] Performing annotation insights health check")
        
        # Rollback any existing failed transaction
        db.rollback()
        
        # Test basic database connectivity
        from src.database.models import QuestionAnnotation, SectionAnnotation, SurveyAnnotation
        
        # Simple count queries to test connectivity
        qa_count = db.query(QuestionAnnotation).count()
        sa_count = db.query(SectionAnnotation).count()
        sva_count = db.query(SurveyAnnotation).count()
        
        total_annotations = qa_count + sa_count + sva_count
        
        return {
            "status": "healthy",
            "database_connected": True,
            "annotation_counts": {
                "question_annotations": qa_count,
                "section_annotations": sa_count,
                "survey_annotations": sva_count,
                "total": total_annotations
            },
            "message": "Database connection is healthy"
        }
        
    except Exception as e:
        logger.error(f"❌ [API] Health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e),
            "message": "Database connection failed"
        }
