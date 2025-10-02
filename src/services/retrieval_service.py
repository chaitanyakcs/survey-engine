from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.models import GoldenRFQSurveyPair
from typing import List, Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db
    
    async def retrieve_golden_pairs(
        self,
        embedding: List[float],
        methodology_tags: Optional[List[str]] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Tier 1: Retrieve exact golden RFQ-survey pairs using semantic similarity
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 [RetrievalService] Starting golden pairs retrieval with embedding dimension: {len(embedding)}")
        logger.info(f"🔍 [RetrievalService] Methodology tags filter: {methodology_tags}")
        logger.info(f"🔍 [RetrievalService] Limit: {limit}")
        
        try:
            # Use ORM query with proper pgvector operations
            from pgvector.sqlalchemy import Vector
            
            # Base query with cosine distance (smaller is more similar)
            query = self.db.query(
                GoldenRFQSurveyPair.id,
                GoldenRFQSurveyPair.rfq_text,
                GoldenRFQSurveyPair.survey_json,
                GoldenRFQSurveyPair.methodology_tags,
                GoldenRFQSurveyPair.industry_category,
                GoldenRFQSurveyPair.research_goal,
                GoldenRFQSurveyPair.quality_score,
                GoldenRFQSurveyPair.rfq_embedding.cosine_distance(embedding).label('similarity')
            ).filter(GoldenRFQSurveyPair.rfq_embedding.is_not(None))
            
            # Add methodology filter if provided
            if methodology_tags:
                query = query.filter(GoldenRFQSurveyPair.methodology_tags.overlap(methodology_tags))
            
            # Order by similarity (cosine distance - smaller is more similar)
            query = query.order_by('similarity').limit(limit)
            
            rows = query.all()
            logger.info(f"🔍 [RetrievalService] Database query executed. Found {len(rows)} golden pairs")
            
            golden_examples = []
            for i, row in enumerate(rows):
                logger.info(f"📋 [RetrievalService] Golden pair {i+1}: ID={row.id}, Similarity={row.similarity:.4f}, Quality={row.quality_score}")
                golden_examples.append({
                    "id": str(row.id),
                    "rfq_text": row.rfq_text,
                    "survey_json": row.survey_json,
                    "methodology_tags": row.methodology_tags,
                    "industry_category": row.industry_category,
                    "research_goal": row.research_goal,
                    "quality_score": float(row.quality_score) if row.quality_score else None,
                    "similarity": float(row.similarity)
                })
            
            # Update usage count for retrieved golden pairs
            logger.info(f"📊 [RetrievalService] Updating usage counts for {len(golden_examples)} golden examples")
            for example in golden_examples:
                # Convert string ID back to UUID for database update
                from uuid import UUID
                example_id = UUID(example["id"])
                logger.info(f"📊 [RetrievalService] Updating usage count for example ID: {example_id}")
                result = self.db.execute(
                    text("UPDATE golden_rfq_survey_pairs SET usage_count = usage_count + 1 WHERE id = :id"),
                    {"id": example_id}
                )
                logger.info(f"📊 [RetrievalService] Update result: {result.rowcount} rows affected")
            
            self.db.commit()
            return golden_examples
            
        except Exception as e:
            raise Exception(f"Golden pair retrieval failed: {str(e)}")
    
    async def retrieve_methodology_blocks(
        self,
        research_goal: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Tier 2: Retrieve methodology blocks extracted from golden surveys
        """
        try:
            methodology_blocks = []
            
            # Build query with optional research goal filtering
            if research_goal:
                query = """
                    SELECT DISTINCT methodology_tags, survey_json, research_goal, 
                           industry_category, quality_score, id
                    FROM golden_rfq_survey_pairs
                    WHERE methodology_tags IS NOT NULL
                      AND research_goal ILIKE :research_goal
                    ORDER BY quality_score DESC NULLS LAST LIMIT :limit
                """
                result = self.db.execute(text(query), {
                    "research_goal": f"%{research_goal}%",
                    "limit": limit * 2
                })
            else:
                query = """
                    SELECT DISTINCT methodology_tags, survey_json, research_goal, 
                           industry_category, quality_score, id
                    FROM golden_rfq_survey_pairs
                    WHERE methodology_tags IS NOT NULL
                    ORDER BY quality_score DESC NULLS LAST LIMIT :limit
                """
                result = self.db.execute(text(query), {"limit": limit * 2})
            rows = result.fetchall()
            
            # Track seen methodologies to avoid duplicates
            seen_methodologies = set()
            
            for row in rows:
                if row.methodology_tags and len(methodology_blocks) < limit:
                    for tag in row.methodology_tags:
                        if tag not in seen_methodologies:
                            seen_methodologies.add(tag)
                            
                            # Extract methodology-specific patterns
                            structure = self._extract_methodology_structure(row.survey_json, tag)
                            usage_pattern = self._analyze_methodology_usage(tag, row.survey_json)
                            
                            methodology_blocks.append({
                                "methodology": tag,
                                "example_structure": structure,
                                "usage_pattern": usage_pattern,
                                "source_survey_id": str(row.id),
                                "quality_score": float(row.quality_score) if row.quality_score else 0.0,
                                "industry_context": row.industry_category,
                                "applicable_research_goals": self._extract_research_goals_for_methodology(tag)
                            })
                            
                            if len(methodology_blocks) >= limit:
                                break
            
            return methodology_blocks
            
        except Exception as e:
            raise Exception(f"Methodology block retrieval failed: {str(e)}")
    
    async def retrieve_template_questions(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tier 3: Retrieve individual template questions (fallback)
        TODO: Implement template question extraction and storage
        """
        try:
            # Placeholder implementation - extract common questions from golden pairs
            template_questions = []
            
            if category:
                query = """
                    SELECT survey_json, industry_category
                    FROM golden_rfq_survey_pairs
                    WHERE survey_json IS NOT NULL
                      AND industry_category = :category
                    LIMIT :limit
                """
                result = self.db.execute(text(query), {
                    "category": category,
                    "limit": limit * 2
                })
            else:
                query = """
                    SELECT survey_json, industry_category
                    FROM golden_rfq_survey_pairs
                    WHERE survey_json IS NOT NULL
                    LIMIT :limit
                """
                result = self.db.execute(text(query), {"limit": limit * 2})
            rows = result.fetchall()
            
            for row in rows:
                extracted_questions = self._extract_questions_from_survey(row.survey_json)
                template_questions.extend(extracted_questions)
                
                if len(template_questions) >= limit:
                    break
            
            return template_questions[:limit]
            
        except Exception as e:
            raise Exception(f"Template question retrieval failed: {str(e)}")
    
    def _extract_methodology_structure(self, survey_json: Dict[str, Any], methodology: str) -> Dict[str, Any]:
        """
        Extract structural patterns for a specific methodology from survey JSON
        """
        try:
            if not isinstance(survey_json, dict):
                return {"structure": "invalid_json"}
            
            method_lower = methodology.lower()
            structure = {"methodology": methodology}
            
            # Extract common structural elements
            questions = survey_json.get("questions", [])
            structure["total_questions"] = len(questions)
            
            if method_lower == "vw" or "van westendorp" in method_lower:
                # Van Westendorp Price Sensitivity Meter
                price_questions = []
                for q in questions:
                    question_text = str(q.get("text", "")).lower()
                    if any(keyword in question_text for keyword in ["price", "expensive", "cheap", "cost"]):
                        price_questions.append(q.get("text", ""))
                
                structure.update({
                    "required_questions": 4,
                    "pricing_structure": ["too_expensive", "too_cheap", "getting_expensive", "good_deal"],
                    "price_questions_found": len(price_questions),
                    "sample_questions": price_questions[:2]
                })
                
            elif method_lower == "gg" or "gabor" in method_lower:
                # Gabor-Granger Price Research
                price_points = []
                for q in questions:
                    options = q.get("options", [])
                    if any("$" in str(opt) or "price" in str(opt).lower() for opt in options):
                        price_points.extend([opt for opt in options if "$" in str(opt)])
                
                structure.update({
                    "price_points": len(price_points),
                    "incremental_structure": True,
                    "sample_price_points": price_points[:3]
                })
                
            elif method_lower == "conjoint" or "choice" in method_lower:
                # Conjoint Analysis / Choice Modeling
                attributes = set()
                for q in questions:
                    options = q.get("options", [])
                    if len(options) > 2:  # Multiple choice likely indicates attributes
                        for opt in options:
                            if isinstance(opt, dict) and "attributes" in opt:
                                attributes.update(opt["attributes"].keys())
                
                structure.update({
                    "max_attributes": 15,
                    "balanced_design": True,
                    "identified_attributes": list(attributes)[:5],
                    "choice_questions": len([q for q in questions if len(q.get("options", [])) > 2])
                })
                
            elif method_lower in ["maxdiff", "max diff", "maximum difference"]:
                # MaxDiff Analysis
                structure.update({
                    "item_sets": len([q for q in questions if "most" in str(q.get("text", "")).lower() or "least" in str(q.get("text", "")).lower()]),
                    "balanced_design": True,
                    "scaling_method": "rank_order"
                })
                
            else:
                # Generic structure extraction
                question_types = {}
                for q in questions:
                    q_type = q.get("type", "unknown")
                    question_types[q_type] = question_types.get(q_type, 0) + 1
                
                structure.update({
                    "structure": "generic",
                    "question_types": question_types,
                    "has_rating_scales": any("rating" in str(q.get("type", "")).lower() for q in questions)
                })
            
            return structure
            
        except Exception as e:
            return {"structure": "extraction_failed", "error": str(e)}
    
    def _extract_questions_from_survey(self, survey_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract individual questions from survey JSON for template use
        """
        questions = []
        
        try:
            if not isinstance(survey_json, dict):
                return questions
            
            # Handle different survey JSON structures
            question_sources = []
            
            # Standard structure: {"questions": [...]}
            if "questions" in survey_json:
                question_sources.extend(survey_json["questions"])
            
            # Alternative structures
            if "items" in survey_json:
                question_sources.extend(survey_json["items"])
            
            if "survey_questions" in survey_json:
                question_sources.extend(survey_json["survey_questions"])
                
            # Process each question
            for i, question in enumerate(question_sources[:5]):  # Limit per survey
                if not isinstance(question, dict):
                    continue
                
                # Extract question text from various possible fields
                question_text = (
                    question.get("text") or 
                    question.get("question") or 
                    question.get("title") or 
                    question.get("label") or 
                    ""
                )
                
                if not question_text:
                    continue
                
                # Determine question type
                question_type = self._classify_question_type(question)
                
                # Extract options/choices
                options = self._extract_question_options(question)
                
                # Determine category based on content
                category = self._categorize_question(question_text, question_type)
                
                # Extract additional metadata
                metadata = {
                    "required": question.get("required", False),
                    "has_other_option": self._has_other_option(options),
                    "scale_type": self._detect_scale_type(question, options),
                    "complexity": self._assess_question_complexity(question_text, options)
                }
                
                questions.append({
                    "question_text": question_text.strip(),
                    "question_type": question_type,
                    "options": options,
                    "category": category,
                    "metadata": metadata,
                    "source_position": i + 1,
                    "reusability_score": self._calculate_reusability_score(question_text, question_type, options)
                })
        
        except Exception as e:
            # Log error but don't fail completely
            questions.append({
                "question_text": "Question extraction failed",
                "question_type": "error",
                "options": [],
                "category": "system",
                "metadata": {"error": str(e)},
                "source_position": 0,
                "reusability_score": 0.0
            })
        
        # Sort by reusability score (highest first)
        questions.sort(key=lambda x: x.get("reusability_score", 0), reverse=True)
        
        return questions
    
    def reparse_survey_output(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reparse survey LLM output using the latest retrieval service logic
        This fixes surveys generated with outdated validation rules
        """
        logger.info("🔄 [RetrievalService] Starting survey reparse process")
        
        try:
            # Create a copy of the raw output to avoid modifying the original
            reparsed_survey = raw_output.copy()
            
            # Process each section
            if 'sections' in reparsed_survey and isinstance(reparsed_survey['sections'], list):
                logger.info(f"📊 [RetrievalService] Processing {len(reparsed_survey['sections'])} sections")
                
                for section in reparsed_survey['sections']:
                    if 'questions' in section and isinstance(section['questions'], list):
                        logger.info(f"🔍 [RetrievalService] Processing {len(section['questions'])} questions in section {section.get('id', 'unknown')}")
                        
                        for question in section['questions']:
                            # Reclassify question type using latest logic
                            original_type = question.get('type', '')
                            new_type = self._classify_question_type(question)
                            
                            if original_type != new_type:
                                logger.info(f"🔄 [RetrievalService] Question {question.get('id', 'unknown')}: {original_type} → {new_type}")
                                question['type'] = new_type
                            
                            # Re-extract options using latest logic
                            extracted_options = self._extract_question_options(question)
                            if extracted_options and not question.get('options'):
                                logger.info(f"➕ [RetrievalService] Question {question.get('id', 'unknown')}: Added {len(extracted_options)} options")
                                question['options'] = extracted_options
                            
                            # Ensure required fields are present
                            if 'required' not in question:
                                question['required'] = True
                            
                            # Add methodology field if missing
                            if 'methodology' not in question:
                                question['methodology'] = self._categorize_question(
                                    question.get('text', ''), 
                                    question.get('type', '')
                                )
            
            # Process legacy format (questions at root level)
            elif 'questions' in reparsed_survey and isinstance(reparsed_survey['questions'], list):
                logger.info(f"📊 [RetrievalService] Processing {len(reparsed_survey['questions'])} questions in legacy format")
                
                for question in reparsed_survey['questions']:
                    # Reclassify question type using latest logic
                    original_type = question.get('type', '')
                    new_type = self._classify_question_type(question)
                    
                    if original_type != new_type:
                        logger.info(f"🔄 [RetrievalService] Question {question.get('id', 'unknown')}: {original_type} → {new_type}")
                        question['type'] = new_type
                    
                    # Re-extract options using latest logic
                    extracted_options = self._extract_question_options(question)
                    if extracted_options and not question.get('options'):
                        logger.info(f"➕ [RetrievalService] Question {question.get('id', 'unknown')}: Added {len(extracted_options)} options")
                        question['options'] = extracted_options
                    
                    # Ensure required fields are present
                    if 'required' not in question:
                        question['required'] = True
            
            logger.info("✅ [RetrievalService] Survey reparse completed successfully")
            return reparsed_survey
            
        except Exception as e:
            logger.error(f"❌ [RetrievalService] Failed to reparse survey output: {str(e)}", exc_info=True)
            return None
    
    def _classify_question_type(self, question: Dict[str, Any]) -> str:
        """
        Classify the type of question based on its structure
        """
        # Check explicit type field first
        if "type" in question:
            return str(question["type"]).lower()
        
        # Infer from structure
        options = question.get("options", [])
        question_text = str(question.get("text", "")).lower()
        
        if len(options) == 0:
            if any(keyword in question_text for keyword in ["email", "name", "address"]):
                return "text"
            elif any(keyword in question_text for keyword in ["price", "amount", "cost", "number", "age", "quantity"]):
                return "numeric_open"
            else:
                return "open_text"
        elif len(options) == 2 and any(str(opt).lower() in ["yes", "no", "true", "false"] for opt in options):
            return "yes_no"
        elif len(options) <= 5:
            return "single_choice" 
        elif len(options) <= 15:
            return "multiple_choice"
        elif "matrix" in question_text or "rate" in question_text:
            return "matrix_likert"
        else:
            return "multiple_choice"
    
    def _extract_question_options(self, question: Dict[str, Any]) -> List[str]:
        """
        Extract options/choices from question
        """
        options = []
        
        # Try different option field names
        for field in ["options", "choices", "answers", "scale", "items"]:
            if field in question:
                raw_options = question[field]
                if isinstance(raw_options, list):
                    for opt in raw_options:
                        if isinstance(opt, dict):
                            # Handle object options
                            option_text = opt.get("text") or opt.get("label") or opt.get("value") or str(opt)
                        else:
                            option_text = str(opt)
                        
                        if option_text.strip():
                            options.append(option_text.strip())
                break
        
        return options[:10]  # Limit to 10 options for practicality
    
    def _categorize_question(self, question_text: str, question_type: str) -> str:
        """
        Categorize question based on content and type
        """
        text_lower = question_text.lower()
        
        # Demographic questions
        if any(keyword in text_lower for keyword in ["age", "gender", "income", "education", "occupation"]):
            return "demographic"
        
        # Rating/satisfaction questions
        elif any(keyword in text_lower for keyword in ["rate", "rating", "satisfy", "likely", "recommend"]):
            return "rating"
        
        # Price-related questions
        elif any(keyword in text_lower for keyword in ["price", "cost", "expensive", "cheap", "pay", "$"]):
            return "pricing"
        
        # Brand/product questions
        elif any(keyword in text_lower for keyword in ["brand", "product", "feature", "prefer"]):
            return "product"
        
        # Behavioral questions
        elif any(keyword in text_lower for keyword in ["how often", "frequency", "use", "buy", "purchase"]):
            return "behavioral"
        
        else:
            return "general"
    
    def _has_other_option(self, options: List[str]) -> bool:
        """
        Check if question has an 'other' or 'none of the above' option
        """
        other_keywords = ["other", "none of the above", "n/a", "prefer not to answer"]
        return any(any(keyword in str(opt).lower() for keyword in other_keywords) for opt in options)
    
    def _detect_scale_type(self, question: Dict[str, Any], options: List[str]) -> str:
        """
        Detect if this is a scale question and what type
        """
        if len(options) >= 3:
            # Check for numeric scales
            numeric_options = [opt for opt in options if opt.strip().isdigit()]
            if len(numeric_options) >= 3:
                return f"numeric_scale_{len(numeric_options)}"
            
            # Check for Likert scales
            likert_keywords = ["strongly disagree", "disagree", "neutral", "agree", "strongly agree"]
            if any(any(keyword in str(opt).lower() for keyword in likert_keywords) for opt in options):
                return f"likert_{len(options)}"
            
            # Check for satisfaction scales
            satisfaction_keywords = ["very dissatisfied", "dissatisfied", "satisfied", "very satisfied"]
            if any(any(keyword in str(opt).lower() for keyword in satisfaction_keywords) for opt in options):
                return f"satisfaction_{len(options)}"
        
        return "none"
    
    def _assess_question_complexity(self, question_text: str, options: List[str]) -> str:
        """
        Assess the complexity of the question
        """
        # Simple heuristics
        text_length = len(question_text.split())
        option_count = len(options)
        
        if text_length <= 8 and option_count <= 5:
            return "simple"
        elif text_length <= 15 and option_count <= 10:
            return "medium"
        else:
            return "complex"
    
    def _calculate_reusability_score(self, question_text: str, question_type: str, options: List[str]) -> float:
        """
        Calculate how reusable this question is across different surveys
        """
        score = 0.5  # Base score
        
        # Higher score for common question types
        if question_type in ["rating_scale", "single_choice", "yes_no"]:
            score += 0.2
        
        # Higher score for demographic questions (widely reusable)
        text_lower = question_text.lower()
        if any(keyword in text_lower for keyword in ["age", "gender", "education", "income"]):
            score += 0.3
        
        # Higher score for standard rating questions
        if any(keyword in text_lower for keyword in ["rate", "satisfaction", "likely to recommend"]):
            score += 0.2
        
        # Lower score for very specific questions
        if any(keyword in text_lower for keyword in ["company", "brand", "specific product name"]):
            score -= 0.2
        
        # Adjust based on option quality
        if len(options) > 0:
            if self._has_other_option(options):
                score += 0.1
            if len(options) in [3, 4, 5, 7]:  # Common scale lengths
                score += 0.1
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def _analyze_methodology_usage(self, methodology: str, survey_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze how a methodology is typically used based on survey structure
        """
        try:
            if not isinstance(survey_json, dict):
                return {"usage": "unknown"}
            
            questions = survey_json.get("questions", [])
            method_lower = methodology.lower()
            
            usage_pattern = {
                "methodology": methodology,
                "typical_question_count": len(questions),
                "complexity": "medium"
            }
            
            # Analyze complexity based on methodology
            if method_lower == "vw" or "van westendorp" in method_lower:
                usage_pattern.update({
                    "complexity": "low",
                    "typical_duration": "5-10 minutes",
                    "best_for": ["price optimization", "pricing research"],
                    "question_flow": "sequential_price_points"
                })
            elif method_lower == "conjoint" or "choice" in method_lower:
                usage_pattern.update({
                    "complexity": "high",
                    "typical_duration": "15-25 minutes",
                    "best_for": ["feature optimization", "product development"],
                    "question_flow": "randomized_choice_sets"
                })
            elif method_lower == "gg" or "gabor" in method_lower:
                usage_pattern.update({
                    "complexity": "medium",
                    "typical_duration": "8-12 minutes", 
                    "best_for": ["price sensitivity", "demand forecasting"],
                    "question_flow": "incremental_price_testing"
                })
            else:
                usage_pattern.update({
                    "complexity": "medium",
                    "typical_duration": "10-15 minutes",
                    "best_for": ["general research"],
                    "question_flow": "standard"
                })
            
            return usage_pattern
            
        except Exception as e:
            return {"usage": "analysis_failed", "error": str(e)}
    
    def _extract_research_goals_for_methodology(self, methodology: str) -> List[str]:
        """
        Return typical research goals that align with specific methodologies
        """
        method_lower = methodology.lower()
        
        methodology_goals = {
            "vw": ["pricing optimization", "price sensitivity analysis", "market positioning"],
            "van westendorp": ["pricing optimization", "price sensitivity analysis", "market positioning"],
            "gg": ["demand forecasting", "price elasticity", "revenue optimization"],
            "gabor": ["demand forecasting", "price elasticity", "revenue optimization"],
            "conjoint": ["feature prioritization", "product optimization", "market simulation"],
            "choice": ["feature prioritization", "product optimization", "market simulation"],
            "maxdiff": ["feature ranking", "priority analysis", "importance scoring"],
            "max diff": ["feature ranking", "priority analysis", "importance scoring"],
            "nps": ["customer satisfaction", "loyalty measurement", "brand health"],
            "csat": ["customer satisfaction", "service quality", "experience measurement"]
        }
        
        # Find matching methodology
        for key, goals in methodology_goals.items():
            if key in method_lower:
                return goals
        
        # Default goals for unknown methodologies
        return ["general research", "data collection", "market insights"]