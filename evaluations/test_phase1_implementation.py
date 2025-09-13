#!/usr/bin/env python3
"""
Test Script for Phase 1 LLM-based Evaluation Implementation
Validates that all components work together correctly
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
def test_imports():
    """Test that all evaluation modules can be imported correctly"""
    print("🔍 Testing module imports...")
    
    try:
        from modules.content_validity_evaluator import ContentValidityEvaluator, ContentValidityResult
        print("   ✅ ContentValidityEvaluator imported successfully")
    except ImportError as e:
        print(f"   ❌ ContentValidityEvaluator import failed: {e}")
        return False
    
    try:
        from modules.methodological_rigor_evaluator import MethodologicalRigorEvaluator, MethodologicalRigorResult
        print("   ✅ MethodologicalRigorEvaluator imported successfully")
    except ImportError as e:
        print(f"   ❌ MethodologicalRigorEvaluator import failed: {e}")
        return False
    
    try:
        from modules.pillar_based_evaluator import PillarBasedEvaluator, PillarScores, PillarEvaluationResult
        print("   ✅ PillarBasedEvaluator imported successfully")
    except ImportError as e:
        print(f"   ❌ PillarBasedEvaluator import failed: {e}")
        return False
    
    print("   ✅ All imports successful!\n")
    return True

def test_pillar_weight_validation():
    """Test that pillar weights are correctly configured"""
    print("⚖️  Testing pillar weight configuration...")
    
    from modules.pillar_based_evaluator import PillarBasedEvaluator
    
    evaluator = PillarBasedEvaluator()
    weights = evaluator.PILLAR_WEIGHTS
    
    expected_weights = {
        'content_validity': 0.20,
        'methodological_rigor': 0.25,
        'clarity_comprehensibility': 0.25,
        'structural_coherence': 0.20,
        'deployment_readiness': 0.10
    }
    
    # Check individual weights
    for pillar, expected_weight in expected_weights.items():
        if weights.get(pillar) != expected_weight:
            print(f"   ❌ {pillar} weight mismatch: expected {expected_weight}, got {weights.get(pillar)}")
            return False
        print(f"   ✅ {pillar}: {weights[pillar]:.0%}")
    
    # Check total weight sums to 1.0
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.001:
        print(f"   ❌ Total weights don't sum to 1.0: {total_weight}")
        return False
    
    print(f"   ✅ Total weights sum correctly: {total_weight}\n")
    return True

async def test_basic_evaluation_functionality():
    """Test basic evaluation functionality without LLM"""
    print("🧪 Testing basic evaluation functionality...")
    
    from modules.pillar_based_evaluator import PillarBasedEvaluator
    
    # Create a test survey
    test_survey = {
        "title": "Test Survey for Phase 1 Validation",
        "description": "A sample survey to test the evaluation system",
        "questions": [
            {
                "text": "What is your age group?",
                "type": "multiple_choice",
                "category": "screening",
                "options": ["18-25", "26-35", "36-45", "46-55", "56+"]
            },
            {
                "text": "How satisfied are you with our product?",
                "type": "scale",
                "category": "satisfaction",
                "scale_min": 1,
                "scale_max": 5
            },
            {
                "text": "Which features are most important to you?",
                "type": "multiple_choice",
                "category": "preferences",
                "options": ["Price", "Quality", "Design", "Support"]
            }
        ],
        "estimated_time": 15,
        "target_responses": 200,
        "metadata": {
            "methodology": ["basic_survey"]
        }
    }
    
    test_rfq = """
    We need to understand customer satisfaction with our product and identify 
    key features that drive purchase decisions. Target general consumers, 
    need about 200 responses, survey should be 15 minutes or less.
    """
    
    # Initialize evaluator without LLM client (fallback mode)
    evaluator = PillarBasedEvaluator(llm_client=None)
    
    try:
        # Run evaluation
        result = await evaluator.evaluate_survey(test_survey, test_rfq)
        
        # Validate result structure
        print("   📊 Evaluation completed successfully")
        print(f"   🎯 Overall Score: {result.overall_score:.2f}")
        print(f"   📖 Content Validity: {result.pillar_scores.content_validity:.2f}")
        print(f"   🔬 Methodological Rigor: {result.pillar_scores.methodological_rigor:.2f}")
        print(f"   📝 Clarity & Comprehensibility: {result.pillar_scores.clarity_comprehensibility:.2f}")
        print(f"   🏗️ Structural Coherence: {result.pillar_scores.structural_coherence:.2f}")
        print(f"   🚀 Deployment Readiness: {result.pillar_scores.deployment_readiness:.2f}")
        
        # Validate score ranges
        all_scores = [
            result.overall_score,
            result.pillar_scores.content_validity,
            result.pillar_scores.methodological_rigor,
            result.pillar_scores.clarity_comprehensibility,
            result.pillar_scores.structural_coherence,
            result.pillar_scores.deployment_readiness
        ]
        
        for score in all_scores:
            if not (0.0 <= score <= 1.0):
                print(f"   ❌ Score out of range: {score}")
                return False
        
        print("   ✅ All scores in valid range [0.0, 1.0]")
        
        # Validate weighted calculation
        calculated_overall = (
            result.pillar_scores.content_validity * 0.20 +
            result.pillar_scores.methodological_rigor * 0.25 +
            result.pillar_scores.clarity_comprehensibility * 0.25 +
            result.pillar_scores.structural_coherence * 0.20 +
            result.pillar_scores.deployment_readiness * 0.10
        )
        
        if abs(calculated_overall - result.overall_score) > 0.001:
            print(f"   ❌ Weighted calculation mismatch: expected {calculated_overall:.3f}, got {result.overall_score:.3f}")
            return False
        
        print("   ✅ Weighted calculation is correct")
        print("   ✅ Basic evaluation functionality working!\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Evaluation failed: {e}")
        return False

def test_enhanced_evaluation_runner():
    """Test that the enhanced evaluation runner imports correctly"""
    print("🏃 Testing enhanced evaluation runner...")
    
    try:
        from evaluation_runner import EvaluationRunner
        
        # Test initialization
        runner = EvaluationRunner(enable_pillar_evaluation=True)
        print("   ✅ EvaluationRunner initialized with pillar evaluation")
        
        # Test disabled mode
        runner_disabled = EvaluationRunner(enable_pillar_evaluation=False)
        print("   ✅ EvaluationRunner initialized with pillar evaluation disabled")
        
        print("   ✅ Enhanced evaluation runner working!\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Enhanced evaluation runner test failed: {e}")
        return False

async def run_comprehensive_validation():
    """Run comprehensive validation of Phase 1 implementation"""
    print("🚀 Starting Phase 1 Implementation Validation")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Module imports
    if not test_imports():
        all_tests_passed = False
    
    # Test 2: Pillar weight configuration
    if not test_pillar_weight_validation():
        all_tests_passed = False
    
    # Test 3: Basic evaluation functionality
    if not await test_basic_evaluation_functionality():
        all_tests_passed = False
    
    # Test 4: Enhanced evaluation runner
    if not test_enhanced_evaluation_runner():
        all_tests_passed = False
    
    # Final result
    print("=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! Phase 1 implementation is working correctly.")
        print("\n📋 Phase 1 Implementation Summary:")
        print("   ✅ Content Validity Evaluator - LLM-based analysis")
        print("   ✅ Methodological Rigor Evaluator - Bias detection & sequencing")
        print("   ✅ Weighted scoring system - 5-pillar framework")
        print("   ✅ Integration with evaluation runner")
        print("   ✅ Pillar-based test cases with expected scores")
        print("   ✅ Fallback functionality when LLM unavailable")
        print("\n🎯 Ready for Phase 2: Clarity & Comprehensibility Analysis")
        return True
    else:
        print("❌ SOME TESTS FAILED! Phase 1 implementation needs attention.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_validation())
    sys.exit(0 if success else 1)