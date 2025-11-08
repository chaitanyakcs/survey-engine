"""
Survey Structure Validator
Non-blocking validation that flags issues but never stops generation
"""

from typing import Dict, List, Optional, Set
import logging
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from src.services.qnr_label_service import QNRLabelService
from src.services.question_label_detector import QuestionLabelDetector

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Single validation issue"""
    severity: IssueSeverity
    section_id: Optional[int]
    label: str
    message: str
    suggestion: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'severity': self.severity.value,
            'section_id': self.section_id,
            'label': self.label,
            'message': self.message,
            'suggestion': self.suggestion
        }


@dataclass
class StructureValidationReport:
    """Non-blocking validation report"""
    survey_id: str
    overall_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    section_scores: Dict[int, float]
    detected_labels: Dict[int, Set[str]]
    missing_required_labels: Dict[int, List[str]]
    
    def is_high_quality(self) -> bool:
        """Check if survey meets quality threshold (non-blocking)"""
        return self.overall_score >= 0.85
    
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues (for flagging)"""
        return any(issue.severity == IssueSeverity.CRITICAL for issue in self.issues)
    
    def get_summary(self) -> str:
        """Human-readable summary"""
        if self.overall_score >= 0.90:
            return f"✅ Excellent structure ({self.overall_score:.0%})"
        elif self.overall_score >= 0.75:
            return f"⚠️ Good structure with minor issues ({self.overall_score:.0%})"
        elif self.overall_score >= 0.60:
            return f"⚠️ Acceptable structure with issues ({self.overall_score:.0%})"
        else:
            return f"❌ Poor structure - review recommended ({self.overall_score:.0%})"
    
    def get_critical_issues_summary(self) -> str:
        """Get summary of critical issues for flagging"""
        critical_issues = [issue for issue in self.issues if issue.severity == IssueSeverity.CRITICAL]
        if not critical_issues:
            return ""
        
        issue_summaries = []
        for issue in critical_issues[:3]:  # Limit to top 3
            section_name = self._get_section_name(issue.section_id)
            issue_summaries.append(f"{section_name}: {issue.message}")
        
        summary = "; ".join(issue_summaries)
        if len(critical_issues) > 3:
            summary += f" (+{len(critical_issues) - 3} more)"
        
        return summary
    
    def _get_section_name(self, section_id: Optional[int]) -> str:
        """Get human-readable section name"""
        section_names = {
            1: "Sample Plan",
            2: "Screener", 
            3: "Brand/Product Awareness",
            4: "Concept Exposure",
            5: "Methodology",
            6: "Additional Questions",
            7: "Programmer Instructions"
        }
        return section_names.get(section_id, f"Section {section_id}")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'survey_id': self.survey_id,
            'overall_score': self.overall_score,
            'summary': self.get_summary(),
            'is_high_quality': self.is_high_quality(),
            'has_critical_issues': self.has_critical_issues(),
            'critical_issues_summary': self.get_critical_issues_summary(),
            'issues': [issue.to_dict() for issue in self.issues],
            'section_scores': self.section_scores,
            'detected_labels': {str(k): list(v) for k, v in self.detected_labels.items()},
            'missing_required_labels': self.missing_required_labels
        }


