#!/usr/bin/env python3
"""
Test Advanced Content Validity Evaluator
Compare basic vs advanced evaluation approaches
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

async def test_advanced_vs_basic():
    """
    Compare basic vs advanced content validity evaluation
    """
    
    print("🧪 Testing Advanced Content Validity Evaluator")
    print("=" * 60)
    
    # Test data
    test_rfq = """
    Research Objective: Evaluate B2B software selection criteria for mid-sized companies
    Target Audience: IT decision makers and procurement managers  
    Key Research Questions: 
    1. What factors influence software purchasing decisions?
    2. How do companies evaluate vendor credibility?
    3. What are the main barriers to software adoption?
    4. How important is pricing vs features in decision making?
    Business Goal: Understand the B2B software market to improve our product positioning
    """
    
    test_survey = {
        "title": "B2B Software Selection Survey",
        "description": "Understanding software selection criteria",
        "questions": [
            {"id": "q1", "text": "What is your role in software selection?", "type": "multiple_choice"},
            {"id": "q2", "text": "How important is price in your software decisions?", "type": "rating"},
            {"id": "q3", "text": "What challenges do you face with new software?", "type": "text"},
            {"id": "q4", "text": "How do you research software vendors?", "type": "multiple_choice"}
        ]
    }
    
    try:
        # Import the advanced evaluator
        from modules.advanced_content_validity_evaluator import AdvancedContentValidityEvaluator
        
        print("🔬 Initializing Advanced Content Validity Evaluator...")
        evaluator = AdvancedContentValidityEvaluator(llm_client=None, db_session=None)
        
        print("🚀 Running advanced evaluation (fallback mode)...")
        result = await evaluator.evaluate_content_validity(test_survey, test_rfq)
        
        print("\n✅ ADVANCED EVALUATION RESULTS:")
        print(f"📊 Overall Score: {result.overall_score:.2f}")
        print(f"🎯 Confidence: {result.confidence_score:.2f}")
        print(f"🧠 Objectives Extracted: {len(result.research_objectives)}")
        print(f"🔗 Question Mappings: {len(result.question_mappings)}")
        print(f"⚠️  Critical Gaps: {len(result.gap_analysis.critical_gaps)}")
        print(f"💡 Recommendations: {len(result.specific_recommendations)}")
        
        print("\n🧠 REASONING CHAIN:")
        for i, step in enumerate(result.reasoning_chain, 1):
            print(f"   {i}. {step}")
        
        print("\n🎯 RESEARCH OBJECTIVES IDENTIFIED:")
        for obj in result.research_objectives:
            print(f"   • {obj.text} ({obj.category}, priority: {obj.priority:.1f})")
        
        print("\n🔗 QUESTION-OBJECTIVE MAPPINGS:")
        for mapping in result.question_mappings:
            print(f"   • Q: '{mapping.question_text[:40]}...'")
            print(f"     Objectives: {len(mapping.mapped_objectives)}, Quality: {mapping.coverage_quality:.2f}")
        
        print("\n⚠️  GAP ANALYSIS:")
        if result.gap_analysis.missing_objectives:
            print("   Missing Objectives:")
            for obj in result.gap_analysis.missing_objectives:
                print(f"     - {obj.text}")
        
        if result.gap_analysis.critical_gaps:
            print("   Critical Gaps:")
            for gap in result.gap_analysis.critical_gaps:
                print(f"     - {gap}")
        
        print("\n💡 SPECIFIC RECOMMENDATIONS:")
        for i, rec in enumerate(result.specific_recommendations[:3], 1):  # Show first 3
            print(f"   {i}. {rec.get('issue', 'N/A')}")
            print(f"      Priority: {rec.get('priority', 'N/A')}")
            if rec.get('suggested_questions'):
                print(f"      Suggested: {rec['suggested_questions'][0]}")
        
        print(f"\n📈 EVALUATION METADATA:")
        for key, value in result.evaluation_metadata.items():
            print(f"   {key}: {value}")
        
        print("\n" + "=" * 60)
        print("🎯 ADVANCED EVALUATION COMPLETE!")
        print("   This demonstrates sophisticated analysis vs basic scoring")
        print("   Next: Add LLM token for even more detailed reasoning")
        
        return result
        
    except ImportError as e:
        print(f"❌ Failed to import advanced evaluator: {e}")
        return None
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return None

async def compare_with_basic():
    """
    Compare advanced evaluator with basic approach
    """
    
    print("\n🔄 COMPARISON: Advanced vs Basic Evaluation")
    print("=" * 60)
    
    try:
        # Import basic evaluator for comparison
        from modules.content_validity_evaluator import ContentValidityEvaluator
        
        test_rfq = "Research Goal: Understand B2B software selection criteria"
        test_survey = {
            "questions": [
                {"text": "What is your role?", "type": "multiple_choice"},
                {"text": "How important is price?", "type": "rating"}
            ]
        }
        
        basic_evaluator = ContentValidityEvaluator(llm_client=None, db_session=None)
        
        print("📊 Running basic evaluation...")
        # Note: This will use fallback heuristics
        basic_result = await basic_evaluator.evaluate_content_validity(test_survey, test_rfq)
        
        print(f"📊 Basic Score: {basic_result.score:.2f}")
        print(f"💡 Basic Recommendations: {len(basic_result.recommendations)}")
        print(f"🔍 Analysis Depth: Basic heuristics")
        
        print("\n📈 ADVANCED vs BASIC COMPARISON:")
        print("   Advanced: Detailed objective extraction, semantic analysis")
        print("   Basic: Simple coverage metrics, generic recommendations")
        print("   Advanced: Multi-perspective analysis")
        print("   Basic: Single-dimension scoring")
        print("   Advanced: Specific actionable recommendations")
        print("   Basic: Generic improvement suggestions")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Comparison failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Advanced Content Validity Evaluator - Phase 1 Test")
    print("Testing state-of-the-art evaluation vs basic approach")
    print()
    
    result = asyncio.run(test_advanced_vs_basic())
    
    if result:
        asyncio.run(compare_with_basic())
        print("\n✅ Phase 1 Advanced Content Validity: SUCCESS!")
        print("   Ready for Phase 1 next steps: Methodological Rigor enhancement")
    else:
        print("\n❌ Phase 1 test failed - check implementation")