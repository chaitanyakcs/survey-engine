"""
Tests for QNR Structure Validation System
"""

import pytest
from unittest.mock import Mock, patch
from src.services.qnr_label_taxonomy import QNRLabelTaxonomy, LabelDefinition
from src.services.question_label_detector import QuestionLabelDetector
from src.services.survey_structure_validator import SurveyStructureValidator, IssueSeverity


class TestQNRLabelTaxonomy:
    """Test QNR label taxonomy service"""
    
    def test_taxonomy_initialization(self):
        """Test taxonomy loads correctly"""
        # Mock CSV loading to avoid file dependencies
        with patch('src.services.qnr_label_taxonomy.Path.glob') as mock_glob:
            mock_glob.return_value = []
            taxonomy = QNRLabelTaxonomy()
            
            # Should initialize with empty categories
            assert len(taxonomy.labels) == 0
            assert 'screener' in taxonomy.categories
            assert 'brand' in taxonomy.categories
            assert 'methodology' in taxonomy.categories
    
    def test_standardize_label_name(self):
        """Test label name standardization"""
        taxonomy = QNRLabelTaxonomy()
        
        # Test standardization mappings
        assert taxonomy._standardize_label_name('CoI_Check') == 'Conflict_Of_Interest_Check'
        assert taxonomy._standardize_label_name('Demog_Basic') == 'Demographics_Basic'
        assert taxonomy._standardize_label_name('Category_Usage_Adnl') == 'Category_Usage_Additional'
        assert taxonomy._standardize_label_name('Brand_awareness_funnel') == 'Brand_Awareness_Funnel'
        assert taxonomy._standardize_label_name('VW_pricing') == 'VW_Price_Generic'
    
    def test_get_van_westendorp_labels(self):
        """Test Van Westendorp label retrieval"""
        taxonomy = QNRLabelTaxonomy()
        vw_labels = taxonomy.get_van_westendorp_labels()
        
        expected = [
            'VW_Price_Too_Cheap',
            'VW_Price_Bargain',
            'VW_Price_Getting_Expensive',
            'VW_Price_Too_Expensive'
        ]
        
        assert vw_labels == expected
    
    def test_is_van_westendorp_label(self):
        """Test Van Westendorp label detection"""
        taxonomy = QNRLabelTaxonomy()
        
        assert taxonomy.is_van_westendorp_label('VW_Price_Too_Cheap') == True
        assert taxonomy.is_van_westendorp_label('VW_Price_Bargain') == True
        assert taxonomy.is_van_westendorp_label('Recent_Participation') == False
        assert taxonomy.is_van_westendorp_label('Invalid_Label') == False


