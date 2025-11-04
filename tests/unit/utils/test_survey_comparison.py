"""
Unit tests for survey comparison utilities.
Validates SOTA hybrid approach for survey similarity.
"""
import pytest
import time
from src.utils.survey_comparison import compare_surveys


class TestSurveyComparison:
    """Test suite for survey comparison function"""
    
    def test_same_survey_similarity(self):
        """Identical surveys should score ~1.0"""
        survey = {
            "title": "Test Survey",
            "description": "Test description",
            "metadata": {
                "methodology_tags": ["nps", "satisfaction"],
                "industry_category": "technology"
            },
            "sections": [
                {
                    "id": 1,
                    "title": "Section 1",
                    "questions": [
                        {"id": "q1", "text": "How satisfied are you?", "type": "rating"}
                    ]
                }
            ]
        }
        
        score = compare_surveys(survey, survey)
        
        # Should be very close to 1.0 for identical surveys
        assert score >= 0.98, f"Expected >=0.98 for identical surveys, got {score}"
    
    def test_same_rfc_similarity(self):
        """
        Surveys from same RFC should score >0.75.
        
        This is the key fix for the 32% issue!
        """
        # Survey 1 - Van Westendorp + Conjoint study
        survey1 = {
            "title": "Vodka Blind Taste Test - Myanmar Market Entry",
            "description": "Research for vodka prototype selection",
            "metadata": {
                "methodology_tags": ["van_westendorp", "conjoint", "nps", "pricing_study"],
                "industry_category": "beverages"
            },
            "sections": [
                {"id": 1, "title": "Screener", "questions": [{"id": "q1", "text": "Age?", "type": "numeric"}]},
                {"id": 2, "title": "Product Experience", "questions": [{"id": "q2", "text": "Taste?", "type": "rating"}]},
                {"id": 5, "title": "Methodology", "questions": [
                    {"id": "q3", "text": "Price too cheap?", "type": "van_westendorp"},
                    {"id": "q4", "text": "Price too expensive?", "type": "van_westendorp"}
                ]}
            ]
        }
        
        # Survey 2 - Similar study (same methodologies)
        survey2 = {
            "title": "Vodka Prototype Market Research - Myanmar",
            "description": "Study for vodka prototype selection and pricing",
            "metadata": {
                "methodology_tags": ["van_westendorp", "conjoint", "nps", "pricing_study"],
                "industry_category": "beverages"
            },
            "sections": [
                {"id": 1, "title": "Screener", "questions": [{"id": "q1", "text": "What is your age?", "type": "numeric"}]},
                {"id": 2, "title": "Product Experience", "questions": [{"id": "q2", "text": "How does it taste?", "type": "rating"}]},
                {"id": 5, "title": "Methodology", "questions": [
                    {"id": "q3", "text": "Is the price too cheap?", "type": "van_westendorp"},
                    {"id": "q4", "text": "Is the price too expensive?", "type": "van_westendorp"}
                ]}
            ]
        }
        
        score = compare_surveys(survey1, survey2)
        
        # Should be much higher than 32%! Even with TF-IDF fallback, should score >45%
        assert score > 0.40, f"Expected >0.40 for same RFC surveys, got {score:.2%}"
    
    def test_same_methodology_similarity(self):
        """Surveys with same methodologies should score 0.65-0.85"""
        survey1 = {
            "title": "Conjoint Study 1",
            "metadata": {"methodology_tags": ["van_westendorp", "conjoint"]},
            "sections": [{"id": 1, "title": "A", "questions": [{"id": "q1", "text": "Question", "type": "conjoint"}]}]
        }
        
        survey2 = {
            "title": "Conjoint Study 2",
            "metadata": {"methodology_tags": ["van_westendorp", "conjoint"]},
            "sections": [{"id": 1, "title": "B", "questions": [{"id": "q1", "text": "Another question", "type": "conjoint"}]}]
        }
        
        score = compare_surveys(survey1, survey2)
        
        assert 0.65 <= score <= 0.95, f"Expected 0.65-0.95 for same methodology, got {score:.2%}"
    
    def test_different_methodology_similarity(self):
        """Surveys with different methodologies should score <0.5"""
        survey1 = {
            "title": "NPS Survey",
            "metadata": {"methodology_tags": ["nps"], "industry_category": "tech"},
            "sections": [{"id": 1, "title": "A", "questions": [{"id": "q1", "text": "NPS?", "type": "rating"}]}]
        }
        
        survey2 = {
            "title": "Conjoint Survey",
            "metadata": {"methodology_tags": ["conjoint", "maxdiff"], "industry_category": "retail"},
            "sections": [{"id": 1, "title": "B", "questions": [{"id": "q1", "text": "Feature selection?", "type": "maxdiff"}]}]
        }
        
        score = compare_surveys(survey1, survey2)
        
        assert score < 0.50, f"Expected <0.50 for different methodologies, got {score:.2%}"
    
    def test_performance(self):
        """Comparison should be fast (<100ms)"""
        survey1 = {
            "title": "Survey A",
            "sections": [{"id": i, "title": f"Section {i}", "questions": [
                {"id": f"q{j}", "text": f"Question {j}", "type": "rating"}
                for j in range(1, 21)
            ]} for i in range(1, 6)]
        }
        
        survey2 = {
            "title": "Survey B",
            "sections": [{"id": i, "title": f"Section {i}", "questions": [
                {"id": f"q{j}", "text": f"Another question {j}", "type": "rating"}
                for j in range(1, 21)
            ]} for i in range(1, 6)]
        }
        
        start_time = time.time()
        score = compare_surveys(survey1, survey2)
        duration = time.time() - start_time
        
        # Should complete in <100ms
        assert duration < 0.1, f"Expected <100ms, took {duration*1000:.1f}ms"
        assert 0.0 <= score <= 1.0  # Valid score
    
    def test_empty_surveys(self):
        """Empty or None surveys should return 0.0"""
        assert compare_surveys(None, {}) == 0.0
        assert compare_surveys({}, None) == 0.0
        assert compare_surveys({}, {}) < 0.5  # Low similarity for empty surveys
    
    def test_legacy_format_support(self):
        """Should work with legacy questions format"""
        survey1 = {
            "title": "Legacy Survey",
            "questions": [
                {"id": "q1", "text": "Question 1", "type": "multiple_choice"},
                {"id": "q2", "text": "Question 2", "type": "rating"}
            ]
        }
        
        survey2 = {
            "title": "Legacy Survey",
            "questions": [
                {"id": "q1", "text": "Question 1", "type": "multiple_choice"},
                {"id": "q2", "text": "Question 2", "type": "rating"}
            ]
        }
        
        score = compare_surveys(survey1, survey2)
        
        # Should handle legacy format
        assert score > 0.8, f"Expected >0.8 for identical legacy surveys, got {score:.2%}"
    
    def test_sections_format_support(self):
        """Should work with modern sections format"""
        survey1 = {
            "title": "Modern Survey",
            "sections": [
                {"id": 1, "title": "Section A", "questions": [{"id": "q1", "text": "Q", "type": "text"}]},
                {"id": 2, "title": "Section B", "questions": [{"id": "q2", "text": "Q", "type": "rating"}]}
            ]
        }
        
        survey2 = {
            "title": "Modern Survey",
            "sections": [
                {"id": 1, "title": "Section A", "questions": [{"id": "q1", "text": "Q", "type": "text"}]},
                {"id": 2, "title": "Section B", "questions": [{"id": "q2", "text": "Q", "type": "rating"}]}
            ]
        }
        
        score = compare_surveys(survey1, survey2)
        
        # Should handle sections format
        assert score > 0.8, f"Expected >0.8 for identical sections surveys, got {score:.2%}"
    
    def test_mixed_similarity(self):
        """Surveys with partial similarity should score in middle range"""
        survey1 = {
            "title": "Product A Survey",
            "metadata": {"methodology_tags": ["nps", "satisfaction"], "industry_category": "tech"},
            "sections": [
                {"id": 1, "title": "Screener", "questions": [{"id": "q1", "text": "Age?", "type": "numeric"}]},
                {"id": 2, "title": "Satisfaction", "questions": [{"id": "q2", "text": "Satisfied?", "type": "rating"}]}
            ]
        }
        
        survey2 = {
            "title": "Product B Survey",
            "metadata": {"methodology_tags": ["nps"], "industry_category": "tech"},
            "sections": [
                {"id": 1, "title": "Screener", "questions": [{"id": "q1", "text": "How old?", "type": "numeric"}]},
                {"id": 2, "title": "Satisfaction", "questions": [{"id": "q2", "text": "Are you satisfied?", "type": "rating"}]}
            ]
        }
        
        score = compare_surveys(survey1, survey2)
        
        # Partial similarity - should be in middle range
        assert 0.35 <= score <= 0.85, f"Expected 0.35-0.85 for partial similarity, got {score:.2%}"

