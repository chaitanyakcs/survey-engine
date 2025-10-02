"""
Advanced Labeling Service for Survey Annotations
Provides automated classification, compliance checking, and advanced labeling capabilities
"""

from sqlalchemy.orm import Session
from src.database.models import QuestionAnnotation, SectionAnnotation, SurveyAnnotation
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from pydantic import BaseModel
import re
import json
from datetime import datetime


class LabelingResult(BaseModel):
    """Result of advanced labeling operation"""
    industry_classification: Optional[str] = None
    respondent_type: Optional[str] = None
    methodology_tags: List[str] = []
    advanced_labels: Dict[str, Any] = {}
    is_mandatory: bool = False
    compliance_status: str = "not_checked"
    confidence_score: float = 0.0


class ComplianceReport(BaseModel):
    """Compliance analysis report"""
    overall_score: int = 0
    mandatory_elements_found: List[str] = []
    missing_elements: List[str] = []
    recommendations: List[str] = []
    compliance_level: str = "unknown"  # low, medium, high, full


class AdvancedLabelingService:
    """Service for advanced survey labeling and compliance checking"""

    def __init__(self, db: Session):
        self.db = db
        self._load_classification_rules()

    def _load_classification_rules(self):
        """Load classification rules and taxonomies"""
        # Industry classifications based on the CSV framework
        self.industry_types = {
            "technology": ["software", "tech", "digital", "AI", "automation", "platform"],
            "healthcare": ["health", "medical", "patient", "clinical", "pharmacy", "therapy"],
            "financial": ["banking", "finance", "investment", "trading", "payment", "credit"],
            "retail": ["shopping", "consumer", "product", "brand", "purchase", "store"],
            "education": ["student", "learning", "academic", "course", "university", "training"],
            "automotive": ["vehicle", "car", "automotive", "driving", "transportation"],
            "real_estate": ["property", "housing", "real estate", "rental", "mortgage"],
            "food_beverage": ["food", "restaurant", "dining", "beverage", "nutrition"],
            "travel": ["travel", "tourism", "hotel", "vacation", "destination"],
            "entertainment": ["entertainment", "media", "gaming", "streaming", "content"]
        }

        # Respondent type classifications
        self.respondent_types = {
            "B2C": ["consumer", "customer", "individual", "personal", "household"],
            "B2B": ["business", "enterprise", "company", "organization", "professional"],
            "healthcare_professional": ["doctor", "nurse", "physician", "medical professional"],
            "student": ["student", "learner", "academic", "scholar"],
            "expert": ["expert", "specialist", "consultant", "analyst"],
            "employee": ["employee", "worker", "staff", "team member"]
        }

        # Methodology tags
        self.methodology_tags = {
            "quantitative": ["scale", "rating", "number", "quantity", "measurement"],
            "qualitative": ["open-ended", "comment", "opinion", "experience", "story"],
            "demographic": ["age", "gender", "income", "location", "education"],
            "behavioral": ["frequency", "usage", "behavior", "habit", "action"],
            "attitudinal": ["satisfaction", "preference", "opinion", "perception", "feeling"],
            "screening": ["qualification", "eligibility", "screening", "filter"],
            "net_promoter": ["recommend", "NPS", "promoter", "likelihood to recommend"],
            "van_westendorp": ["price", "pricing", "cost", "expensive", "cheap"]
        }

        # Mandatory elements for compliance
        self.mandatory_elements = {
            "introduction": ["introduction", "welcome", "purpose", "explanation"],
            "consent": ["consent", "agreement", "permission", "privacy"],
            "demographics": ["demographic", "background", "profile"],
            "screening": ["screening", "qualification", "eligibility"],
            "core_questions": ["main", "core", "primary", "key questions"],
            "closing": ["thank you", "completion", "closing", "summary"]
        }

    def classify_industry(self, text: str) -> Tuple[Optional[str], float]:
        """Classify industry based on survey content"""
        text_lower = text.lower()
        industry_scores = {}

        for industry, keywords in self.industry_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                industry_scores[industry] = score / len(keywords)

        if not industry_scores:
            return None, 0.0

        best_industry = max(industry_scores.items(), key=lambda x: x[1])
        return best_industry[0], best_industry[1]

    def classify_respondent_type(self, text: str) -> Tuple[Optional[str], float]:
        """Classify respondent type based on survey content"""
        text_lower = text.lower()
        type_scores = {}

        for resp_type, keywords in self.respondent_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[resp_type] = score / len(keywords)

        if not type_scores:
            return None, 0.0

        best_type = max(type_scores.items(), key=lambda x: x[1])
        return best_type[0], best_type[1]

    def detect_methodology_tags(self, text: str) -> List[str]:
        """Detect methodology tags in survey content"""
        text_lower = text.lower()
        detected_tags = []

        for tag, keywords in self.methodology_tags.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_tags.append(tag)

        return detected_tags

    def check_mandatory_elements(self, survey_content: str) -> Tuple[List[str], List[str]]:
        """Check for mandatory elements in survey"""
        content_lower = survey_content.lower()
        found_elements = []
        missing_elements = []

        for element, keywords in self.mandatory_elements.items():
            if any(keyword in content_lower for keyword in keywords):
                found_elements.append(element)
            else:
                missing_elements.append(element)

        return found_elements, missing_elements

    def calculate_compliance_score(self, found_elements: List[str], total_elements: int = None) -> int:
        """Calculate compliance score based on found mandatory elements"""
        if total_elements is None:
            total_elements = len(self.mandatory_elements)

        if total_elements == 0:
            return 100

        return min(100, int((len(found_elements) / total_elements) * 100))

    def analyze_question(self, question_text: str, context: str = "") -> LabelingResult:
        """Analyze a single question for advanced labeling"""
        combined_text = f"{question_text} {context}"

        # Classify industry and respondent type
        industry, industry_confidence = self.classify_industry(combined_text)
        respondent_type, respondent_confidence = self.classify_respondent_type(combined_text)

        # Detect methodology tags
        methodology_tags = self.detect_methodology_tags(combined_text)

        # Check if question appears mandatory
        is_mandatory = any(keyword in question_text.lower() for keyword in
                          ["required", "must", "mandatory", "necessary"])

        # Create advanced labels
        advanced_labels = {
            "analysis_timestamp": datetime.now().isoformat(),
            "industry_confidence": industry_confidence,
            "respondent_confidence": respondent_confidence,
            "methodology_confidence": len(methodology_tags) / len(self.methodology_tags),
            "keywords_detected": self._extract_keywords(combined_text)
        }

        # Determine compliance status
        compliance_status = "compliant" if industry_confidence > 0.3 else "needs_review"

        return LabelingResult(
            industry_classification=industry,
            respondent_type=respondent_type,
            methodology_tags=methodology_tags,
            advanced_labels=advanced_labels,
            is_mandatory=is_mandatory,
            compliance_status=compliance_status,
            confidence_score=max(industry_confidence, respondent_confidence)
        )

    def analyze_section(self, section_content: str, section_title: str = "") -> Dict[str, Any]:
        """Analyze a survey section for advanced labeling"""
        combined_text = f"{section_title} {section_content}"

        # Check for mandatory elements in this section
        found_elements, missing_elements = self.check_mandatory_elements(combined_text)
        compliance_score = self.calculate_compliance_score(found_elements)

        # Classify section type
        section_classification = self._classify_section_type(combined_text)

        # Create mandatory elements structure
        mandatory_elements = {
            "found": found_elements,
            "missing": missing_elements,
            "analysis_timestamp": datetime.now().isoformat()
        }

        return {
            "section_classification": section_classification,
            "mandatory_elements": mandatory_elements,
            "compliance_score": compliance_score
        }

    def analyze_survey(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze entire survey for advanced labeling"""
        # Extract survey content
        survey_text = self._extract_survey_text(survey_data)

        # Detect labels across entire survey
        detected_labels = {
            "industry_analysis": {},
            "respondent_analysis": {},
            "methodology_analysis": {},
            "quality_metrics": {}
        }

        # Industry analysis
        industry, industry_conf = self.classify_industry(survey_text)
        detected_labels["industry_analysis"] = {
            "primary_industry": industry,
            "confidence": industry_conf,
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Respondent analysis
        respondent_type, resp_conf = self.classify_respondent_type(survey_text)
        detected_labels["respondent_analysis"] = {
            "primary_type": respondent_type,
            "confidence": resp_conf,
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Methodology analysis
        methodology_tags = self.detect_methodology_tags(survey_text)
        detected_labels["methodology_analysis"] = {
            "tags": methodology_tags,
            "primary_approach": "mixed" if len(methodology_tags) > 2 else methodology_tags[0] if methodology_tags else "unknown",
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Generate compliance report
        found_elements, missing_elements = self.check_mandatory_elements(survey_text)
        compliance_score = self.calculate_compliance_score(found_elements)

        compliance_report = {
            "overall_score": compliance_score,
            "mandatory_elements_found": found_elements,
            "missing_elements": missing_elements,
            "compliance_level": self._get_compliance_level(compliance_score),
            "recommendations": self._generate_recommendations(missing_elements),
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Advanced metadata
        advanced_metadata = {
            "total_questions": self._count_questions(survey_data),
            "total_sections": self._count_sections(survey_data),
            "estimated_completion_time": self._estimate_completion_time(survey_data),
            "complexity_score": self._calculate_complexity_score(survey_data),
            "analysis_timestamp": datetime.now().isoformat()
        }

        return {
            "detected_labels": detected_labels,
            "compliance_report": compliance_report,
            "advanced_metadata": advanced_metadata
        }

    def _classify_section_type(self, section_content: str) -> str:
        """Classify the type of survey section"""
        content_lower = section_content.lower()

        if any(keyword in content_lower for keyword in ["welcome", "introduction", "purpose"]):
            return "introduction"
        elif any(keyword in content_lower for keyword in ["demographic", "background", "about you"]):
            return "demographics"
        elif any(keyword in content_lower for keyword in ["screen", "qualify", "eligible"]):
            return "screening"
        elif any(keyword in content_lower for keyword in ["thank", "complete", "finish", "end"]):
            return "closing"
        else:
            return "content"

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common words and return significant terms
        stopwords = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "a", "an", "is", "are", "was", "were"}
        keywords = [word for word in words if len(word) > 3 and word not in stopwords]
        return list(set(keywords[:10]))  # Return top 10 unique keywords

    def _extract_survey_text(self, survey_data: Dict[str, Any]) -> str:
        """Extract all text content from survey data"""
        # This would need to be adapted based on your survey data structure
        text_parts = []

        if isinstance(survey_data, dict):
            for key, value in survey_data.items():
                if isinstance(value, str):
                    text_parts.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            text_parts.append(item)
                        elif isinstance(item, dict):
                            text_parts.append(self._extract_survey_text(item))

        return " ".join(text_parts)

    def _get_compliance_level(self, score: int) -> str:
        """Get compliance level based on score"""
        if score >= 90:
            return "full"
        elif score >= 70:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"

    def _generate_recommendations(self, missing_elements: List[str]) -> List[str]:
        """Generate recommendations based on missing elements"""
        recommendations = []

        for element in missing_elements:
            if element == "introduction":
                recommendations.append("Add an introduction section explaining the survey purpose")
            elif element == "consent":
                recommendations.append("Include consent and privacy information")
            elif element == "demographics":
                recommendations.append("Add demographic questions for better analysis")
            elif element == "screening":
                recommendations.append("Consider adding screening questions to ensure target audience")
            elif element == "closing":
                recommendations.append("Add a closing section with thank you message")

        return recommendations

    def _count_questions(self, survey_data: Dict[str, Any]) -> int:
        """Count total questions in survey"""
        # Simplified implementation - would need survey structure knowledge
        return len(str(survey_data).split("question")) - 1

    def _count_sections(self, survey_data: Dict[str, Any]) -> int:
        """Count total sections in survey"""
        # Simplified implementation - would need survey structure knowledge
        return len(str(survey_data).split("section")) - 1

    def _estimate_completion_time(self, survey_data: Dict[str, Any]) -> int:
        """Estimate completion time in minutes"""
        # Rule of thumb: 2-3 seconds per word, with minimum per question
        text = self._extract_survey_text(survey_data)
        word_count = len(text.split())
        question_count = self._count_questions(survey_data)

        # 2 seconds per word + 10 seconds per question overhead
        estimated_seconds = (word_count * 2) + (question_count * 10)
        return max(1, int(estimated_seconds / 60))  # Convert to minutes, minimum 1

    def _calculate_complexity_score(self, survey_data: Dict[str, Any]) -> float:
        """Calculate survey complexity score (0-10)"""
        text = self._extract_survey_text(survey_data)
        word_count = len(text.split())
        question_count = self._count_questions(survey_data)
        section_count = self._count_sections(survey_data)

        # Complexity factors
        length_factor = min(5, word_count / 100)  # Max 5 points for length
        structure_factor = min(3, section_count * 0.5)  # Max 3 points for structure
        question_factor = min(2, question_count / 10)  # Max 2 points for question count

        return round(length_factor + structure_factor + question_factor, 1)

    def apply_bulk_labeling(self, survey_id: str, annotator_id: str = "advanced_labeling_system") -> Dict[str, Any]:
        """Apply advanced labeling to all annotations for a survey"""
        results = {
            "survey_id": survey_id,
            "processed_questions": 0,
            "processed_sections": 0,
            "updated_survey": False,
            "errors": []
        }

        try:
            # Get all annotations for the survey
            question_annotations = self.db.query(QuestionAnnotation).filter(
                QuestionAnnotation.survey_id == survey_id
            ).all()

            section_annotations = self.db.query(SectionAnnotation).filter(
                SectionAnnotation.survey_id == survey_id
            ).all()

            survey_annotation = self.db.query(SurveyAnnotation).filter(
                SurveyAnnotation.survey_id == survey_id
            ).first()

            # Process question annotations
            for qa in question_annotations:
                try:
                    # Analyze question (you'd need actual question text here)
                    labeling_result = self.analyze_question(f"Question {qa.question_id}", "")

                    # Update annotation with advanced labeling
                    qa.advanced_labels = labeling_result.advanced_labels
                    qa.industry_classification = labeling_result.industry_classification
                    qa.respondent_type = labeling_result.respondent_type
                    qa.methodology_tags = labeling_result.methodology_tags
                    qa.is_mandatory = labeling_result.is_mandatory
                    qa.compliance_status = labeling_result.compliance_status

                    results["processed_questions"] += 1
                except Exception as e:
                    results["errors"].append(f"Question {qa.question_id}: {str(e)}")

            # Process section annotations
            for sa in section_annotations:
                try:
                    # Analyze section (you'd need actual section content here)
                    section_result = self.analyze_section(f"Section {sa.section_id}", "")

                    # Update annotation with advanced labeling
                    sa.section_classification = section_result["section_classification"]
                    sa.mandatory_elements = section_result["mandatory_elements"]
                    sa.compliance_score = section_result["compliance_score"]

                    results["processed_sections"] += 1
                except Exception as e:
                    results["errors"].append(f"Section {sa.section_id}: {str(e)}")

            # Process survey-level annotation
            if survey_annotation:
                try:
                    # Analyze entire survey (you'd need actual survey data here)
                    survey_result = self.analyze_survey({"survey_id": survey_id})

                    # Update survey annotation with advanced labeling
                    survey_annotation.detected_labels = survey_result["detected_labels"]
                    survey_annotation.compliance_report = survey_result["compliance_report"]
                    survey_annotation.advanced_metadata = survey_result["advanced_metadata"]

                    results["updated_survey"] = True
                except Exception as e:
                    results["errors"].append(f"Survey level: {str(e)}")

            # Commit all changes
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            results["errors"].append(f"General error: {str(e)}")

        return results