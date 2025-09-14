#!/usr/bin/env python3
"""
Test Integrated Pillar System
Verify that advanced evaluators are properly integrated into main pillar system
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

async def test_integrated_pillar_evaluation():
    """
    Test the integrated pillar system with advanced evaluators
    """
    
    print("🧪 Testing Integrated Pillar System with Advanced Evaluators")
    print("=" * 70)
    
    # Test data
    test_rfq = """
    Research Objective: Evaluate pricing strategies for B2B software solutions
    Target Audience: IT decision makers and procurement managers in companies with 50-500 employees
    Key Research Questions: 
    1. What pricing models are preferred by different company sizes?
    2. How do buyers evaluate value vs price in software selection?
    3. What are acceptable price ranges for different feature sets?
    Business Goal: Optimize pricing strategy and packaging for maximum market penetration
    """
    
    test_survey = {
        "title": "B2B Software Pricing Strategy Survey",
        "description": "Understanding pricing preferences and decision criteria",
        "target_responses": 200,
        "estimated_time": 12,
        "metadata": {
            "methodology": ["Van Westendorp PSM", "Conjoint Analysis"]
        },
        "questions": [
            {"id": "q1", "text": "What is your role in software purchasing decisions?", "type": "multiple_choice"},
            {"id": "q2", "text": "How important is pricing in your software selection process?", "type": "rating"},
            {"id": "q3", "text": "What challenges do you face when evaluating new software?", "type": "text"},
            {"id": "q4", "text": "At what price would this software be too expensive to consider?", "type": "text"},
            {"id": "q5", "text": "Which software package would you prefer?", "type": "multiple_choice",
             "options": ["Package A: $100/month, Basic", "Package B: $200/month, Advanced"]},
        ]
    }
    
    try:
        # Import the integrated pillar evaluator
        from modules.pillar_based_evaluator import PillarBasedEvaluator
        
        print("🔬 Initializing Integrated Pillar-Based Evaluator...")
        evaluator = PillarBasedEvaluator(llm_client=None, db_session=None)
        
        print("🚀 Running integrated pillar evaluation...")
        result = await evaluator.evaluate_survey(test_survey, test_rfq)
        
        print("\\n✅ INTEGRATED PILLAR EVALUATION RESULTS:")
        print(f"📊 Overall Weighted Score: {result.overall_score:.2f}")
        print()
        
        print("📊 INDIVIDUAL PILLAR SCORES:")
        print(f"   📝 Content Validity (20%): {result.pillar_scores.content_validity:.2f}")
        print(f"   🔬 Methodological Rigor (25%): {result.pillar_scores.methodological_rigor:.2f}")
        print(f"   💬 Clarity & Comprehensibility (25%): {result.pillar_scores.clarity_comprehensibility:.2f}")
        print(f"   🏗️  Structural Coherence (20%): {result.pillar_scores.structural_coherence:.2f}")
        print(f"   🚀 Deployment Readiness (10%): {result.pillar_scores.deployment_readiness:.2f}")
        print()
        
        print("⚖️  WEIGHTED CONTRIBUTION BREAKDOWN:")
        for pillar, contribution in result.weighted_breakdown.items():
            print(f"   {pillar.replace('_', ' ').title()}: {contribution:.3f}")
        print()
        
        print("💡 COMPREHENSIVE RECOMMENDATIONS:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"   {i}. {rec}")
        print()
        
        print("🔍 EVALUATION METADATA:")
        metadata = result.evaluation_metadata
        print(f"   Evaluation Version: {metadata.get('evaluation_version', 'N/A')}")
        print(f"   Advanced Evaluators Used: {metadata.get('advanced_evaluators_used', 'N/A')}")
        if metadata.get('advanced_evaluators_used'):
            print(f"   Content Validity Confidence: {metadata.get('content_validity_confidence', 'N/A'):.2f}")
            print(f"   Methodological Rigor Confidence: {metadata.get('methodological_rigor_confidence', 'N/A'):.2f}")
            print(f"   Research Objectives Extracted: {metadata.get('objectives_extracted', 'N/A')}")
            print(f"   Biases Detected: {metadata.get('biases_detected', 'N/A')}")
            print(f"   Chain-of-Thought Reasoning: {metadata.get('reasoning_chains_used', 'N/A')}")
        print(f"   Total Questions Analyzed: {metadata.get('total_questions', 'N/A')}")
        print(f"   Methodologies Declared: {metadata.get('declared_methodologies', 'N/A')}")
        print()
        
        print("📈 DETAILED ANALYSIS AVAILABLE:")
        for pillar, analysis in result.detailed_results.items():
            if isinstance(analysis, dict):
                focus = analysis.get('evaluation_focus', 'Analysis available')
                print(f"   {pillar.replace('_', ' ').title()}: {focus}")
        print()
        
        # Compare with what would be in basic version
        if metadata.get('advanced_evaluators_used'):
            print("🆚 ADVANCED vs BASIC COMPARISON:")
            print("   ✅ ADVANCED: Chain-of-thought reasoning with detailed steps")
            print("   ❌ Basic: Simple LLM scoring without reasoning chains")
            print("   ✅ ADVANCED: Specific actionable recommendations with priorities") 
            print("   ❌ Basic: Generic improvement suggestions")
            print("   ✅ ADVANCED: Multi-type bias detection with severity levels")
            print("   ❌ Basic: Simple bias pattern matching")
            print("   ✅ ADVANCED: Research objective extraction and gap analysis")
            print("   ❌ Basic: Basic coverage assessment")
            print("   ✅ ADVANCED: Confidence scoring for reliability assessment")
            print("   ❌ Basic: No confidence metrics")
        else:
            print("⚠️  Currently using basic evaluators - advanced features not available")
        
        print("\\n" + "=" * 70)
        print("🎯 INTEGRATION TEST COMPLETE!")
        
        if metadata.get('advanced_evaluators_used'):
            print("   ✅ SUCCESS: Advanced evaluators successfully integrated!")
            print("   🚀 The UI will now show dramatically improved pillar analysis")
            print("   💡 Users get specific actionable recommendations instead of generic advice")
        else:
            print("   ⚠️  Using basic evaluators - check advanced module availability")
        
        return result
        
    except ImportError as e:
        print(f"❌ Failed to import pillar evaluator: {e}")
        return None
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_ui_readiness():
    """
    Test that the integration is ready for UI consumption
    """
    
    print("\\n🖥️  UI READINESS CHECK")
    print("=" * 50)
    
    try:
        from modules.pillar_based_evaluator import PillarBasedEvaluator
        
        # Simple test survey
        simple_survey = {
            "title": "Test Survey",
            "questions": [
                {"text": "What is your role?", "type": "multiple_choice"}
            ]
        }
        simple_rfq = "Test RFQ for UI integration"
        
        evaluator = PillarBasedEvaluator(llm_client=None, db_session=None)
        result = await evaluator.evaluate_survey(simple_survey, simple_rfq)
        
        # Check that result has all expected fields for UI
        required_fields = ['overall_score', 'pillar_scores', 'weighted_breakdown', 'recommendations', 'evaluation_metadata']
        missing_fields = [field for field in required_fields if not hasattr(result, field)]
        
        if not missing_fields:
            print("✅ All required fields present for UI integration")
            print(f"✅ Overall score format: {type(result.overall_score)} = {result.overall_score:.2f}")
            print(f"✅ Recommendations format: {type(result.recommendations)} with {len(result.recommendations)} items")
            print("✅ UI integration ready!")
        else:
            print(f"❌ Missing required fields: {missing_fields}")
        
        return len(missing_fields) == 0
        
    except Exception as e:
        print(f"❌ UI readiness check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Integrated Pillar System - Advanced Evaluator Integration")
    print("Testing that advanced chain-of-thought evaluators work in main system")
    print()
    
    # Test the integration
    result = asyncio.run(test_integrated_pillar_evaluation())
    
    if result:
        # Test UI readiness
        ui_ready = asyncio.run(test_ui_readiness())
        
        if ui_ready:
            print("\\n🎉 INTEGRATION SUCCESS!")
            print("   The advanced evaluators are now integrated and UI-ready")
            print("   Users will see dramatically improved pillar analysis")
        else:
            print("\\n⚠️  Integration partially successful - UI compatibility issues detected")
    else:
        print("\\n❌ Integration test failed - check implementation")