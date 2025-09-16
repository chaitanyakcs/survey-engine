"""
Survey Engine Evaluation Framework
Advanced pillar-based evaluation system for survey quality assessment
"""

from .modules.pillar_based_evaluator import PillarBasedEvaluator, PillarScores, PillarEvaluationResult
from .modules.content_validity_evaluator import ContentValidityEvaluator, ContentValidityResult
from .modules.methodological_rigor_evaluator import MethodologicalRigorEvaluator, MethodologicalRigorResult

# Advanced evaluators (if available)
try:
    from .modules.advanced_content_validity_evaluator import AdvancedContentValidityEvaluator, AdvancedContentValidityResult
    from .modules.advanced_methodological_rigor_evaluator import AdvancedMethodologicalRigorEvaluator, AdvancedMethodologicalRigorResult
    ADVANCED_EVALUATORS_AVAILABLE = True
except ImportError:
    ADVANCED_EVALUATORS_AVAILABLE = False

__all__ = [
    'PillarBasedEvaluator',
    'PillarScores', 
    'PillarEvaluationResult',
    'ContentValidityEvaluator',
    'ContentValidityResult',
    'MethodologicalRigorEvaluator',
    'MethodologicalRigorResult',
    'ADVANCED_EVALUATORS_AVAILABLE'
]

# Add advanced evaluators to __all__ if available
if ADVANCED_EVALUATORS_AVAILABLE:
    __all__.extend([
        'AdvancedContentValidityEvaluator',
        'AdvancedContentValidityResult',
        'AdvancedMethodologicalRigorEvaluator', 
        'AdvancedMethodologicalRigorResult'
    ])