class SurveyStructureValidator:
    """Non-blocking survey structure validation"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.qnr_service = QNRLabelService(db_session) if db_session else None
        self.detector = QuestionLabelDetector() if db_session else None
    
    async def validate_structure(self, survey_json: Dict, 
                                 rfq_context: Dict) -> StructureValidationReport:
        """
        Validate survey structure - NEVER blocks generation
        Returns quality score and flagged issues
        """
        try:
            issues = []
            section_scores = {}
            detected_labels = self.detector.detect_labels_in_survey(survey_json)
            missing_required = {}
            
            # Extract context
            methodology = rfq_context.get('methodology_tags', []) or []
            industry = rfq_context.get('industry')
            
            # Validate each section
            for section in survey_json.get('sections', []):
                section_id = section.get('id')
                section_issues, section_score, missing = self._validate_section(
                    section, detected_labels.get(section_id, set()), 
                    methodology, industry
                )
                issues.extend(section_issues)
                section_scores[section_id] = section_score
                if missing:
                    missing_required[section_id] = missing
            
            # Methodology-specific validation
            if 'van_westendorp' in [m.lower() for m in methodology]:
                vw_issues, vw_score = self._validate_van_westendorp(detected_labels)
                issues.extend(vw_issues)
                if 5 in section_scores:  # Methodology section
                    section_scores[5] = min(section_scores[5], vw_score)
                else:
                    section_scores[5] = vw_score
            
            # Gabor Granger validation
            if 'gabor_granger' in [m.lower() for m in methodology]:
                gg_issues, gg_score = self._validate_gabor_granger(detected_labels)
                issues.extend(gg_issues)
                if 5 in section_scores:  # Methodology section
                    section_scores[5] = min(section_scores[5], gg_score)
                else:
                    section_scores[5] = gg_score
            
            # Validate satisfaction scale format and positioning exclusion
            satisfaction_issues = self._validate_satisfaction_scales(survey_json)
            issues.extend(satisfaction_issues)
            
            positioning_issues = self._validate_positioning_exclusion(survey_json)
            issues.extend(positioning_issues)
            
            # Validate Brand_Awareness_Funnel format
            funnel_issues = self._validate_brand_awareness_funnel(survey_json)
            issues.extend(funnel_issues)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(section_scores, issues)
            
            return StructureValidationReport(
                survey_id=survey_json.get('id', 'unknown'),
                overall_score=overall_score,
                issues=issues,
                section_scores=section_scores,
                detected_labels=detected_labels,
                missing_required_labels=missing_required
            )
            
        except Exception as e:
            logger.error(f"Structure validation failed: {e}")
            # Return minimal report on error - don't block
            return StructureValidationReport(
                survey_id=survey_json.get('id', 'unknown'),
                overall_score=0.5,  # Neutral score
                issues=[ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    section_id=None,
                    label='Validation_Error',
                    message=f'Structure validation encountered an error: {str(e)}',
                    suggestion='Review survey manually'
                )],
                section_scores={},
                detected_labels={},
                missing_required_labels={}
            )
    
    def _validate_section(self, section: Dict, detected: Set[str],
                         methodology: List[str], industry: str) -> tuple:
        """Validate a single section"""
        issues = []
        section_id = section.get('id')
        
        # Special handling for Section 1 (Sample Plan) - should have samplePlanData, not questions
        if section_id == 1:
            if 'questions' in section:
                # Flag even empty questions array - Section 1 should not have questions field at all
                if section.get('questions'):
                    issues.append(ValidationIssue(
                        severity=IssueSeverity.ERROR,
                        section_id=1,
                        label='Sample_Plan_Structure',
                        message="Section 1 (Sample Plan) should have samplePlanData, not questions array",
                        suggestion="Remove questions array and use samplePlanData tabular structure"
                    ))
                else:
                    # Empty array is also wrong - should not have the field at all
                    issues.append(ValidationIssue(
                        severity=IssueSeverity.WARNING,
                        section_id=1,
                        label='Sample_Plan_Empty_Questions',
                        message="Section 1 (Sample Plan) should not have a 'questions' field at all (even if empty)",
                        suggestion="Remove the empty 'questions' field from Section 1"
                    ))
            if 'samplePlanData' not in section:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    section_id=1,
                    label='Sample_Plan_Missing',
                    message="Section 1 (Sample Plan) is missing samplePlanData table",
                    suggestion="Add samplePlanData with overallSample, subsamples, and quotas"
                ))
            else:
                # Validate samplePlanData structure
                sample_plan_issues = self._validate_sample_plan_data(section.get('samplePlanData', {}))
                issues.extend(sample_plan_issues)
            # Section 1 doesn't use question labels - return early
            return issues, 1.0 if not issues else 0.7, []
        
        # Get required labels for this section (deterministic filtering for validation)
        if not self.qnr_service:
            logger.warning("QNR service not available, skipping validation")
            return [], 1.0, []
        
        required_labels = self.qnr_service.get_required_labels(
            section_id, methodology, industry
        )
        
        # Check for missing required labels
        missing = []
        for label_dict in required_labels:
            label_name = label_dict['name']
            if label_name not in detected:
                missing.append(label_name)
                
                # Determine severity
                if self._is_critical_screener_label(label_name):
                    severity = IssueSeverity.CRITICAL
                elif label_name.startswith('VW_Price_'):
                    severity = IssueSeverity.ERROR
                elif label_name in ['Brand_Awareness_Funnel', 'Brand_Product_Satisfaction']:
                    severity = IssueSeverity.ERROR  # Changed to ERROR - these are mandatory
                elif label_name == 'Product_Satisfaction':
                    severity = IssueSeverity.WARNING
                else:
                    severity = IssueSeverity.WARNING
                
                issues.append(ValidationIssue(
                    severity=severity,
                    section_id=section_id,
                    label=label_name,
                    message=f"Missing required label: {label_name}",
                    suggestion=f"Add question for: {label_dict.get('description', '')}"
                ))
        
        # Calculate section score
        if required_labels:
            score = 1.0 - (len(missing) / len(required_labels))
        else:
            score = 1.0
        
        return issues, score, missing
    
    def _is_critical_screener_label(self, label_name: str) -> bool:
        """Check if a label is critical for screening"""
        critical_labels = [
            'Recent_Participation',
            'CoI_Check',
            'Category_Usage_Frequency',
            'Category_Usage_Financial',  # Added: Financial spending question is mandatory
            'Demog_Basic'
        ]
        return label_name in critical_labels
    
    def _validate_van_westendorp(self, detected_labels: Dict[int, Set[str]]) -> tuple:
        """Validate Van Westendorp 4-price requirement"""
        issues = []
        
        # Van Westendorp requires 4 price questions
        required_vw = ['VW_Price_Too_Expensive', 'VW_Price_Too_Cheap', 
                      'VW_Price_Expensive', 'VW_Price_Bargain']
        
        # Check methodology section (id=5)
        methodology_labels = detected_labels.get(5, set())
        missing_vw = [vw for vw in required_vw if vw not in methodology_labels]
        
        if missing_vw:
            issues.append(ValidationIssue(
                severity=IssueSeverity.CRITICAL,
                section_id=5,
                label='Van_Westendorp_Complete',
                message=f"Van Westendorp requires 4 price questions. Missing: {', '.join(missing_vw)}",
                suggestion="Add all 4 Van Westendorp price sensitivity questions in Methodology section"
            ))
            score = (len(required_vw) - len(missing_vw)) / len(required_vw)
        else:
            score = 1.0
        
        return issues, score
    
    def _validate_gabor_granger(self, detected_labels: Dict[int, Set[str]]) -> tuple:
        """Validate Gabor Granger requirements"""
        issues = []
        
        # Check methodology section (id=5)
        methodology_labels = detected_labels.get(5, set())
        
        if 'GG_Price_Acceptance' not in methodology_labels:
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                section_id=5,
                label='Gabor_Granger_Complete',
                message="Gabor Granger methodology requires sequential price acceptance questions",
                suggestion="Add Gabor Granger price acceptance questions in Methodology section"
            ))
            score = 0.0
        else:
            score = 1.0
        
        return issues, score
    
    def _calculate_overall_score(self, section_scores: Dict[int, float], 
                                 issues: List[ValidationIssue]) -> float:
        """Calculate overall structure quality score"""
        # Average section scores
        if section_scores:
            avg_score = sum(section_scores.values()) / len(section_scores)
        else:
            avg_score = 1.0
        
        # Penalty for critical issues
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
        
        # Calculate penalty
        penalty = (critical_count * 0.15) + (error_count * 0.05) + (warning_count * 0.02)
        
        return max(0.0, min(1.0, avg_score - penalty))
    
    def get_validation_summary(self, report: StructureValidationReport) -> Dict:
        """Get a summary of validation results for logging/display"""
        return {
            'survey_id': report.survey_id,
            'overall_score': report.overall_score,
            'quality_level': self._get_quality_level(report.overall_score),
            'total_issues': len(report.issues),
            'critical_issues': len([i for i in report.issues if i.severity == IssueSeverity.CRITICAL]),
            'error_issues': len([i for i in report.issues if i.severity == IssueSeverity.ERROR]),
            'warning_issues': len([i for i in report.issues if i.severity == IssueSeverity.WARNING]),
            'section_count': len(report.section_scores),
            'average_section_score': sum(report.section_scores.values()) / len(report.section_scores) if report.section_scores else 0.0
        }
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level description"""
        if score >= 0.90:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.60:
            return "acceptable"
        else:
            return "poor"
    
    def _validate_satisfaction_scales(self, survey_json: Dict) -> List[ValidationIssue]:
        """Validate that Brand_Product_Satisfaction questions use 1-5 scale with text labels"""
        issues = []
        
        for section in survey_json.get('sections', []):
            section_id = section.get('id')
            if section_id != 3:  # Only check Brand/Product Awareness section
                continue
                
            for question in section.get('questions', []):
                # Check if this is a satisfaction question
                question_text = question.get('text', '').lower()
                if 'satisfaction' in question_text or 'satisfied' in question_text:
                    question_type = question.get('type', '')
                    options = question.get('options', [])
                    scale_labels = question.get('scale_labels', {})
                    
                    # Check if it's a scale question
                    if question_type == 'scale':
                        # Validate 1-5 scale
                        if options != ['1', '2', '3', '4', '5']:
                            issues.append(ValidationIssue(
                                severity=IssueSeverity.ERROR,
                                section_id=section_id,
                                label='Satisfaction_Scale_Format',
                                message=f"Satisfaction question should use 1-5 scale, found: {options}",
                                suggestion="Use options: ['1', '2', '3', '4', '5'] with scale_labels"
                            ))
                        
                        # Validate scale_labels
                        expected_labels = {
                            '1': 'Very Dissatisfied',
                            '2': 'Dissatisfied',
                            '3': 'Neutral',
                            '4': 'Satisfied',
                            '5': 'Very Satisfied'
                        }
                        if scale_labels != expected_labels:
                            issues.append(ValidationIssue(
                                severity=IssueSeverity.ERROR,
                                section_id=section_id,
                                label='Satisfaction_Scale_Labels',
                                message=f"Satisfaction question missing correct scale_labels",
                                suggestion=f"Add scale_labels: {expected_labels}"
                            ))
        
        return issues
    
    def _validate_positioning_exclusion(self, survey_json: Dict) -> List[ValidationIssue]:
        """Validate that positioning questions are NOT in Section 5 (Methodology)"""
        issues = []
        
        for section in survey_json.get('sections', []):
            section_id = section.get('id')
            if section_id != 5:  # Only check Methodology section
                continue
                
            for question in section.get('questions', []):
                question_text = question.get('text', '').lower()
                # Check for positioning-related keywords
                positioning_keywords = ['positioning', 'position', 'position statement', 'brand position']
                if any(keyword in question_text for keyword in positioning_keywords):
                    issues.append(ValidationIssue(
                        severity=IssueSeverity.WARNING,
                        section_id=section_id,
                        label='Positioning_In_Methodology',
                        message="Positioning question found in Section 5 (Methodology) - should not be system-generated",
                        suggestion="Remove positioning questions from Methodology section. Positioning should only come from user-provided content in Concept Reaction (Section 4)"
                    ))
        
        return issues
    
    def _validate_brand_awareness_funnel(self, survey_json: Dict) -> List[ValidationIssue]:
        """Validate that Brand_Awareness_Funnel is a matrix_likert question with proper stages"""
        issues = []
        
        for section in survey_json.get('sections', []):
            section_id = section.get('id')
            if section_id != 3:  # Only check Brand/Product Awareness section
                continue
                
            for question in section.get('questions', []):
                question_text = question.get('text', '').lower()
                # Check if this is a brand awareness funnel question
                if any(keyword in question_text for keyword in ['aware', 'considered', 'purchased', 'continue', 'prefer']):
                    question_type = question.get('type', '')
                    
                    # Should be matrix_likert
                    if question_type != 'matrix_likert':
                        issues.append(ValidationIssue(
                            severity=IssueSeverity.ERROR,
                            section_id=section_id,
                            label='Brand_Awareness_Funnel_Format',
                            message=f"Brand_Awareness_Funnel should be matrix_likert type, found: {question_type}",
                            suggestion="Change question type to 'matrix_likert' with brands as rows and funnel stages (Aware, Considered, Purchased, Continue, Preferred) as options"
                        ))
                    else:
                        # Check for proper stages
                        options = question.get('options', [])
                        required_stages = ['aware', 'considered', 'purchased']
                        options_lower = [opt.lower() for opt in options]
                        missing_stages = [stage for stage in required_stages if not any(stage in opt for opt in options_lower)]
                        
                        if missing_stages:
                            issues.append(ValidationIssue(
                                severity=IssueSeverity.WARNING,
                                section_id=section_id,
                                label='Brand_Awareness_Funnel_Stages',
                                message=f"Brand_Awareness_Funnel missing stages: {', '.join(missing_stages)}",
                                suggestion="Include all funnel stages: Aware → Considered → Purchased → Continue → Preferred"
                            ))
        
        return issues
    
    def validate_single_question(self, question: Dict, section_id: int) -> List[ValidationIssue]:
        """Validate a single question for label compliance"""
        issues = []
        if not self.detector or not self.qnr_service:
            return issues
        
        detected_labels = self.detector.detect_labels_in_question(question)
        
        # Get required labels for this section (no context - basic check only)
        required_labels = self.qnr_service.get_required_labels(section_id)
        
        # Check if any required labels are missing
        for label_dict in required_labels:
            label_name = label_dict['name']
            if label_name not in detected_labels and label_dict.get('mandatory'):
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    section_id=section_id,
                    label=label_name,
                    message=f"Question may be missing required label: {label_name}",
                    suggestion=f"Consider adding: {label_dict.get('description', '')}"
                ))
        
        return issues
    
    def _validate_sample_plan_data(self, sample_plan_data: Dict) -> List[ValidationIssue]:
        """Validate samplePlanData structure"""
        issues = []
        
        if not sample_plan_data:
            return [ValidationIssue(
                severity=IssueSeverity.ERROR,
                section_id=1,
                label='Sample_Plan_Empty',
                message="samplePlanData is empty",
                suggestion="Add overallSample with totalSize and demographic breakdowns"
            )]
        
        # Check overallSample
        overall_sample = sample_plan_data.get('overallSample', {})
        if not overall_sample:
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                section_id=1,
                label='Overall_Sample_Missing',
                message="samplePlanData missing overallSample",
                suggestion="Add overallSample with totalSize and demographic breakdowns"
            ))
        else:
            if 'totalSize' not in overall_sample:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    section_id=1,
                    label='Total_Size_Missing',
                    message="overallSample missing totalSize",
                    suggestion="Add totalSize field with overall sample size"
                ))
            
            # Check for demographic breakdowns
            has_demographics = any([
                overall_sample.get('ageGroups'),
                overall_sample.get('gender'),
                overall_sample.get('income'),
                overall_sample.get('otherDemographics')
            ])
            if not has_demographics:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    section_id=1,
                    label='Demographics_Missing',
                    message="overallSample missing demographic breakdowns",
                    suggestion="Add ageGroups, gender, income, or otherDemographics"
                ))
        
        # Validate subsamples if present
        subsamples = sample_plan_data.get('subsamples', [])
        for idx, subsample in enumerate(subsamples):
            if 'name' not in subsample:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    section_id=1,
                    label=f'Subsample_{idx}_Name_Missing',
                    message=f"Subsample {idx+1} missing name",
                    suggestion="Add name field for subsample"
                ))
            if 'totalSize' not in subsample:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    section_id=1,
                    label=f'Subsample_{idx}_Size_Missing',
                    message=f"Subsample {idx+1} missing totalSize",
                    suggestion="Add totalSize field for subsample"
                ))
        
        return issues


