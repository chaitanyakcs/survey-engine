from sqlalchemy.orm import Session
from src.database import GoldenRFQSurveyPair
from src.database.models import Survey
from src.services.embedding_service import EmbeddingService
from typing import Dict, List, Any, Optional
from uuid import UUID
from src.config import settings
from datetime import datetime
import replicate
import json
import logging

logger = logging.getLogger(__name__)


class GoldenService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        # Initialize Replicate client
        if not settings.replicate_api_token:
            raise ValueError("REPLICATE_API_TOKEN is required but not set")
        self.replicate_client = replicate.Client(api_token=settings.replicate_api_token)
    
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

    async def generate_rfq_from_survey(
        self,
        survey_json: Dict[str, Any],
        methodology_tags: Optional[List[str]] = None,
        industry_category: Optional[str] = None,
        research_goal: Optional[str] = None
    ) -> str:
        """
        Generate RFQ text from a survey JSON using LLM
        """
        logger.info(f"🤖 [GoldenService] Generating RFQ from survey")
        logger.info(f"📊 [GoldenService] Survey has {len(survey_json.get('questions', []))} questions")
        logger.info(f"🏷️ [GoldenService] Methodology tags: {methodology_tags}")
        logger.info(f"🏭 [GoldenService] Industry category: {industry_category}")
        logger.info(f"🎯 [GoldenService] Research goal: {research_goal}")

        try:
            # Extract key information from survey
            survey_title = survey_json.get('title', 'Survey')
            survey_description = survey_json.get('description', '')
            questions = survey_json.get('questions', [])

            # Build context for RFQ generation
            question_summary = []
            for i, q in enumerate(questions[:5]):  # Limit to first 5 questions for context
                q_text = q.get('text', f'Question {i+1}')
                q_type = q.get('type', 'text')
                question_summary.append(f"- {q_text[:100]}... (Type: {q_type})")

            methodology_text = ", ".join(methodology_tags) if methodology_tags else "general survey research"

            # Create prompt for RFQ generation
            prompt = f"""You are a market research professional writing an RFQ (Request for Quotation) for a survey project.
Based on the provided survey structure, generate a realistic and detailed RFQ that a client might send to a research vendor.

SURVEY INFORMATION:
Title: {survey_title}
Description: {survey_description}
Industry: {industry_category or 'Not specified'}
Research Goal: {research_goal or 'Market research'}
Methodology: {methodology_text}

SURVEY STRUCTURE ({len(questions)} questions total):
{chr(10).join(question_summary[:5])}

Generate a realistic RFQ that includes:
1. Project background and objectives
2. Target audience/market segment
3. Key research questions to address
4. Methodology requirements (mention {methodology_text})
5. Timeline expectations
6. Sample size requirements
7. Deliverables expected

Write in a professional, business tone as if from a client company seeking research services. Make it specific enough to generate the survey shown above, but realistic for a business context.

RFQ Text:"""

            logger.info(f"🚀 [GoldenService] Calling Replicate API for RFQ generation")

            output = await self.replicate_client.async_run(
                settings.generation_model,
                input={
                    "prompt": prompt,
                    "temperature": 0.3,  # Lower temperature for more consistent, professional output
                    "max_tokens": 1500,
                    "top_p": 0.9
                }
            )

            # Extract text from output
            if isinstance(output, list):
                generated_rfq = "".join(str(item) for item in output)
            else:
                generated_rfq = str(output)

            # Clean up the generated RFQ
            generated_rfq = generated_rfq.strip()

            # Remove any unwanted prefixes
            if generated_rfq.startswith("RFQ Text:"):
                generated_rfq = generated_rfq[9:].strip()

            logger.info(f"✅ [GoldenService] RFQ generated successfully, length: {len(generated_rfq)}")
            logger.info(f"📝 [GoldenService] Generated RFQ preview: {generated_rfq[:200]}...")

            return generated_rfq

        except Exception as e:
            logger.error(f"❌ [GoldenService] Failed to generate RFQ: {str(e)}", exc_info=True)
            # Return a fallback RFQ if generation fails
            fallback_rfq = f"""We need market research for {industry_category or 'our industry'} focusing on {research_goal or 'market insights'}.
The research should use {methodology_text} methodology and cover the key areas addressed in our survey requirements.
Target audience: {survey_json.get('metadata', {}).get('target_audience', 'General market')}.
We need a comprehensive survey with approximately {len(questions)} questions to gather actionable insights."""

            logger.info(f"🔄 [GoldenService] Using fallback RFQ due to generation error")
            return fallback_rfq
    
    async def create_golden_pair(
        self,
        rfq_text: Optional[str],
        survey_json: Dict[str, Any],
        title: Optional[str] = None,
        methodology_tags: Optional[List[str]] = None,
        industry_category: Optional[str] = None,
        research_goal: Optional[str] = None,
        quality_score: Optional[float] = None,
        auto_generate_rfq: bool = False
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
            # Handle RFQ text - generate if requested, or allow empty if auto-generate is enabled
            if not rfq_text or not rfq_text.strip():
                if auto_generate_rfq:
                    logger.info(f"🤖 [GoldenService] RFQ text is missing and auto_generate_rfq is True, generating from survey")
                    rfq_text = await self.generate_rfq_from_survey(
                        survey_json=survey_json,
                        methodology_tags=methodology_tags,
                        industry_category=industry_category,
                        research_goal=research_goal
                    )
                    logger.info(f"✅ [GoldenService] RFQ generated, length: {len(rfq_text)}")
                else:
                    # Allow creating golden examples without RFQ text
                    logger.info(f"📝 [GoldenService] No RFQ text provided and auto_generate_rfq is False - creating golden example without RFQ")
                    rfq_text = ""  # Use empty string instead of raising error
            else:
                logger.info(f"📝 [GoldenService] Using provided RFQ text")

            logger.info(f"🧠 [GoldenService] Generating embedding for RFQ text")
            # Generate embedding for RFQ text
            rfq_embedding = await self.embedding_service.get_embedding(rfq_text)
            logger.info(f"✅ [GoldenService] Embedding generated successfully, length: {len(rfq_embedding) if rfq_embedding else 0}")

            logger.info(f"💾 [GoldenService] Creating GoldenRFQSurveyPair record")
            # Create golden pair record with default quality score if not provided
            final_quality_score = quality_score if quality_score is not None else 1.0
            logger.info(f"⭐ [GoldenService] Using quality score: {final_quality_score}")
            
            # Create the golden pair first to get the ID
            golden_pair = GoldenRFQSurveyPair(
                title=title,
                rfq_text=rfq_text,
                rfq_embedding=rfq_embedding,
                survey_json=survey_json,
                methodology_tags=methodology_tags,
                industry_category=industry_category,
                research_goal=research_goal,
                quality_score=final_quality_score,
                human_verified=True  # Manually created examples are human-verified
            )
            
            logger.info(f"💾 [GoldenService] Adding golden pair to database")
            self.db.add(golden_pair)
            
            # Commit to get the golden_pair.id
            self.db.commit()
            self.db.refresh(golden_pair)
            
            # Generate survey_id for the reference example (use actual UUID)
            survey_id = golden_pair.id  # Use the same UUID as the golden pair
            logger.info(f"🔍 [GoldenService] Using golden pair ID as survey_id for reference example: {survey_id}")
            
            # Add survey_id to the survey_json for consistency
            if isinstance(survey_json, dict):
                survey_json["survey_id"] = str(survey_id)  # Convert UUID to string for JSON
                
                # Ensure survey JSON has a title (use golden pair title if survey JSON doesn't have one)
                if not survey_json.get('title') and title:
                    survey_json["title"] = title
                    logger.info(f"📝 [GoldenService] Added title to survey JSON: {title}")
                
                # Update the golden pair with the modified survey_json
                golden_pair.survey_json = survey_json
                self.db.commit()
            
            # Create survey record for annotation support
            logger.info(f"💾 [GoldenService] Creating survey record for reference example")
            reference_survey = Survey(
                id=survey_id,  # Use the same UUID as golden pair
                rfq_id=None,  # Reference examples don't have RFQ
                status="reference",  # Special status for reference examples
                raw_output=survey_json,
                final_output=survey_json,
                created_at=datetime.now()
            )
            
            self.db.add(reference_survey)
            self.db.commit()
            
            logger.info(f"✅ [GoldenService] Golden pair created successfully with ID: {golden_pair.id}")
            logger.info(f"✅ [GoldenService] Survey record created with ID: {survey_id}")
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
            
            # Generate survey_id for the reference example (use actual UUID)
            survey_id = golden_pair.id  # Use the same UUID as the golden pair
            
            # Add survey_id to the survey_json for consistency
            if isinstance(survey_json, dict):
                survey_json["survey_id"] = str(survey_id)  # Convert UUID to string for JSON
            
            # Update fields
            golden_pair.rfq_text = rfq_text
            golden_pair.survey_json = survey_json
            golden_pair.methodology_tags = methodology_tags or []
            golden_pair.industry_category = industry_category or "General"
            golden_pair.research_goal = research_goal or "Market Research"
            
            if quality_score is not None:
                golden_pair.quality_score = quality_score
            
            # Update or create the corresponding survey record
            existing_survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
            if existing_survey:
                # Update existing survey record
                existing_survey.raw_output = survey_json
                existing_survey.final_output = survey_json
            else:
                # Create new survey record
                reference_survey = Survey(
                    id=survey_id,
                    rfq_id=None,
                    status="reference",
                    raw_output=survey_json,
                    final_output=survey_json,
                    created_at=datetime.now()
                )
                self.db.add(reference_survey)
            
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
            
            # Also delete the corresponding survey record
            survey_id = golden_id  # Use the same UUID as the golden pair
            survey_record = self.db.query(Survey).filter(Survey.id == survey_id).first()
            if survey_record:
                self.db.delete(survey_record)
                logger.info(f"🗑️ [GoldenService] Deleted survey record: {survey_id}")
            
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