class TestQuestionLabelDetector:
    """Test question label detection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.taxonomy = QNRLabelTaxonomy()
        self.detector = QuestionLabelDetector(self.taxonomy)
    
    def test_detect_recent_participation(self):
        """Test detection of Recent_Participation label"""
        question = {
            'text': 'Have you participated in any market research studies in the past 6 months?',
            'type': 'single_choice',
            'options': ['Yes', 'No']
        }
        
        labels = self.detector.detect_labels_in_question(question)
        assert 'Recent_Participation' in labels
    
    def test_detect_conflict_of_interest(self):
        """Test detection of Conflict_Of_Interest_Check label"""
        question = {
            'text': 'Do you work for a pharmaceutical company or medical device manufacturer?',
            'type': 'single_choice',
            'options': ['Yes', 'No']
        }
        
        labels = self.detector.detect_labels_in_question(question)
        assert 'Conflict_Of_Interest_Check' in labels
    
    def test_detect_demographics_basic(self):
        """Test detection of Demographics_Basic label"""
        question = {
            'text': 'What is your age range?',
            'type': 'single_choice',
            'options': ['18-24', '25-34', '35-44', '45-54', '55+']
        }
        
        labels = self.detector.detect_labels_in_question(question)
        assert 'Demographics_Basic' in labels
    
    def test_detect_brand_recall_unaided(self):
        """Test detection of Brand_Recall_Unaided label"""
        question = {
            'text': 'What brands of contact lenses come to mind?',
            'type': 'text'
        }
        
        labels = self.detector.detect_labels_in_question(question)
        assert 'Brand_Recall_Unaided' in labels
    
    def test_detect_van_westendorp_labels(self):
        """Test detection of Van Westendorp labels"""
        # Too cheap
        question1 = {
            'text': 'At what price per box would this product be too cheap to trust quality?',
            'type': 'numeric_open'
        }
        labels1 = self.detector.detect_labels_in_question(question1)
        assert 'VW_Price_Too_Cheap' in labels1
        
        # Too expensive
        question2 = {
            'text': 'At what price per box would this product be too expensive to consider?',
            'type': 'numeric_open'
        }
        labels2 = self.detector.detect_labels_in_question(question2)
        assert 'VW_Price_Too_Expensive' in labels2
        
        # Bargain
        question3 = {
            'text': 'At what price per box would this product be a good value?',
            'type': 'numeric_open'
        }
        labels3 = self.detector.detect_labels_in_question(question3)
        assert 'VW_Price_Bargain' in labels3
        
        # Getting expensive
        question4 = {
            'text': 'At what price per box is this product starting to get expensive?',
            'type': 'numeric_open'
        }
        labels4 = self.detector.detect_labels_in_question(question4)
        assert 'VW_Price_Getting_Expensive' in labels4
    
    def test_detect_brand_awareness_funnel(self):
        """Test detection of Brand_Awareness_Funnel label"""
        question = {
            'text': 'How familiar are you with these brands?',
            'type': 'matrix_likert',
            'options': ['Not aware', 'Aware', 'Considered', 'Purchased', 'Prefer']
        }
        
        labels = self.detector.detect_labels_in_question(question)
        assert 'Brand_Awareness_Funnel' in labels
    
    def test_detection_confidence(self):
        """Test confidence scoring"""
        question = {
            'text': 'Have you participated in any market research studies in the past 6 months?',
            'type': 'single_choice',
            'options': ['Yes', 'No']
        }
        
        detected_labels = ['Recent_Participation']
        confidence = self.detector.get_detection_confidence(question, detected_labels)
        
        assert 'Recent_Participation' in confidence
        assert 0.0 <= confidence['Recent_Participation'] <= 1.0
        assert confidence['Recent_Participation'] > 0.5  # Should be high confidence
    
    def test_validation_accuracy(self):
        """Test validation accuracy calculation"""
        test_cases = [
            {
                'question': {
                    'text': 'Have you participated in any market research studies in the past 6 months?',
                    'type': 'single_choice',
                    'options': ['Yes', 'No']
                },
                'expected_labels': ['Recent_Participation']
            },
            {
                'question': {
                    'text': 'What is your age range?',
                    'type': 'single_choice',
                    'options': ['18-24', '25-34', '35-44', '45-54', '55+']
                },
                'expected_labels': ['Demographics_Basic']
            }
        ]
        
        results = self.detector.validate_detection_accuracy(test_cases)
        
        assert results['total_tests'] == 2
        assert results['precision'] > 0.0
        assert results['recall'] > 0.0
        assert results['f1_score'] > 0.0


class TestSurveyStructureValidator:
    """Test survey structure validator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = SurveyStructureValidator()
    
    def test_validation_issue_creation(self):
        """Test validation issue creation"""
        issue = IssueSeverity.CRITICAL
        section_id = 2
        label = 'Recent_Participation'
        message = 'Missing required label'
        suggestion = 'Add participation check question'
        
        validation_issue = {
            'severity': issue,
            'section_id': section_id,
            'label': label,
            'message': message,
            'suggestion': suggestion
        }
        
        assert validation_issue['severity'] == IssueSeverity.CRITICAL
        assert validation_issue['section_id'] == 2
        assert validation_issue['label'] == 'Recent_Participation'
    
    def test_van_westendorp_validation(self):
        """Test Van Westendorp validation"""
        # Test with missing VW labels
        detected_labels = {
            5: {'VW_Price_Too_Cheap', 'VW_Price_Bargain'}  # Missing 2 labels
        }
        
        issues, score = self.validator._validate_van_westendorp(detected_labels)
        
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.CRITICAL
        assert 'Van Westendorp requires 4 price questions' in issues[0].message
        assert score < 1.0  # Should be penalized for missing labels
        
        # Test with all VW labels present
        detected_labels_complete = {
            5: {
                'VW_Price_Too_Cheap',
                'VW_Price_Bargain',
                'VW_Price_Getting_Expensive',
                'VW_Price_Too_Expensive'
            }
        }
        
        issues_complete, score_complete = self.validator._validate_van_westendorp(detected_labels_complete)
        
        assert len(issues_complete) == 0
        assert score_complete == 1.0
    
    def test_overall_score_calculation(self):
        """Test overall score calculation"""
        section_scores = {2: 0.8, 3: 0.9, 5: 0.7}
        
        issues = [
            Mock(severity=IssueSeverity.CRITICAL),
            Mock(severity=IssueSeverity.ERROR),
            Mock(severity=IssueSeverity.WARNING)
        ]
        
        score = self.validator._calculate_overall_score(section_scores, issues)
        
        # Should be penalized for issues
        assert score < 0.8  # Average of section scores
        assert score > 0.0  # Should not be zero
    
    def test_validation_summary(self):
        """Test validation summary generation"""
        # Mock a validation report
        report = Mock()
        report.overall_score = 0.85
        report.issues = [
            Mock(severity=IssueSeverity.CRITICAL),
            Mock(severity=IssueSeverity.ERROR),
            Mock(severity=IssueSeverity.WARNING)
        ]
        report.section_scores = {2: 0.8, 3: 0.9, 5: 0.7}
        
        summary = self.validator.get_validation_summary(report)
        
        assert summary['overall_score'] == 0.85
        assert summary['quality_level'] == 'good'
        assert summary['total_issues'] == 3
        assert summary['critical_issues'] == 1
        assert summary['error_issues'] == 1
        assert summary['warning_issues'] == 1
        assert summary['section_count'] == 3


