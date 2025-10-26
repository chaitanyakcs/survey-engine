"""
Golden Similarity Analysis Service

Provides comprehensive similarity analysis between generated surveys
and golden examples, with industry and methodology-specific insights.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from src.services.embedding_service import EmbeddingService
from src.services.validation_service import ValidationService
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class GoldenSimilarityAnalysisService:
    """Service for analyzing survey similarity to golden examples"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.embedding_service = EmbeddingService()
        self.validation_service = ValidationService(db_session) if db_session else None

    async def analyze_survey_similarity(
        self,
        survey: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        rfq_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main analysis orchestrator - returns comprehensive similarity analysis
        
        Args:
            survey: Generated survey JSON
            golden_examples: List of golden examples used during generation
            rfq_context: Optional RFQ context (industry, methodologies, etc.)
            
        Returns:
            Comprehensive similarity analysis with best matches and breakdowns
        """
        try:
            logger.info(f"🔍 [GoldenSimilarityAnalysis] Starting analysis for survey with {len(golden_examples)} golden examples")
            
            if not golden_examples:
                logger.warning("⚠️ [GoldenSimilarityAnalysis] No golden examples provided")
                return self._create_empty_analysis()
            
            # Extract RFQ context
            industry = rfq_context.get('industry_category') if rfq_context else None
            methodologies = rfq_context.get('methodology_tags', []) if rfq_context else []
            
            # Calculate individual similarities
            individual_similarities = await self.calculate_individual_similarities(survey, golden_examples)
            
            # Calculate average similarity
            overall_average = sum(s['similarity'] for s in individual_similarities) / len(individual_similarities) if individual_similarities else 0.0
            
            # Find best matches
            best_match = self._find_best_match(individual_similarities)
            best_industry_match = self.find_best_industry_match(individual_similarities, industry)
            best_methodology_match = self.find_best_methodology_match(individual_similarities, methodologies)
            best_combined_match = self.find_best_combined_match(individual_similarities, industry, methodologies)
            
            # Calculate methodology and industry alignment
            methodology_alignment = self.calculate_methodology_alignment(survey, golden_examples, methodologies)
            industry_alignment = self.calculate_industry_alignment(survey, golden_examples, industry)
            
            analysis = {
                "overall_average": round(overall_average, 3),
                "best_match": best_match,
                "best_industry_match": best_industry_match,
                "best_methodology_match": best_methodology_match,
                "best_combined_match": best_combined_match,
                "individual_similarities": individual_similarities,
                "methodology_alignment": methodology_alignment,
                "industry_alignment": industry_alignment,
                "total_golden_examples_analyzed": len(individual_similarities)
            }
            
            logger.info(f"✅ [GoldenSimilarityAnalysis] Analysis complete: avg={overall_average:.3f}, best={best_match.get('similarity', 0):.3f}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ [GoldenSimilarityAnalysis] Analysis failed: {str(e)}", exc_info=True)
            return self._create_empty_analysis()

    async def calculate_individual_similarities(
        self,
        survey: Dict[str, Any],
        golden_examples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate similarity score for each golden example
        
        Args:
            survey: Generated survey JSON
            golden_examples: List of golden examples
            
        Returns:
            List of individual similarity scores with metadata
        """
        similarities = []
        
        try:
            # Generate embedding for the generated survey
            survey_text = self._survey_to_text(survey)
            survey_embedding = await self.embedding_service.get_embedding(survey_text)
            
            for example in golden_examples:
                try:
                    # Extract metadata
                    golden_id = example.get("id")
                    golden_title = example.get("title", "Unknown")
                    methodology_tags = example.get("methodology_tags", [])
                    industry_category = example.get("industry_category")
                    
                    # Generate embedding for golden survey
                    golden_survey = example.get("survey_json", {})
                    golden_text = self._survey_to_text(golden_survey)
                    golden_embedding = await self.embedding_service.get_embedding(golden_text)
                    
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(survey_embedding, golden_embedding)
                    
                    similarities.append({
                        "golden_id": str(golden_id),
                        "title": golden_title,
                        "similarity": round(similarity, 3),
                        "methodology_tags": methodology_tags or [],
                        "industry_category": industry_category,
                        "quality_score": float(example.get("quality_score", 0)) if example.get("quality_score") else None,
                        "human_verified": example.get("human_verified", False)
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ [GoldenSimilarityAnalysis] Failed to calculate similarity for golden example {example.get('id')}: {e}")
                    continue
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities
            
        except Exception as e:
            logger.error(f"❌ [GoldenSimilarityAnalysis] Failed to calculate individual similarities: {str(e)}")
            return []

    def find_best_industry_match(
        self,
        individual_similarities: List[Dict[str, Any]],
        target_industry: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Find best matching golden example for the same industry
        
        Args:
            individual_similarities: List of similarity results
            target_industry: Target industry to match
            
        Returns:
            Best industry match with enhanced metadata
        """
        if not target_industry:
            return None
        
        # Filter for same industry
        industry_matches = [
            s for s in individual_similarities
            if s.get('industry_category') and 
            self._is_same_industry(target_industry, s.get('industry_category'))
        ]
        
        if not industry_matches:
            return None
        
        best = industry_matches[0]  # Already sorted by similarity
        return {
            **best,
            "match_type": "industry",
            "match_reason": f"Best match for '{target_industry}' industry"
        }

    def find_best_methodology_match(
        self,
        individual_similarities: List[Dict[str, Any]],
        target_methodologies: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Find best matching golden example for the same methodologies
        
        Args:
            individual_similarities: List of similarity results
            target_methodologies: Target methodologies to match
            
        Returns:
            Best methodology match with enhanced metadata
        """
        if not target_methodologies:
            return None
        
        # Score each golden example by methodology overlap
        scored_matches = []
        for sim in individual_similarities:
            golden_methodologies = sim.get('methodology_tags', [])
            overlap_count = sum(1 for m in target_methodologies if m in golden_methodologies)
            overlap_ratio = overlap_count / len(target_methodologies) if target_methodologies else 0
            
            if overlap_ratio > 0:
                scored_matches.append({
                    **sim,
                    "methodology_overlap": round(overlap_ratio, 3),
                    "combined_score": round(sim['similarity'] * overlap_ratio, 3)
                })
        
        if not scored_matches:
            return None
        
        # Sort by combined score (similarity weighted by methodology overlap)
        scored_matches.sort(key=lambda x: x['combined_score'], reverse=True)
        best = scored_matches[0]
        
        return {
            **best,
            "match_type": "methodology",
            "match_reason": f"Best match for methodologies: {', '.join(target_methodologies)}",
            "methodologies_in_common": [m for m in target_methodologies if m in best['methodology_tags']]
        }

    def find_best_combined_match(
        self,
        individual_similarities: List[Dict[str, Any]],
        target_industry: Optional[str],
        target_methodologies: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Find best overall match considering both industry and methodology
        
        Args:
            individual_similarities: List of similarity results
            target_industry: Target industry
            target_methodologies: Target methodologies
            
        Returns:
            Best combined match with enhanced metadata
        """
        scored_matches = []
        
        for sim in individual_similarities:
            combined_score = sim['similarity']
            match_components = []
            
            # Check industry match
            industry_score = 0.0
            if target_industry and sim.get('industry_category'):
                if self._is_same_industry(target_industry, sim.get('industry_category')):
                    industry_score = 0.5
                    match_components.append(f"Industry: {sim['industry_category']}")
            
            # Check methodology match
            methodology_score = 0.0
            if target_methodologies:
                golden_methodologies = sim.get('methodology_tags', [])
                overlap = sum(1 for m in target_methodologies if m in golden_methodologies)
                methodology_score = (overlap / len(target_methodologies)) * 0.5 if target_methodologies else 0
                if overlap > 0:
                    match_components.append(f"Methodologies: {', '.join(set(target_methodologies) & set(golden_methodologies))}")
            
            combined_score = round(sim['similarity'] + industry_score + methodology_score, 3)
            
            scored_matches.append({
                **sim,
                "combined_score": combined_score,
                "match_components": match_components
            })
        
        if not scored_matches:
            return None
        
        # Sort by combined score
        scored_matches.sort(key=lambda x: x['combined_score'], reverse=True)
        best = scored_matches[0]
        
        return {
            **best,
            "match_type": "combined",
            "match_reason": "Best overall match considering industry and methodology alignment"
        }

    def calculate_methodology_alignment(
        self,
        survey: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        target_methodologies: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate methodology-specific alignment scores
        
        Args:
            survey: Generated survey JSON
            golden_examples: List of golden examples
            target_methodologies: Target methodologies
            
        Returns:
            Methodology alignment analysis
        """
        if not target_methodologies:
            return {"score": 0.0, "methodology_details": []}
        
        alignment_scores = []
        
        for methodology in target_methodologies:
            # Find golden examples using this methodology
            methodology_examples = [
                ex for ex in golden_examples
                if ex.get('methodology_tags') and methodology in ex.get('methodology_tags', [])
            ]
            
            if methodology_examples:
                # Calculate average similarity to these examples
                avg_similarity = 0.0
                try:
                    similarities = []
                    for ex in methodology_examples[:5]:  # Limit to top 5 for performance
                        # Use simplified similarity check
                        similarity = self._calculate_simple_similarity(survey, ex.get('survey_json', {}))
                        similarities.append(similarity)
                    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
                except Exception as e:
                    logger.warning(f"Failed to calculate methodology alignment for {methodology}: {e}")
                
                alignment_scores.append({
                    "methodology": methodology,
                    "score": round(avg_similarity, 3),
                    "golden_examples_count": len(methodology_examples)
                })
        
        overall_score = sum(s['score'] for s in alignment_scores) / len(alignment_scores) if alignment_scores else 0.0
        
        return {
            "score": round(overall_score, 3),
            "methodology_details": alignment_scores
        }

    def calculate_industry_alignment(
        self,
        survey: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        target_industry: Optional[str]
    ) -> Dict[str, Any]:
        """
        Calculate industry-specific alignment scores
        
        Args:
            survey: Generated survey JSON
            golden_examples: List of golden examples
            target_industry: Target industry
            
        Returns:
            Industry alignment analysis
        """
        if not target_industry:
            return {"score": 0.0, "industry": "unknown"}
        
        # Find golden examples for the same industry
        industry_examples = [
            ex for ex in golden_examples
            if ex.get('industry_category') and self._is_same_industry(target_industry, ex.get('industry_category'))
        ]
        
        if not industry_examples:
            return {"score": 0.0, "industry": target_industry, "note": "No industry-specific examples found"}
        
        # Calculate average similarity to industry examples
        try:
            similarities = []
            for ex in industry_examples[:10]:  # Limit to top 10 for performance
                similarity = self._calculate_simple_similarity(survey, ex.get('survey_json', {}))
                similarities.append(similarity)
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
            
            return {
                "score": round(avg_similarity, 3),
                "industry": target_industry,
                "golden_examples_count": len(industry_examples)
            }
            
        except Exception as e:
            logger.warning(f"Failed to calculate industry alignment: {e}")
            return {"score": 0.0, "industry": target_industry}

    def _find_best_match(self, individual_similarities: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find overall best matching golden example"""
        if not individual_similarities:
            return None
        
        best = individual_similarities[0]  # Already sorted by similarity
        return {
            **best,
            "match_type": "overall",
            "match_reason": "Best overall semantic similarity"
        }

    def _calculate_simple_similarity(self, survey1: Dict[str, Any], survey2: Dict[str, Any]) -> float:
        """Calculate simple text-based similarity without embeddings"""
        try:
            text1 = self._survey_to_text(survey1)
            text2 = self._survey_to_text(survey2)
            
            # Use SequenceMatcher for simple similarity
            similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
            return similarity
            
        except Exception as e:
            logger.warning(f"Failed to calculate simple similarity: {e}")
            return 0.0

    def _is_same_industry(self, industry1: str, industry2: str) -> bool:
        """Check if two industries match (with fuzzy matching)"""
        if not industry1 or not industry2:
            return False
        
        i1_lower = industry1.lower()
        i2_lower = industry2.lower()
        
        # Exact match
        if i1_lower == i2_lower:
            return True
        
        # Fuzzy match with threshold
        similarity = SequenceMatcher(None, i1_lower, i2_lower).ratio()
        return similarity > 0.8

    def _survey_to_text(self, survey: Dict[str, Any]) -> str:
        """Convert survey JSON to text for comparison"""
        try:
            text_parts = []
            
            # Add title
            if "title" in survey:
                text_parts.append(f"Title: {survey['title']}")
            
            # Add description
            if "description" in survey:
                text_parts.append(f"Description: {survey['description']}")
            
            # Handle sections format
            if "sections" in survey and isinstance(survey["sections"], list):
                for section in survey["sections"]:
                    if isinstance(section, dict):
                        section_title = section.get("title", "")
                        text_parts.append(f"Section: {section_title}")
                        
                        if "questions" in section and isinstance(section["questions"], list):
                            for question in section["questions"]:
                                if isinstance(question, dict) and "text" in question:
                                    text_parts.append(f"Q: {question['text']}")
            
            # Handle legacy questions format
            elif "questions" in survey and isinstance(survey["questions"], list):
                for question in survey["questions"]:
                    if isinstance(question, dict) and "text" in question:
                        text_parts.append(f"Q: {question['text']}")
            
            return " ".join(text_parts)
            
        except Exception as e:
            logger.warning(f"Failed to convert survey to text: {e}")
            return ""

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Failed to calculate cosine similarity: {e}")
            return 0.0

    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis structure"""
        return {
            "overall_average": 0.0,
            "best_match": None,
            "best_industry_match": None,
            "best_methodology_match": None,
            "best_combined_match": None,
            "individual_similarities": [],
            "methodology_alignment": {"score": 0.0, "methodology_details": []},
            "industry_alignment": {"score": 0.0, "industry": "unknown"},
            "total_golden_examples_analyzed": 0
        }

