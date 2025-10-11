"""
AI Annotation Service
Converts evaluation results to annotation records for database storage
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import QuestionAnnotation, SectionAnnotation
from evaluations.modules.single_call_evaluator import SingleCallEvaluationResult

logger = logging.getLogger(__name__)


class AIAnnotationService:
    """Service for converting evaluation results to AI-generated annotations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    async def create_annotations_from_evaluation(
        self, 
        evaluation_result: SingleCallEvaluationResult, 
        survey_id: str,
        annotator_id: str = "ai_system"
    ) -> Dict[str, Any]:
        """
        Create question and section annotations from evaluation result
        
        Args:
            evaluation_result: SingleCallEvaluationResult from evaluator
            survey_id: Survey identifier
            annotator_id: Identifier for the AI system
            
        Returns:
            Dict with created annotation counts and details
        """
        try:
            logger.info(f"🤖 Creating AI annotations for survey {survey_id}")
            
            # Clean up existing AI annotations for this survey to avoid constraint violations
            logger.info(f"🧹 Cleaning up existing AI annotations for survey {survey_id}")
            
            # Delete existing question annotations
            deleted_questions = self.db_session.query(QuestionAnnotation).filter(
                QuestionAnnotation.survey_id == survey_id,
                QuestionAnnotation.annotator_id == annotator_id
            ).delete(synchronize_session=False)
            
            # Delete existing section annotations
            deleted_sections = self.db_session.query(SectionAnnotation).filter(
                SectionAnnotation.survey_id == survey_id,
                SectionAnnotation.annotator_id == annotator_id
            ).delete(synchronize_session=False)
            
            # Commit the cleanup
            self.db_session.commit()
            logger.info(f"✅ Cleaned up {deleted_questions} question and {deleted_sections} section annotations")
            
            created_annotations = {
                "question_annotations": [],
                "section_annotations": [],
                "total_created": 0,
                "errors": []
            }
            
            # Create question annotations
            for q_annotation in evaluation_result.question_annotations:
                try:
                    annotation = await self._create_question_annotation(
                        q_annotation, survey_id, annotator_id
                    )
                    created_annotations["question_annotations"].append(annotation.id)
                    created_annotations["total_created"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to create question annotation for {q_annotation.get('question_id', 'unknown')}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    created_annotations["errors"].append(error_msg)
            
            # Create section annotations
            for s_annotation in evaluation_result.section_annotations:
                try:
                    annotation = await self._create_section_annotation(
                        s_annotation, survey_id, annotator_id
                    )
                    created_annotations["section_annotations"].append(annotation.id)
                    created_annotations["total_created"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to create section annotation for {s_annotation.get('section_id', 'unknown')}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    created_annotations["errors"].append(error_msg)
            
            # Commit all changes
            self.db_session.commit()
            
            logger.info(f"✅ Created {created_annotations['total_created']} AI annotations for survey {survey_id}")
            
            return created_annotations
            
        except Exception as e:
            logger.error(f"❌ Error creating AI annotations: {str(e)}")
            self.db_session.rollback()
            raise
    
    async def _create_question_annotation(
        self, 
        q_data: Dict[str, Any], 
        survey_id: str, 
        annotator_id: str
    ) -> QuestionAnnotation:
        """Create a single question annotation from evaluation data"""
        
        # Create new annotation (cleanup already handled)
        # Make question_id unique across surveys by prefixing with survey_id
        unique_question_id = f"{survey_id}_{q_data.get('question_id', '')}"
        annotation = QuestionAnnotation(
            question_id=unique_question_id,
            survey_id=survey_id,
            required=True,
            quality=q_data.get("quality", 3),
            relevant=q_data.get("relevant", 3),
            methodological_rigor=q_data.get("methodological_rigor", 3),
            content_validity=q_data.get("content_validity", 3),
            respondent_experience=q_data.get("respondent_experience", 3),
            analytical_value=q_data.get("analytical_value", 3),
            business_impact=q_data.get("business_impact", 3),
            comment=q_data.get("comment", ""),
            annotator_id=annotator_id,
            labels={},  # Empty labels for AI-generated annotations
            ai_generated=True,
            ai_confidence=q_data.get("ai_confidence", 0.8),
            human_verified=False,
            generation_timestamp=datetime.now()
        )
        
        self.db_session.add(annotation)
        self.db_session.flush()  # Get the ID
        
        logger.info(f"✅ Created new question annotation for {q_data.get('question_id')}")
        return annotation
    
    async def _create_section_annotation(
        self, 
        s_data: Dict[str, Any], 
        survey_id: str, 
        annotator_id: str
    ) -> SectionAnnotation:
        """Create a single section annotation from evaluation data"""
        
        # Create new annotation (cleanup already handled)
        # Create unique section_id by using a smaller hash
        import hashlib
        section_id_str = str(s_data.get("section_id", 0))
        hash_str = hashlib.md5(f"{survey_id}_{section_id_str}".encode()).hexdigest()[:6]
        unique_section_id = int(hash_str, 16)  # Convert hex to int (smaller range)
        annotation = SectionAnnotation(
            section_id=unique_section_id,
            survey_id=survey_id,
            quality=s_data.get("quality", 3),
            relevant=s_data.get("relevant", 3),
            methodological_rigor=s_data.get("methodological_rigor", 3),
            content_validity=s_data.get("content_validity", 3),
            respondent_experience=s_data.get("respondent_experience", 3),
            analytical_value=s_data.get("analytical_value", 3),
            business_impact=s_data.get("business_impact", 3),
            comment=s_data.get("comment", ""),
            annotator_id=annotator_id,
            labels={},  # Empty labels for AI-generated annotations
            ai_generated=True,
            ai_confidence=s_data.get("ai_confidence", 0.8),
            human_verified=False,
            generation_timestamp=datetime.now()
        )
        
        self.db_session.add(annotation)
        self.db_session.flush()  # Get the ID
        
        logger.info(f"✅ Created new section annotation for {s_data.get('section_id')}")
        return annotation
    
    def get_ai_annotations_for_survey(self, survey_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all AI-generated annotations for a survey"""
        try:
            # Get question annotations
            question_annotations = self.db_session.query(QuestionAnnotation).filter(
                QuestionAnnotation.survey_id == survey_id,
                QuestionAnnotation.ai_generated == True
            ).all()
            
            # Get section annotations
            section_annotations = self.db_session.query(SectionAnnotation).filter(
                SectionAnnotation.survey_id == survey_id,
                SectionAnnotation.ai_generated == True
            ).all()
            
            return {
                "question_annotations": [
                    {
                        "id": qa.id,
                        "question_id": qa.question_id,
                        "quality": qa.quality,
                        "relevant": qa.relevant,
                        "content_validity": qa.content_validity,
                        "methodological_rigor": qa.methodological_rigor,
                        "respondent_experience": qa.respondent_experience,
                        "analytical_value": qa.analytical_value,
                        "business_impact": qa.business_impact,
                        "ai_confidence": float(qa.ai_confidence) if qa.ai_confidence else None,
                        "human_verified": qa.human_verified,
                        "comment": qa.comment,
                        "created_at": qa.created_at.isoformat() if qa.created_at else None
                    }
                    for qa in question_annotations
                ],
                "section_annotations": [
                    {
                        "id": sa.id,
                        "section_id": sa.section_id,
                        "quality": sa.quality,
                        "relevant": sa.relevant,
                        "content_validity": sa.content_validity,
                        "methodological_rigor": sa.methodological_rigor,
                        "respondent_experience": sa.respondent_experience,
                        "analytical_value": sa.analytical_value,
                        "business_impact": sa.business_impact,
                        "ai_confidence": float(sa.ai_confidence) if sa.ai_confidence else None,
                        "human_verified": sa.human_verified,
                        "comment": sa.comment,
                        "created_at": sa.created_at.isoformat() if sa.created_at else None
                    }
                    for sa in section_annotations
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting AI annotations: {str(e)}")
            return {"question_annotations": [], "section_annotations": []}
    
    def mark_annotation_as_verified(self, annotation_id: int, annotation_type: str) -> bool:
        """Mark an AI-generated annotation as human verified"""
        try:
            if annotation_type == "question":
                annotation = self.db_session.query(QuestionAnnotation).filter(
                    QuestionAnnotation.id == annotation_id
                ).first()
            elif annotation_type == "section":
                annotation = self.db_session.query(SectionAnnotation).filter(
                    SectionAnnotation.id == annotation_id
                ).first()
            else:
                logger.error(f"❌ Invalid annotation type: {annotation_type}")
                return False
            
            if annotation:
                annotation.human_verified = True
                annotation.updated_at = datetime.now()
                self.db_session.commit()
                logger.info(f"✅ Marked {annotation_type} annotation {annotation_id} as verified")
                return True
            else:
                logger.error(f"❌ Annotation {annotation_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error marking annotation as verified: {str(e)}")
            self.db_session.rollback()
            return False
