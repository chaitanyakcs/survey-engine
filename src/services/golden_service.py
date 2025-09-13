from sqlalchemy.orm import Session
from src.database import GoldenRFQSurveyPair
from src.services.embedding_service import EmbeddingService
from typing import Dict, List, Any, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class GoldenService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    def list_golden_pairs(self, skip: int = 0, limit: int = 100) -> List[GoldenRFQSurveyPair]:
        """
        List golden standard pairs with pagination
        """
        return (
            self.db.query(GoldenRFQSurveyPair)
            .order_by(GoldenRFQSurveyPair.usage_count.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    async def create_golden_pair(
        self,
        rfq_text: str,
        survey_json: Dict[str, Any],
        title: Optional[str] = None,
        methodology_tags: Optional[List[str]] = None,
        industry_category: Optional[str] = None,
        research_goal: Optional[str] = None,
        quality_score: float = 1.0
    ) -> GoldenRFQSurveyPair:
        """
        Create new golden standard pair with embedding generation
        """
        logger.info(f"🏆 [GoldenService] Starting golden pair creation")
        logger.info(f"📝 [GoldenService] Input data - title: {title}, rfq_text_length: {len(rfq_text) if rfq_text else 0}")
        logger.info(f"📊 [GoldenService] Survey JSON type: {type(survey_json)}")
        logger.info(f"📊 [GoldenService] Survey JSON keys: {list(survey_json.keys()) if isinstance(survey_json, dict) else 'Not a dict'}")
        logger.info(f"🏷️ [GoldenService] Methodology tags: {methodology_tags}")
        logger.info(f"🏭 [GoldenService] Industry category: {industry_category}")
        logger.info(f"🎯 [GoldenService] Research goal: {research_goal}")
        logger.info(f"⭐ [GoldenService] Quality score: {quality_score}")
        
        try:
            logger.info(f"🧠 [GoldenService] Generating embedding for RFQ text")
            # Generate embedding for RFQ text
            rfq_embedding = await self.embedding_service.get_embedding(rfq_text)
            logger.info(f"✅ [GoldenService] Embedding generated successfully, length: {len(rfq_embedding) if rfq_embedding else 0}")
            
            logger.info(f"💾 [GoldenService] Creating GoldenRFQSurveyPair record")
            # Create golden pair record
            golden_pair = GoldenRFQSurveyPair(
                title=title,
                rfq_text=rfq_text,
                rfq_embedding=rfq_embedding,
                survey_json=survey_json,
                methodology_tags=methodology_tags,
                industry_category=industry_category,
                research_goal=research_goal,
                quality_score=quality_score
            )
            
            logger.info(f"💾 [GoldenService] Adding golden pair to database")
            self.db.add(golden_pair)
            
            logger.info(f"💾 [GoldenService] Committing transaction")
            self.db.commit()
            
            logger.info(f"💾 [GoldenService] Refreshing golden pair from database")
            self.db.refresh(golden_pair)
            
            logger.info(f"✅ [GoldenService] Golden pair created successfully with ID: {golden_pair.id}")
            logger.info(f"📋 [GoldenService] Created pair details - title: {golden_pair.title}, quality_score: {golden_pair.quality_score}")
            
            return golden_pair
            
        except Exception as e:
            logger.error(f"❌ [GoldenService] Failed to create golden pair: {str(e)}", exc_info=True)
            logger.error(f"❌ [GoldenService] Rolling back transaction")
            self.db.rollback()
            raise Exception(f"Failed to create golden pair: {str(e)}")
    
    def update_golden_pair(
        self,
        golden_id: UUID,
        rfq_text: str,
        survey_json: Dict[str, Any],
        methodology_tags: Optional[List[str]] = None,
        industry_category: Optional[str] = None,
        research_goal: Optional[str] = None,
        quality_score: Optional[float] = None
    ) -> GoldenRFQSurveyPair:
        """
        Update existing golden pair
        """
        try:
            golden_pair = self.db.query(GoldenRFQSurveyPair).filter(
                GoldenRFQSurveyPair.id == golden_id
            ).first()
            
            if not golden_pair:
                raise ValueError("Golden pair not found")
            
            # Update fields
            golden_pair.rfq_text = rfq_text
            golden_pair.survey_json = survey_json
            golden_pair.methodology_tags = methodology_tags or []
            golden_pair.industry_category = industry_category or "General"
            golden_pair.research_goal = research_goal or "Market Research"
            
            if quality_score is not None:
                golden_pair.quality_score = quality_score
            
            self.db.commit()
            self.db.refresh(golden_pair)
            
            return golden_pair
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update golden pair: {str(e)}")
    
    def delete_golden_pair(self, golden_id: UUID) -> bool:
        """
        Delete a golden pair by ID (including its vector embedding)
        
        Note: Since we use pgvector, the vector embedding is stored in the same
        PostgreSQL table as the metadata, so deleting the record automatically
        removes the vector from the vector database as well.
        """
        try:
            golden_pair = self.db.query(GoldenRFQSurveyPair).filter(
                GoldenRFQSurveyPair.id == golden_id
            ).first()
            
            if not golden_pair:
                return False
            
            # Log what we're deleting for debugging
            try:
                if golden_pair.rfq_embedding is not None:
                    # Handle both NumPy arrays and pgvector objects
                    if hasattr(golden_pair.rfq_embedding, '__len__'):
                        embedding_dim = len(golden_pair.rfq_embedding)
                    else:
                        embedding_dim = 'Unknown'
                else:
                    embedding_dim = 'None'
                print(f"Deleting golden pair {golden_id} with embedding dimension: {embedding_dim}")
            except Exception as e:
                print(f"Deleting golden pair {golden_id} with embedding (dimension check failed: {str(e)})")
            
            # Delete the record (this also removes the vector from pgvector)
            self.db.delete(golden_pair)
            self.db.commit()
            
            print(f"Successfully deleted golden pair {golden_id} and its vector embedding")
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete golden pair: {str(e)}")
    
    def validate_golden_pair(
        self,
        golden_id: UUID,
        expert_validation: bool,
        quality_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Expert validation and quality scoring of golden pair
        """
        try:
            golden_pair = self.db.query(GoldenRFQSurveyPair).filter(
                GoldenRFQSurveyPair.id == golden_id
            ).first()
            
            if not golden_pair:
                raise ValueError("Golden pair not found")
            
            # Update quality score if provided
            if quality_score is not None:
                golden_pair.quality_score = quality_score  # type: ignore
            
            # TODO: Add expert validation tracking
            # Could add fields like validated_by, validation_date, validation_notes
            
            self.db.commit()
            
            return {
                "golden_id": str(golden_pair.id),
                "expert_validation": expert_validation,
                "quality_score": float(golden_pair.quality_score) if golden_pair.quality_score else None,
                "validation_status": "validated" if expert_validation else "rejected",
                "validated_at": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to validate golden pair: {str(e)}")
    
    def get_golden_pair_stats(self) -> Dict[str, Any]:
        """
        Get statistics about golden pairs usage and performance
        """
        try:
            total_pairs = self.db.query(GoldenRFQSurveyPair).count()
            
            # Get usage stats
            usage_stats = self.db.query(
                GoldenRFQSurveyPair.usage_count
            ).all()
            
            total_usage = sum(stat[0] for stat in usage_stats)
            avg_usage = total_usage / len(usage_stats) if usage_stats else 0
            
            # Get quality stats
            quality_stats = self.db.query(
                GoldenRFQSurveyPair.quality_score
            ).filter(
                GoldenRFQSurveyPair.quality_score.isnot(None)
            ).all()
            
            avg_quality = (
                sum(float(stat[0]) for stat in quality_stats) / len(quality_stats)
                if quality_stats else 0
            )
            
            return {
                "total_golden_pairs": total_pairs,
                "total_usage": total_usage,
                "average_usage_per_pair": round(avg_usage, 2),
                "average_quality_score": round(avg_quality, 2),
                "pairs_with_quality_scores": len(quality_stats)
            }
            
        except Exception as e:
            raise Exception(f"Failed to get golden pair stats: {str(e)}")