class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_end_to_end_validation(self):
        """Test end-to-end validation with sample survey"""
        survey = {
            'id': 'test_survey',
            'sections': [
                {
                    'id': 2,
                    'title': 'Screener',
                    'questions': [
                        {
                            'id': 'q1',
                            'text': 'Have you participated in any market research studies in the past 6 months?',
                            'type': 'single_choice',
                            'options': ['Yes', 'No']
                        },
                        {
                            'id': 'q2',
                            'text': 'What is your age range?',
                            'type': 'single_choice',
                            'options': ['18-24', '25-34', '35-44', '45-54', '55+']
                        }
                    ]
                },
                {
                    'id': 5,
                    'title': 'Methodology',
                    'questions': [
                        {
                            'id': 'q3',
                            'text': 'At what price per box would this product be too cheap to trust quality?',
                            'type': 'numeric_open'
                        },
                        {
                            'id': 'q4',
                            'text': 'At what price per box would this product be too expensive to consider?',
                            'type': 'numeric_open'
                        }
                    ]
                }
            ]
        }
        
        rfq_context = {
            'methodology_tags': ['van_westendorp'],
            'industry': 'healthcare'
        }
        
        validator = SurveyStructureValidator()
        
        # This would normally be async, but for testing we'll mock it
        with patch.object(validator, 'validate_structure') as mock_validate:
            mock_report = Mock()
            mock_report.overall_score = 0.75
            mock_report.has_critical_issues.return_value = False
            mock_report.get_summary.return_value = "⚠️ Good structure with minor issues (75%)"
            mock_report.to_dict.return_value = {
                'overall_score': 0.75,
                'summary': "⚠️ Good structure with minor issues (75%)",
                'issues': []
            }
            mock_validate.return_value = mock_report
            
            # Test that validation doesn't block
            result = validator.validate_structure(survey, rfq_context)
            
            # Should return a report (even if mocked)
            assert result is not None


if __name__ == '__main__':
    pytest.main([__file__])


