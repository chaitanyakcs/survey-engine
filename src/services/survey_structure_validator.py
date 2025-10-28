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
                elif label_name in ['Brand_Awareness_Funnel', 'Product_Satisfaction']:
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


