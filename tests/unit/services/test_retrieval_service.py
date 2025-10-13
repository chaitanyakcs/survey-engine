import pytest
from unittest.mock import MagicMock, patch

# Mock pgvector before importing RetrievalService
with patch.dict('sys.modules', {
    'pgvector': MagicMock(),
    'pgvector.sqlalchemy': MagicMock()
}):
    from src.services.retrieval_service import RetrievalService


class TestRetrievalService:
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = MagicMock()
        return mock_session
    
    @pytest.fixture
    def retrieval_service(self, mock_db_session):
        """Create RetrievalService instance with mock DB"""
        return RetrievalService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_retrieve_golden_pairs(self, retrieval_service, mock_db_session):
        """Test golden pair retrieval with semantic similarity"""
        # Mock database response
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.rfq_text = "Test RFQ"
        mock_row.survey_json = {"questions": []}
        mock_row.methodology_tags = ["vw"]
        mock_row.industry_category = "tech"
        mock_row.research_goal = "pricing"
        mock_row.quality_score = 0.95
        mock_row.similarity = 0.85
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db_session.execute.return_value = mock_result
        
        # Test retrieval
        embedding = [0.1, 0.2, 0.3]
        results = await retrieval_service.retrieve_golden_pairs(embedding, limit=1)
        
        assert len(results) == 1
        assert results[0]["id"] == "1"
        assert results[0]["rfq_text"] == "Test RFQ"
        assert results[0]["similarity"] == 0.85
        assert results[0]["methodology_tags"] == ["vw"]
    
    @pytest.mark.asyncio
    async def test_retrieve_methodology_blocks(self, retrieval_service, mock_db_session):
        """Test methodology block extraction and retrieval"""
        # Mock database response
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.methodology_tags = ["vw", "conjoint"]
        mock_row.survey_json = {
            "questions": [
                {"text": "At what price would this be too expensive?", "type": "text"},
                {"text": "At what price would this be too cheap?", "type": "text"}
            ]
        }
        mock_row.research_goal = "pricing research"
        mock_row.industry_category = "consumer"
        mock_row.quality_score = 0.9
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db_session.execute.return_value = mock_result
        
        # Test methodology block retrieval
        results = await retrieval_service.retrieve_methodology_blocks(
            research_goal="pricing", limit=2
        )
        
        assert len(results) <= 2
        assert all("methodology" in block for block in results)
        assert all("example_structure" in block for block in results)
        assert all("usage_pattern" in block for block in results)
    
    @pytest.mark.asyncio
    async def test_retrieve_template_questions(self, retrieval_service, mock_db_session):
        """Test template question extraction"""
        # Mock database response
        mock_row = MagicMock()
        mock_row.survey_json = {
            "questions": [
                {
                    "text": "What is your age?",
                    "type": "single_choice",
                    "options": ["18-24", "25-34", "35-44", "45+"]
                },
                {
                    "text": "How satisfied are you?",
                    "type": "rating_scale",
                    "options": ["Very dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very satisfied"]
                }
            ]
        }
        mock_row.industry_category = "general"
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db_session.execute.return_value = mock_result
        
        # Test template question retrieval
        results = await retrieval_service.retrieve_template_questions(
            category="general", limit=5
        )
        
        assert len(results) <= 5
        for question in results:
            assert "question_text" in question
            assert "question_type" in question
            assert "category" in question
            assert "reusability_score" in question
    
    def test_extract_methodology_structure_vw(self, retrieval_service):
        """Test Van Westendorp methodology structure extraction"""
        survey_json = {
            "questions": [
                {"text": "At what price would this be too expensive?", "type": "text"},
                {"text": "At what price would this be getting expensive?", "type": "text"},
                {"text": "At what price would this be a good deal?", "type": "text"},
                {"text": "At what price would this be too cheap?", "type": "text"}
            ]
        }
        
        structure = retrieval_service._extract_methodology_structure(survey_json, "vw")
        
        assert structure["methodology"] == "vw"
        assert structure["required_questions"] == 4
        assert "price_questions_found" in structure
        assert structure["price_questions_found"] == 4
        assert "pricing_structure" in structure
    
    def test_extract_methodology_structure_conjoint(self, retrieval_service):
        """Test Conjoint methodology structure extraction"""
        survey_json = {
            "questions": [
                {
                    "text": "Which would you choose?",
                    "type": "single_choice",
                    "options": ["Option A", "Option B", "Option C"]
                },
                {
                    "text": "Rate this feature combination",
                    "type": "rating",
                    "options": ["1", "2", "3", "4", "5"]
                }
            ]
        }
        
        structure = retrieval_service._extract_methodology_structure(survey_json, "conjoint")
        
        assert structure["methodology"] == "conjoint"
        assert structure["max_attributes"] == 15
        assert structure["balanced_design"] == True
        assert "choice_questions" in structure
    
    def test_classify_question_type(self, retrieval_service):
        """Test question type classification"""
        # Test explicit type
        question_with_type = {"type": "rating", "text": "Rate this"}
        assert retrieval_service._classify_question_type(question_with_type) == "rating"
        
        # Test yes/no inference
        yes_no_question = {
            "text": "Do you agree?",
            "options": ["Yes", "No"]
        }
        assert retrieval_service._classify_question_type(yes_no_question) == "yes_no"
        
        # Test single choice
        single_choice = {
            "text": "Pick one",
            "options": ["A", "B", "C"]
        }
        assert retrieval_service._classify_question_type(single_choice) == "single_choice"
        
        # Test open text
        open_text = {"text": "Tell us about yourself"}
        assert retrieval_service._classify_question_type(open_text) == "open_text"
    
    def test_categorize_question(self, retrieval_service):
        """Test question categorization by content"""
        # Test demographic
        assert retrieval_service._categorize_question("What is your age?", "single_choice") == "demographic"
        assert retrieval_service._categorize_question("What is your gender?", "single_choice") == "demographic"
        
        # Test pricing
        assert retrieval_service._categorize_question("What would you pay?", "text") == "pricing"
        assert retrieval_service._categorize_question("Is $50 expensive?", "yes_no") == "pricing"
        
        # Test rating
        assert retrieval_service._categorize_question("Rate your satisfaction", "rating") == "rating"
        assert retrieval_service._categorize_question("How likely to recommend?", "rating") == "rating"
        
        # Test behavioral
        assert retrieval_service._categorize_question("How often do you buy?", "single_choice") == "behavioral"
        
        # Test general
        assert retrieval_service._categorize_question("What do you think?", "text") == "general"
    
    def test_detect_scale_type(self, retrieval_service):
        """Test scale type detection"""
        # Test numeric scale
        numeric_question = {"text": "Rate 1-10"}
        numeric_options = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        scale_type = retrieval_service._detect_scale_type(numeric_question, numeric_options)
        assert "numeric_scale" in scale_type
        
        # Test Likert scale
        likert_options = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]
        scale_type = retrieval_service._detect_scale_type({}, likert_options)
        assert "likert" in scale_type
        
        # Test satisfaction scale
        satisfaction_options = ["Very dissatisfied", "Dissatisfied", "Satisfied", "Very satisfied"]
        scale_type = retrieval_service._detect_scale_type({}, satisfaction_options)
        assert "satisfaction" in scale_type
        
        # Test no scale
        regular_options = ["Apple", "Banana", "Orange"]
        scale_type = retrieval_service._detect_scale_type({}, regular_options)
        assert scale_type == "none"
    
    def test_calculate_reusability_score(self, retrieval_service):
        """Test reusability score calculation"""
        # High reusability - demographic question
        score = retrieval_service._calculate_reusability_score(
            "What is your age?", "single_choice", ["18-24", "25-34", "35+"]
        )
        assert score > 0.7
        
        # Medium reusability - rating question
        score = retrieval_service._calculate_reusability_score(
            "Rate your satisfaction", "rating_scale", ["1", "2", "3", "4", "5"]
        )
        assert 0.4 < score <= 1.0
        
        # Low reusability - very specific question
        score = retrieval_service._calculate_reusability_score(
            "What do you think of our specific company product XYZ?", "text", []
        )
        assert score < 0.5
    
    def test_extract_research_goals_for_methodology(self, retrieval_service):
        """Test research goal extraction for methodologies"""
        # Test Van Westendorp
        goals = retrieval_service._extract_research_goals_for_methodology("vw")
        assert "pricing optimization" in goals
        assert "price sensitivity analysis" in goals
        
        # Test Conjoint
        goals = retrieval_service._extract_research_goals_for_methodology("conjoint")
        assert "feature prioritization" in goals
        assert "product optimization" in goals
        
        # Test unknown methodology
        goals = retrieval_service._extract_research_goals_for_methodology("unknown_method")
        assert "general research" in goals


if __name__ == "__main__":
    pytest.main([__file__])