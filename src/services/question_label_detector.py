"""
Question Label Detector
Deterministic rule-based pattern matching for QNR label detection
"""

from typing import Dict, List, Set, Optional
import re
import logging

logger = logging.getLogger(__name__)


class QuestionLabelDetector:
    """Deterministic rule-based label detection"""
    
    def __init__(self, qnr_service=None):
        # qnr_service is optional for future enhancements
        # Currently detection is purely pattern-based
        self.qnr_service = qnr_service
        self.patterns = self._build_detection_patterns()
    
    def _build_detection_patterns(self) -> Dict[str, List[Dict]]:
        """Build detection patterns for each label"""
        return {
            'Study_Intro': [
                {'keywords': ['thank you', 'participating', 'research study', 'survey will take', 'confidential']},
                {'label_type': 'Text'},
            ],
            'Recent_Participation': [
                {'keywords': ['participated', 'market research', 'recent study', 'past 6 months', 'last 6 months', 'research studies']},
                {'question_type': 'single_choice'},
                {'negative_keywords': ['never', 'not participated']},  # Must NOT be negative
            ],
            'Conflict_Of_Interest_Check': [
                {'keywords': ['work for', 'employed by', 'conflict of interest', 'employee of', 'work in', 'employed in']},
                {'context': ['company', 'industry', 'competitor', 'pharmaceutical', 'medical device']},
            ],
            'Demographics_Basic': [
                {'keywords': ['age', 'gender', 'male', 'female', 'age range', 'age group', 'years old']},
                {'question_type': ['single_choice', 'multiple_choice']},
            ],
            'Medical_Conditions_General': [
                {'keywords': ['medical condition', 'health condition', 'diagnosed', 'suffering from', 'have you been diagnosed']},
                {'context': ['healthcare', 'medical', 'health']},
            ],
            'Medical_Conditions_Study': [
                {'keywords': ['current', 'past', 'future', 'currently have', 'previously had', 'plan to']},
                {'context': ['medical condition', 'health condition']},
            ],
            'Category_Usage_Frequency': [
                {'keywords': ['how often', 'frequency', 'regularly', 'daily', 'weekly', 'monthly', 'use']},
                {'context': ['product', 'category', 'brand']},
            ],
            'Category_Usage_Financial': [
                {'keywords': ['spend', 'spending', 'cost', 'price', 'budget', 'money', 'financial']},
                {'context': ['product', 'category', 'monthly', 'annually']},
            ],
            'Category_Usage_Additional': [
                {'keywords': ['where', 'how', 'additional', 'other', 'else', 'besides']},
                {'context': ['use', 'purchase', 'buy']},
            ],
            'Category_Usage_Consideration': [
                {'keywords': ['considering', 'plan to', 'intend to', 'thinking about', 'future']},
                {'context': ['purchase', 'buy', 'product']},
            ],
            'User_Category_Rules': [
                {'keywords': ['user', 'non-user', 'continue', 'terminate', 'categorization', 'classification']},
                {'label_type': 'Rules'},
            ],
            'Confidentiality_Agreement': [
                {'keywords': ['confidential', 'privacy', 'data protection', 'personal information', 'agreement']},
                {'label_type': 'Text'},
            ],
            'Product_Usage': [
                {'keywords': ['products do you use', 'currently use', 'experience with', 'usage patterns']},
                {'label_type': 'Text'},
            ],
            'Product_Usage_Frequency': [
                {'keywords': ['frequency of usage', 'how often do you', 'purchase frequency', 'usage patterns']},
                {'context': ['product', 'brand']},
            ],
            'Product_Usage_Financial': [
                {'keywords': ['how much do you spend', 'spending on', 'financial', 'subscription', 'channel']},
                {'context': ['product', 'brand', 'purchase']},
            ],
            'Purchase_Decision_Influence': [
                {'keywords': ['who influences', 'decision maker', 'influence', 'decide', 'chooses']},
                {'context': ['purchase', 'buying']},
            ],
            'Brand_Recall_Unaided': [
                {'keywords': ['brands', 'think of', 'top of mind', 'come to mind', 'aware of brands', 'name brands']},
                {'negative_keywords': ['list', 'shown', 'mentioned', 'displayed']},  # Must NOT have these (unaided)
                {'question_type': 'text'},
            ],
            'Brand_Awareness_Funnel': [
                {'keywords': ['aware', 'considered', 'purchased', 'continue', 'prefer', 'familiar with']},
                {'question_type': 'matrix_likert'},
                {'min_options': 4},  # Must have multiple stages
                {'context': ['brand', 'product']},
            ],
            'Product_Satisfaction': [
                {'keywords': ['satisfied', 'satisfaction', 'rate', 'evaluate', 'experience', 'opinion']},
                {'context': ['product', 'brand', 'service']},
            ],
            'Concept_Intro': [
                {'keywords': ['concept', 'product concept', 'please review', 'carefully', 'introduction']},
                {'label_type': 'Text'},
            ],
            'Message_Reaction': [
                {'keywords': ['preference', 'reaction', 'appealing', 'attractive', 'interesting']},
                {'context': ['product', 'feature', 'name', 'caption']},
            ],
            'Concept_Impression': [
                {'keywords': ['overall impression', 'first impression', 'initial reaction', 'general feeling']},
                {'context': ['concept', 'product']},
            ],
            'Concept_Feature_Highlight': [
                {'keywords': ['most important', 'least important', 'highlight', 'stand out', 'key features']},
                {'context': ['concept', 'description', 'words', 'phrases']},
            ],
            'Concept_Evaluation_Funnel': [
                {'keywords': ['follow up', 'learn more', 'new and different', 'meets needs', 'recommend']},
                {'question_type': 'matrix_likert'},
            ],
            'Concept_Purchase_Likelihood': [
                {'keywords': ['likely to purchase', 'purchase likelihood', 'how soon', 'when would you']},
                {'context': ['concept', 'product']},
            ],
            'VW_Price_Too_Cheap': [
                {'keywords': ['too cheap', 'too inexpensive', 'suspiciously cheap', 'unreasonably cheap']},
                {'question_type': 'numeric_open'},
                {'context': ['price', 'cost', 'value']},
            ],
            'VW_Price_Bargain': [
                {'keywords': ['bargain', 'good value', 'great deal', 'good price', 'reasonable price']},
                {'question_type': 'numeric_open'},
                {'context': ['price', 'cost', 'value']},
            ],
            'VW_Price_Getting_Expensive': [
                {'keywords': ['getting expensive', 'starting to expensive', 'bit expensive', 'becoming expensive']},
                {'question_type': 'numeric_open'},
                {'context': ['price', 'cost']},
            ],
            'VW_Price_Too_Expensive': [
                {'keywords': ['too expensive', 'prohibitively expensive', 'cannot afford', 'unaffordable']},
                {'question_type': 'numeric_open'},
                {'context': ['price', 'cost']},
            ],
            'VW_Purchase_Likelihood': [
                {'keywords': ['purchase likelihood', 'likely to buy', 'probability', 'chance']},
                {'context': ['chosen price', 'price point']},
            ],
            'GG_Price_Acceptance': [
                {'keywords': ['accept this price', 'willing to pay', 'price acceptable', 'random price']},
                {'context': ['gabor', 'granger', 'sequential']},
            ],
            'Additional_Demographics': [
                {'keywords': ['education', 'employment', 'salary', 'income', 'ethnicity', 'race']},
                {'context': ['demographic', 'background']},
            ],
            'Adoption_Behavior': [
                {'keywords': ['adopt', 'adoption', 'new products', 'technology', 'early adopter']},
                {'context': ['behavior', 'tendency']},
            ],
            'Media_Consumption': [
                {'keywords': ['platform', 'social media', 'television', 'radio', 'internet', 'consume']},
                {'context': ['information', 'content', 'media']},
            ],
            'Additional_Awareness': [
                {'keywords': ['aware of', 'familiar with', 'heard of', 'knowledge of']},
                {'context': ['features', 'technology', 'innovations']},
            ],
        }
    
    def detect_labels_in_question(self, question: Dict) -> List[str]:
        """Detect applicable labels for a single question (deterministic)"""
        detected = []
        q_text = question.get('text', '').lower()
        q_type = question.get('type', '')
        q_options = question.get('options', [])
        
        for label_name, patterns in self.patterns.items():
            if self._matches_patterns(q_text, q_type, q_options, patterns):
                detected.append(label_name)
        
        return detected
    
    def _matches_patterns(self, text: str, q_type: str, options: List, 
                         patterns: List[Dict]) -> bool:
        """Check if question matches all pattern requirements"""
        for pattern in patterns:
            # Keyword matching
            if 'keywords' in pattern:
                if not any(kw in text for kw in pattern['keywords']):
                    return False
            
            # Negative keywords (must NOT be present)
            if 'negative_keywords' in pattern:
                if any(kw in text for kw in pattern['negative_keywords']):
                    return False
            
            # Question type matching
            if 'question_type' in pattern:
                if isinstance(pattern['question_type'], list):
                    if q_type not in pattern['question_type']:
                        return False
                else:
                    if q_type != pattern['question_type']:
                        return False
            
            # Context keywords (additional required terms)
            if 'context' in pattern:
                if not any(ctx in text for ctx in pattern['context']):
                    return False
            
            # Minimum options count
            if 'min_options' in pattern:
                if len(options) < pattern['min_options']:
                    return False
            
            # Label type matching
            if 'label_type' in pattern:
                # This would need to be passed from the question context
                # For now, skip this check
                pass
        
        return True
    
    def detect_labels_in_section(self, section: Dict) -> Set[str]:
        """Detect all labels in a section"""
        all_labels = set()
        
        # Check text blocks
        for text_block in section.get('textBlocks', []):
            if isinstance(text_block, dict):
                text_content = text_block.get('content', '').lower()
                for label_name, patterns in self.patterns.items():
                    if self._matches_patterns(text_content, 'text', [], patterns):
                        all_labels.add(label_name)
        
        # Check intro text
        intro_text = section.get('introText', {})
        if isinstance(intro_text, dict):
            text_content = intro_text.get('content', '').lower()
            for label_name, patterns in self.patterns.items():
                if self._matches_patterns(text_content, 'text', [], patterns):
                    all_labels.add(label_name)
        
        # Check questions
        for question in section.get('questions', []):
            labels = self.detect_labels_in_question(question)
            all_labels.update(labels)
        
        return all_labels
    
    def detect_labels_in_survey(self, survey: Dict) -> Dict[int, Set[str]]:
        """Detect labels across entire survey, grouped by section"""
        section_labels = {}
        for section in survey.get('sections', []):
            section_id = section.get('id')
            section_labels[section_id] = self.detect_labels_in_section(section)
        return section_labels
    
    def get_detection_confidence(self, question: Dict, detected_labels: List[str]) -> Dict[str, float]:
        """Get confidence scores for detected labels (0.0 to 1.0)"""
        confidence_scores = {}
        
        for label_name in detected_labels:
            patterns = self.patterns.get(label_name, [])
            if not patterns:
                confidence_scores[label_name] = 0.5  # Default confidence
                continue
            
            # Calculate confidence based on pattern matches
            q_text = question.get('text', '').lower()
            q_type = question.get('type', '')
            q_options = question.get('options', [])
            
            match_score = 0.0
            total_patterns = len(patterns)
            
            for pattern in patterns:
                pattern_score = 0.0
                
                # Keyword matching (weight: 0.4)
                if 'keywords' in pattern:
                    keyword_matches = sum(1 for kw in pattern['keywords'] if kw in q_text)
                    if keyword_matches > 0:
                        pattern_score += 0.4 * min(keyword_matches / len(pattern['keywords']), 1.0)
                
                # Question type matching (weight: 0.3)
                if 'question_type' in pattern:
                    if isinstance(pattern['question_type'], list):
                        if q_type in pattern['question_type']:
                            pattern_score += 0.3
                    else:
                        if q_type == pattern['question_type']:
                            pattern_score += 0.3
                
                # Context matching (weight: 0.2)
                if 'context' in pattern:
                    context_matches = sum(1 for ctx in pattern['context'] if ctx in q_text)
                    if context_matches > 0:
                        pattern_score += 0.2 * min(context_matches / len(pattern['context']), 1.0)
                
                # Options count (weight: 0.1)
                if 'min_options' in pattern:
                    if len(q_options) >= pattern['min_options']:
                        pattern_score += 0.1
                
                match_score += pattern_score
            
            confidence_scores[label_name] = min(match_score / total_patterns, 1.0)
        
        return confidence_scores
    
    def validate_detection_accuracy(self, test_cases: List[Dict]) -> Dict[str, float]:
        """Validate detection accuracy against test cases"""
        results = {
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'total_tests': len(test_cases),
            'correct_detections': 0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        if not test_cases:
            return results
        
        correct = 0
        false_positives = 0
        false_negatives = 0
        
        for test_case in test_cases:
            question = test_case.get('question', {})
            expected_labels = set(test_case.get('expected_labels', []))
            
            detected_labels = set(self.detect_labels_in_question(question))
            
            # Count correct detections
            correct += len(expected_labels.intersection(detected_labels))
            
            # Count false positives
            false_positives += len(detected_labels - expected_labels)
            
            # Count false negatives
            false_negatives += len(expected_labels - detected_labels)
        
        results['correct_detections'] = correct
        results['false_positives'] = false_positives
        results['false_negatives'] = false_negatives
        
        # Calculate precision and recall
        if correct + false_positives > 0:
            results['precision'] = correct / (correct + false_positives)
        
        if correct + false_negatives > 0:
            results['recall'] = correct / (correct + false_negatives)
        
        # Calculate F1 score
        if results['precision'] + results['recall'] > 0:
            results['f1_score'] = (2 * results['precision'] * results['recall']) / (results['precision'] + results['recall'])
        
        return results


